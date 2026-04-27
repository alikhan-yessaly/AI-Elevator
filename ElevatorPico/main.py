import time
import bluetooth
from helpers import periodic
from ble_transport import BLETransport
from config import BLE_NAMES, BLE_UUIDS
from actuators import light_on, light_off, dispense, auto_mode, actuator_state
from telemetry import telemetry, get_telemetry


def build_payload():
    return {
        "t": telemetry.get("temp"),
        "h": telemetry.get("hum"),
        "v": telemetry.get("dist"),
        "w": 200  # Dummy weight — replace with real sensor value, clamp 0–500
    }


def command_handler(cmd):
    commands = {
        "light_on()":  light_on,
        "light_off()": light_off,
        "dispense()":  dispense,
    }
    fn = commands.get(cmd)
    if fn is None:
        print("[CMD] Unknown command:", cmd)
        return
    fn()
    print("[CMD] Done. State:", actuator_state)


print("[MAIN] Starting...")
_uuids = BLE_UUIDS["elevator"]
ble = BLETransport(
    name=BLE_NAMES["elevator"],
    service_uuid=bluetooth.UUID(int(_uuids["service"], 16)),
    tx_uuid=bluetooth.UUID(_uuids["tx"]),
    rx_uuid=bluetooth.UUID(_uuids["rx"]),
    mode="peripheral",
    notify_interval_ms=500,
    command_handler=command_handler,
    payload_provider=build_payload,
)
print("[MAIN] BLE created")
ble.start()
print("[MAIN] BLE started")


@periodic(10)
def thread_task(timer):
    get_telemetry()
    auto_mode()


try:
    while True:
        ble.tick()
        time.sleep_ms(50)
except KeyboardInterrupt:
    thread_task.deinit()   # stop hardware timer
    ble.stop()             # stop BLE advertising / connections
