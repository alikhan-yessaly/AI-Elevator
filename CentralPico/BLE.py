import bluetooth
import struct
import time
from micropython import const

try:
    import ujson as json
except ImportError:
    import json

_IRQ_SCAN_RESULT                 = const(5)
_IRQ_SCAN_DONE                   = const(6)
_IRQ_PERIPHERAL_CONNECT          = const(7)
_IRQ_PERIPHERAL_DISCONNECT       = const(8)
_IRQ_GATTC_SERVICE_RESULT        = const(9)
_IRQ_GATTC_SERVICE_DONE          = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE   = const(12)
_IRQ_GATTC_WRITE_DONE            = const(17)
_IRQ_GATTC_NOTIFY                = const(18)
_IRQ_MTU_EXCHANGED               = const(21)

_ST_IDLE        = const(0)
_ST_SCANNING    = const(1)
_ST_CONNECTING  = const(2)
_ST_DISCOVERING = const(3)
_ST_SUBSCRIBING = const(4)
_ST_READY       = const(5)

_ELEVATOR_SVC_UUID = bluetooth.UUID(0x181B)
_ELEVATOR_TX_UUID  = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_ELEVATOR_RX_UUID  = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_SCALES_SVC_UUID   = bluetooth.UUID(0x181A)
_SCALES_TX_UUID    = bluetooth.UUID("6E400013-B5A3-F393-E0A9-E50E24DCCA9E")
_SCALES_RX_UUID    = bluetooth.UUID("6E400012-B5A3-F393-E0A9-E50E24DCCA9E")


def _parse_adv_name(adv_data):
    i = 0
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        if adv_data[i + 1] in (0x08, 0x09):
            return bytes(adv_data[i + 2: i + 1 + length]).decode("utf-8", "ignore")
        i += 1 + length
    return None


def _to_bytes(payload):
    if payload is None:
        return b""
    if isinstance(payload, (bytes, bytearray)):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload).encode("utf-8")


class _Slot:
    def __init__(self, device_name, service_uuid, tx_uuid, rx_uuid,
                 on_payload=None, on_connect=None, on_disconnect=None):
        self.device_name   = device_name
        self.service_uuid  = service_uuid
        self.tx_uuid       = tx_uuid
        self.rx_uuid       = rx_uuid
        self.on_payload    = on_payload or (lambda p: None)
        self.on_connect    = on_connect
        self.on_disconnect = on_disconnect
        # runtime state
        self.state         = _ST_IDLE
        self.conn_handle   = None
        self.addr_type     = None
        self.addr          = None
        self.service_start = None
        self.service_end   = None
        self.tx_handle     = None
        self.rx_handle     = None
        self.att_payload_max = 20
        self.write_queue   = []
        self.in_buffer     = bytearray()
        self.in_expected   = None


