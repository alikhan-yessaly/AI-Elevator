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

_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
_TX_UUID        = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_RX_UUID        = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")


def _parse_adv_name(adv_data):
    i = 0
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        adv_type = adv_data[i + 1]
        if adv_type in (0x08, 0x09):
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


class BLEClient:
    def __init__(
        self,
        device_name="PicoBLE",
        service_uuid=_ENV_SENSE_UUID,
        tx_uuid=_TX_UUID,
        rx_uuid=_RX_UUID,
        on_payload=None,
        on_connect=None,
        on_disconnect=None,
        scan_duration_ms=5_000,
        retry_delay_ms=3_000,
        chunk_size=20,
    ):
        self.device_name      = device_name
        self.service_uuid     = service_uuid
        self.tx_uuid          = tx_uuid
        self.rx_uuid          = rx_uuid
        self.on_payload       = on_payload or (lambda p: print("[APP]", p))
        self.on_connect       = on_connect
        self.on_disconnect    = on_disconnect
        self.scan_duration_ms = scan_duration_ms
        self.retry_delay_ms   = retry_delay_ms

        self._state           = _ST_IDLE
        self._conn_handle     = None
        self._addr_type       = None
        self._addr            = None
        self._service_start   = None
        self._service_end     = None
        self._tx_handle       = None
        self._rx_handle       = None
        self._att_payload_max = chunk_size
        self._last_scan_ms    = 0
        self._paused          = False
        self._write_queue     = []

        self._in_buffer       = bytearray()
        self._in_expected     = None

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

    @property
    def is_connected(self):
        return self._state == _ST_READY

    def start(self):
        self._scan()

    def stop(self):
        if self._conn_handle is not None:
            try:
                self._ble.gap_disconnect(self._conn_handle)
            except Exception:
                pass
        self._ble.active(False)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def send(self, payload):
        if not self.is_connected:
            print("[TX] Not connected — dropping payload")
            return False

        data = _to_bytes(payload)
        if not data:
            return False

        total = len(data)
        cs    = self._att_payload_max

        if total <= cs:
            self._write_queue.append(data)
        else:
            self._write_queue.append(("BEGIN:%d" % total).encode())
            offset = 0
            while offset < total:
                self._write_queue.append(data[offset: offset + cs])
                offset += cs
            self._write_queue.append(b"END")

        return True

    def tick(self):
        if self._state == _ST_IDLE:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_scan_ms) >= self.retry_delay_ms:
                self._scan()
            return

        # FIX 1: write-without-response (mode=0) — no waiting for WRITE_DONE
        # This avoids status=3 WRITE_NOT_PERMITTED from write-with-response
        if self._state == _ST_READY and self._write_queue:
            chunk = self._write_queue.pop(0)
            try:
                self._ble.gattc_write(self._conn_handle, self._rx_handle, chunk, 0)
            except Exception as e:
                print(f"[TX] Write error: {e}")
                self._write_queue.clear()

    def _scan(self):
        print(f"[BLE] Scanning for '{self.device_name}'...")
        self._state        = _ST_SCANNING
        self._last_scan_ms = time.ticks_ms()
        self._ble.gap_scan(self.scan_duration_ms, 30_000, 30_000)

    def _reset(self):
        self._state         = _ST_IDLE
        self._conn_handle   = None
        self._tx_handle     = None
        self._rx_handle     = None
        self._service_start = None
        self._service_end   = None
        self._write_queue.clear()
        self._reset_inbound()

    def _reset_inbound(self):
        self._in_buffer   = bytearray()
        self._in_expected = None

    def _irq(self, event, data):

        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            name = _parse_adv_name(bytes(adv_data))
            if name == self.device_name:
                print(f"[BLE] Found '{name}' — queued for connect")
                self._state     = _ST_CONNECTING
                self._addr_type = addr_type
                self._addr      = bytes(addr)

        elif event == _IRQ_SCAN_DONE:
            if self._state == _ST_SCANNING:
                print(f"[BLE] '{self.device_name}' not found — will retry")
                self._state = _ST_IDLE
            elif self._state == _ST_CONNECTING:
                # FIX 2: gap_connect only after scan is fully done — avoids EINVAL crash
                print("[BLE] Connecting...")
                self._ble.gap_connect(self._addr_type, self._addr)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            if bytes(addr) == self._addr:
                self._conn_handle = conn_handle
                self._state       = _ST_DISCOVERING
                print("[BLE] Connected — discovering services...")
                self._ble.gattc_discover_services(conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                print("[BLE] Disconnected")
                self._reset()
                if self.on_disconnect:
                    self.on_disconnect()

        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data
            if conn_handle == self._conn_handle:
                self._att_payload_max = max(20, mtu - 3)
                print(f"[BLE] MTU {mtu} → payload max {self._att_payload_max}")

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if conn_handle == self._conn_handle and uuid == self.service_uuid:
                self._service_start = start_handle
                self._service_end   = end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            if conn_handle == self._conn_handle:
                if self._service_start is None:
                    print("[BLE] Target service not found — disconnecting")
                    self._ble.gap_disconnect(conn_handle)
                else:
                    self._ble.gattc_discover_characteristics(
                        conn_handle, self._service_start, self._service_end
                    )

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_handle:
                if uuid == self.tx_uuid:
                    # FIX 3: store TX and RX handles separately, never mix them up
                    self._tx_handle = value_handle
                    print(f"[BLE] TX handle: {value_handle}")
                elif uuid == self.rx_uuid:
                    self._rx_handle = value_handle
                    print(f"[BLE] RX handle: {value_handle}")

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            if conn_handle == self._conn_handle:
                if self._tx_handle is None or self._rx_handle is None:
                    print(f"[BLE] Missing handles TX:{self._tx_handle} RX:{self._rx_handle} — disconnecting")
                    self._ble.gap_disconnect(conn_handle)
                else:
                    self._state = _ST_SUBSCRIBING
                    print(f"[BLE] Subscribing via CCCD at handle {self._tx_handle + 1}...")
                    # FIX 4: CCCD is always _tx_handle + 1, never touch _rx_handle here
                    self._ble.gattc_write(
                        conn_handle,
                        self._tx_handle + 1,
                        struct.pack("<H", 0x0001),
                        1,
                    )

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            if conn_handle == self._conn_handle and self._state == _ST_SUBSCRIBING:
                if status == 0:
                    self._state = _ST_READY
                    print("[BLE] Ready")
                    if self.on_connect:
                        self.on_connect()
                else:
                    print(f"[BLE] Subscribe failed (status={status}) — disconnecting")
                    self._ble.gap_disconnect(conn_handle)

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._conn_handle and self._state == _ST_READY:
                self._handle_inbound(bytes(notify_data))

    def _handle_inbound(self, data):
        if data.startswith(b"BEGIN:"):
            if self._in_expected is not None:
                print(f"[RX] Interrupted transfer discarded "
                      f"({len(self._in_buffer)}/{self._in_expected})")
            try:
                self._in_expected = int(data[6:])
                self._in_buffer   = bytearray()
            except ValueError:
                print("[RX] Malformed BEGIN — resetting")
                self._reset_inbound()
            return

        if data == b"END":
            if self._in_expected is None:
                return
            if len(self._in_buffer) == self._in_expected:
                self._dispatch(bytes(self._in_buffer))
            else:
                print(f"[RX] Size mismatch: expected {self._in_expected}, "
                      f"got {len(self._in_buffer)} — discarding")
            self._reset_inbound()
            return

        if self._in_expected is not None:
            self._in_buffer.extend(data)
        else:
            stripped = data.strip()
            if stripped.startswith(b"{") or stripped.startswith(b"["):
                self._dispatch(data)

    def _dispatch(self, raw):
        if self._paused:
            return
        try:
            payload = json.loads(raw)
        except Exception:
            try:
                payload = raw.decode("utf-8")
            except Exception:
                payload = raw
        self.on_payload(payload)