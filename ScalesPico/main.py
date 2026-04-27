import time
import bluetooth
from ble_transport import BLETransport
from telemetry import get_telemetry, telemetry
from weighing_flow import tick, flow_state
from config import BLE_NAMES, BLE_UUIDS
from actuators import open_gate, close_gate, actuator_state


def build_payload():
    return {
        "w":     round(telemetry.get("weight") or 0),
        "car":   telemetry.get("car_present"),
        "dist":  telemetry.get("distance_mm"),
        "grain": telemetry.get("last_grain_weight"),
        "net":   flow_state.get("net_weight"),
    }


def command_handler(cmd):
    commands = {
        "open_gate()":  open_gate,
        "close_gate()": close_gate,
    }
    fn = commands.get(cmd)
    if fn is None:
        print("[CMD] Unknown command:", cmd)
        return
    fn()
    print("[CMD] Done. State:", actuator_state)


_uuids = BLE_UUIDS["scales"]
ble = BLETransport(
    name=BLE_NAMES["scales"],
    service_uuid=bluetooth.UUID(int(_uuids["service"], 16)),
    tx_uuid=bluetooth.UUID(_uuids["tx"]),
    rx_uuid=bluetooth.UUID(_uuids["rx"]),
    mode="peripheral",
    notify_interval_ms=500,
    command_handler=command_handler,
    payload_provider=build_payload,
)
ble.start()

try:
    while True:
        get_telemetry()
        tick()
        ble.tick()
        print("[main] state=%s  weight=%s  car=%s  dist=%s" % (
            flow_state.get("state"),
            telemetry.get("weight"),
            telemetry.get("car_present"),
            telemetry.get("distance_mm"),
        ))
        time.sleep_ms(50)
except KeyboardInterrupt:
    ble.stop()
