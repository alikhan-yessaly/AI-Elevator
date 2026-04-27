import bluetooth
import struct
import time
from micropython import const

try:
    import ujson as json
except ImportError:
    import json


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_NOTIFY = const(18)

_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0004)
_FLAG_NOTIFY = const(0x0010)

_ENV_SENSE_UUID = bluetooth.UUID(0x181A)  # Environmental Sensing Service
_TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")


def _to_bytes(payload):
    if payload is None:
        return b""
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload).encode("utf-8")


def advertising_payload(name=None, services=None):
    payload = bytearray()

    def _append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    _append(0x01, b"\x06")

    if name:
        _append(0x09, name if isinstance(name, bytes) else name.encode("utf-8"))

    if services:
        for uuid in services:
            raw = bytes(uuid)
            if len(raw) == 2:
                _append(0x03, raw)
            elif len(raw) == 16:
                _append(0x07, raw)

    return payload


class BLETransport:
    """
    Reusable BLE transport.
    - peripheral mode: RX (write commands), TX (notify telemetry/state)
    - central mode scaffolding: scanning + notify callback entrypoints
    """

    def __init__(
        self,
        name="PicoBLE",
        service_uuid=_ENV_SENSE_UUID,
        tx_uuid=_TX_UUID,
        rx_uuid=_RX_UUID,
        mode="peripheral",
        rx_buffer_size=512,
        notify_interval_ms=500,
        chunk_sleep_ms=100,
        command_handler=None,
        payload_provider=None,
        on_connect=None,
        on_disconnect=None,
    ):
        self.mode = mode
        self.name = name if isinstance(name, bytes) else name.encode("utf-8")
        self.service_uuid = service_uuid
        self.tx_uuid = tx_uuid
        self.rx_uuid = rx_uuid
        self.rx_buffer_size = rx_buffer_size
        self.notify_interval_ms = notify_interval_ms
        self.chunk_sleep_ms = chunk_sleep_ms

        self.command_handler = command_handler
        self.payload_provider = payload_provider
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)

        self.conn_handle = None
        self.att_payload_max = 20
        self.last_notify_ms = 0

        self.tx_handle = None
        self.rx_handle = None
        self._services_registered = False

        self.scan_results = []

        if self.mode == "peripheral":
            self._register_peripheral_services()
        elif self.mode != "central":
            raise ValueError("Unsupported BLE mode: %s" % mode)

    def _register_peripheral_services(self):
        tx = (self.tx_uuid, _FLAG_READ | _FLAG_NOTIFY)
        rx = (self.rx_uuid, _FLAG_WRITE)
        service = (self.service_uuid, (tx, rx))
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services((service,))
        self.ble.gatts_set_buffer(self.rx_handle, self.rx_buffer_size, True)
        self._services_registered = True

    def start(self, interval_us=250000):
        if self.mode == "peripheral":
            self.advertise(interval_us=interval_us)
        else:
            print("[BLE] Central mode active")

    def advertise(self, interval_us=250000):
        if self.mode != "peripheral":
            return
        payload = advertising_payload(name=self.name, services=[self.service_uuid])
        self.ble.gap_advertise(interval_us, adv_data=payload)
        print("[BLE] Advertising as '%s'" % self.name.decode("utf-8"))

    def stop(self):
        if self.mode == "peripheral":
            self.ble.gap_advertise(None)
        self.ble.active(False)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.conn_handle = conn_handle
            print("[BLE] Central connected:", conn_handle)
            if self.on_connect:
                self.on_connect(conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if self.conn_handle == conn_handle:
                self.conn_handle = None
            print("[BLE] Central disconnected:", conn_handle)
            if self.on_disconnect:
                self.on_disconnect(conn_handle)
            if self.mode == "peripheral":
                self.advertise()

        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data
            if self.conn_handle == conn_handle:
                self.att_payload_max = max(20, mtu - 3)
            print("[BLE] MTU exchanged:", mtu, "payload:", self.att_payload_max)

        elif event == _IRQ_GATTS_WRITE and self.mode == "peripheral":
            conn_handle, value_handle = data
            if conn_handle == self.conn_handle and value_handle == self.rx_handle:
                raw = self.ble.gatts_read(self.rx_handle)
                self._handle_command(raw)

        elif event == _IRQ_SCAN_RESULT and self.mode == "central":
            self.scan_results.append(data)

        elif event == _IRQ_SCAN_DONE and self.mode == "central":
            print("[BLE] Scan done. Found:", len(self.scan_results))

        elif event == _IRQ_PERIPHERAL_CONNECT and self.mode == "central":
            conn_handle, _, _ = data
            self.conn_handle = conn_handle
            print("[BLE] Connected to peripheral:", conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT and self.mode == "central":
            conn_handle, _, _ = data
            if self.conn_handle == conn_handle:
                self.conn_handle = None
            print("[BLE] Peripheral disconnected:", conn_handle)

        elif event == _IRQ_GATTC_NOTIFY and self.mode == "central":
            conn_handle, value_handle, notify_data = data
            self._handle_notify(conn_handle, value_handle, notify_data)

    def _handle_command(self, raw):
        if not self.command_handler:
            print("[CMD] No command handler configured")
            return
        try:
            cmd = raw.decode("utf-8").strip()
        except Exception:
            cmd = ""
        if not cmd:
            print("[CMD] Empty command")
            return
        self.command_handler(cmd)

    def _handle_notify(self, conn_handle, value_handle, notify_data):
        print("[BLE] Notify from", conn_handle, "handle", value_handle, "len", len(notify_data))

    def _notify_one(self, data):
        if self.mode != "peripheral" or self.conn_handle is None:
            return False
        try:
            self.ble.gatts_notify(self.conn_handle, self.tx_handle, data)
            return True
        except Exception as exc:
            print("[TX] Notify error:", exc)
            return False

    def send(self, payload):
        data = _to_bytes(payload)
        if not data:
            return False

        total_len = len(data)
        chunk_size = self.att_payload_max

        if total_len <= chunk_size:
            return self._notify_one(data)

        if not self._notify_one(("BEGIN:%d" % total_len).encode("utf-8")):
            return False
        time.sleep_ms(self.chunk_sleep_ms)

        offset = 0
        while offset < total_len:
            chunk = data[offset: offset + chunk_size]
            if not self._notify_one(chunk):
                return False
            offset += chunk_size
            time.sleep_ms(self.chunk_sleep_ms)

        return self._notify_one(b"END")

    def tick(self):
        if self.mode != "peripheral":
            return
        if self.payload_provider is None:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_notify_ms) < self.notify_interval_ms:
            return

        self.last_notify_ms = now
        payload = self.payload_provider()
        self.send(payload)

    # Central helpers for future projects
    def scan(self, duration_ms=5000, interval_us=30000, window_us=30000):
        if self.mode != "central":
            raise RuntimeError("scan() is available only in central mode")
        self.scan_results = []
        self.ble.gap_scan(duration_ms, interval_us, window_us)

    def connect(self, addr_type, addr):
        if self.mode != "central":
            raise RuntimeError("connect() is available only in central mode")
        self.ble.gap_connect(addr_type, addr)