class BLEMultiClient:
    def __init__(self, slots, scan_duration_ms=5_000, retry_delay_ms=3_000):
        self._slots          = slots
        self._scan_duration  = scan_duration_ms
        self._retry_delay    = retry_delay_ms
        self._scanning       = False
        self._last_scan_ms   = 0
        self._addr_to_slot   = {}
        self._handle_to_slot = {}
        self._connect_queue  = []

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

    def start(self):
        self._scan()

    def stop(self):
        if self._scanning:
            self._ble.gap_scan(None)
        for slot in self._slots:
            if slot.conn_handle is not None:
                try:
                    self._ble.gap_disconnect(slot.conn_handle)
                except Exception:
                    pass
        self._ble.active(False)

    def is_connected(self, device_name):
        for slot in self._slots:
            if slot.device_name == device_name:
                return slot.state == _ST_READY
        return False

    def send(self, device_name, payload):
        for slot in self._slots:
            if slot.device_name == device_name:
                if slot.state != _ST_READY:
                    print("[TX] %s not ready — dropping" % device_name)
                    return False
                data = _to_bytes(payload)
                if not data:
                    return False
                total = len(data)
                cs    = slot.att_payload_max
                if total <= cs:
                    slot.write_queue.append(data)
                else:
                    slot.write_queue.append(("BEGIN:%d" % total).encode())
                    offset = 0
                    while offset < total:
                        slot.write_queue.append(data[offset:offset + cs])
                        offset += cs
                    slot.write_queue.append(b"END")
                return True
        print("[TX] Unknown device: %s" % device_name)
        return False

    def tick(self):
        if not self._scanning:
            if any(s.state == _ST_IDLE for s in self._slots):
                now = time.ticks_ms()
                if time.ticks_diff(now, self._last_scan_ms) >= self._retry_delay:
                    self._scan()

        for slot in self._slots:
            if slot.state == _ST_READY and slot.write_queue:
                chunk = slot.write_queue.pop(0)
                try:
                    self._ble.gattc_write(slot.conn_handle, slot.rx_handle, chunk, 0)
                except Exception as e:
                    print("[TX] Write error on %s: %s" % (slot.device_name, e))
                    slot.write_queue.clear()

    def _scan(self):
        print("[BLE] Scanning...")
        self._scanning     = True
        self._last_scan_ms = time.ticks_ms()
        self._ble.gap_scan(self._scan_duration, 30_000, 30_000)

    def _connect_next(self):
        if self._connect_queue:
            slot = self._connect_queue.pop(0)
            print("[BLE] Connecting to %s..." % slot.device_name)
            self._ble.gap_connect(slot.addr_type, slot.addr)

    def _reset_slot(self, slot):
        slot.state         = _ST_IDLE
        slot.conn_handle   = None
        slot.addr_type     = None
        slot.addr          = None
        slot.service_start = None
        slot.service_end   = None
        slot.tx_handle     = None
        slot.rx_handle     = None
        slot.write_queue.clear()
        slot.in_buffer     = bytearray()
        slot.in_expected   = None

    def _irq(self, event, data):

        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            name = _parse_adv_name(bytes(adv_data))
            for slot in self._slots:
                if slot.state == _ST_IDLE and slot.device_name == name:
                    slot.addr_type = addr_type
                    slot.addr      = bytes(addr)
                    slot.state     = _ST_CONNECTING
                    self._addr_to_slot[slot.addr] = slot
                    print("[BLE] Found '%s'" % name)

        elif event == _IRQ_SCAN_DONE:
            self._scanning = False
            for slot in self._slots:
                if slot.state == _ST_CONNECTING:
                    self._connect_queue.append(slot)
            not_found = [s.device_name for s in self._slots if s.state == _ST_IDLE]
            if not_found:
                print("[BLE] Not found: %s" % not_found)
            self._connect_next()

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            slot = self._addr_to_slot.get(bytes(addr))
            if slot:
                slot.conn_handle = conn_handle
                slot.state       = _ST_DISCOVERING
                self._handle_to_slot[conn_handle] = slot
                print("[BLE] Connected to %s (handle=%d)" % (slot.device_name, conn_handle))
                self._ble.gattc_discover_services(conn_handle)
            self._connect_next()

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            slot = self._handle_to_slot.pop(conn_handle, None)
            if slot:
                print("[BLE] Disconnected: %s" % slot.device_name)
                self._addr_to_slot.pop(slot.addr, None)
                if slot.on_disconnect:
                    slot.on_disconnect()
                self._reset_slot(slot)

        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot:
                slot.att_payload_max = max(20, mtu - 3)

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot and uuid == slot.service_uuid:
                slot.service_start = start_handle
                slot.service_end   = end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot:
                if slot.service_start is None:
                    print("[BLE] Service not found for %s — disconnecting" % slot.device_name)
                    self._ble.gap_disconnect(conn_handle)
                else:
                    self._ble.gattc_discover_characteristics(
                        conn_handle, slot.service_start, slot.service_end
                    )

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot:
                if uuid == slot.tx_uuid:
                    slot.tx_handle = value_handle
                elif uuid == slot.rx_uuid:
                    slot.rx_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot:
                if slot.tx_handle is None or slot.rx_handle is None:
                    print("[BLE] Missing handles for %s — disconnecting" % slot.device_name)
                    self._ble.gap_disconnect(conn_handle)
                else:
                    slot.state = _ST_SUBSCRIBING
                    self._ble.gattc_write(
                        conn_handle,
                        slot.tx_handle + 1,
                        struct.pack("<H", 0x0001),
                        1,
                    )

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot and slot.state == _ST_SUBSCRIBING:
                if status == 0:
                    slot.state = _ST_READY
                    print("[BLE] Ready: %s" % slot.device_name)
                    if slot.on_connect:
                        slot.on_connect()
                else:
                    print("[BLE] Subscribe failed for %s (status=%d)" % (slot.device_name, status))
                    self._ble.gap_disconnect(conn_handle)

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            slot = self._handle_to_slot.get(conn_handle)
            if slot and slot.state == _ST_READY:
                self._handle_inbound(slot, bytes(notify_data))

    def _handle_inbound(self, slot, data):
        if data.startswith(b"BEGIN:"):
            try:
                slot.in_expected = int(data[6:])
                slot.in_buffer   = bytearray()
            except ValueError:
                slot.in_buffer   = bytearray()
                slot.in_expected = None
            return

        if data == b"END":
            if slot.in_expected is None:
                return
            if len(slot.in_buffer) == slot.in_expected:
                self._dispatch(slot, bytes(slot.in_buffer))
            else:
                print("[RX] Size mismatch on %s: expected %d got %d" % (
                    slot.device_name, slot.in_expected, len(slot.in_buffer)))
            slot.in_buffer   = bytearray()
            slot.in_expected = None
            return

        if slot.in_expected is not None:
            slot.in_buffer.extend(data)
        else:
            stripped = data.strip()
            if stripped.startswith(b"{") or stripped.startswith(b"["):
                self._dispatch(slot, data)

    def _dispatch(self, slot, raw):
        try:
            payload = json.loads(raw)
        except Exception:
            try:
                payload = raw.decode("utf-8")
            except Exception:
                payload = raw
        slot.on_payload(payload)
