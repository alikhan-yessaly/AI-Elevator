import time
import bluetooth
from ble_transport import BLETransport
from config import BLE_NAMES, BLE_UUIDS
from actuators import heater_on, heater_off, cooler_on, cooler_off, light_on, light_off, dispense, auto_mode, actuator_state
from telemetry import telemetry, get_telemetry


def build_payload():
    return {
        "t":    telemetry.get("temp"),
        "h":    telemetry.get("hum"),
        "v":    telemetry.get("dist"),
        "w":    200,  # Dummy weight
        "cool": actuator_state["cooler"],
        "heat": actuator_state["heater"],
    }


def command_handler(cmd):
    commands = {
        "heater_on()":  heater_on,
        "heater_off()": heater_off,
        "cooler_on()":  cooler_on,
        "cooler_off()": cooler_off,
        "light_on()":   light_on,
        "light_off()":  light_off,
        "dispense()":   dispense,
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


_TELEMETRY_MS = 100   # 10 Hz
_last_telemetry = 0

try:
    while True:
        ble.tick()

        now = time.ticks_ms()
        if time.ticks_diff(now, _last_telemetry) >= _TELEMETRY_MS:
            _last_telemetry = now
            get_telemetry()
            auto_mode()

        time.sleep_ms(50)
except KeyboardInterrupt:
    ble.stop()
