import time
from machine import Pin
import bluetooth
from Helpers.helpers import periodic
from Helpers.ble_transport import BLETransport
from config import BLE_UUIDS, BLE_NAMES
from Picos.Elevator.actuators import (
    air_on,
    air_off,
    cooler_on,
    cooler_off,
    light_on,
    light_off,
    auto_on,
    auto_off,
    auto_mode,
    actuator_state,
    dispense,
)
from Picos.Elevator.telemetry import telemetry, get_telemetry


def _b(value):
    return 1 if value else 0


def build_payload():
    return { 
            "t": telemetry.get("temp"),
            "h": telemetry.get("hum"),
            "v": telemetry.get("dist"),
            "w": 200 # Dummy, Don't forget to round it and clamp it from 0 to 500 
    }


def command_handler(cmd):
    commands = {
        "cooler_on()":    air_on,
        "cooler_off()":   air_off,
        "heater_on()": cooler_on,
        "heater_off()": cooler_off,
        "light_on()":  light_on,
        "light_off()": light_off,
        "auto_on()":   auto_on,
        "auto_off()":  auto_off,
        "dispense()":  dispense,
    }
    fn = commands.get(cmd)
    if fn is None:
        print("[CMD] Unknown command:", cmd)
        return
    fn()
    print("[CMD] Done. State:", actuator_state)


indicator = Pin("LED", Pin.OUT)

uuids = BLE_UUIDS["elevator"]
def main():
    print("[MAIN] Starting...")
    ble = BLETransport(
        name=BLE_NAMES["elevator"],
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

    while True:
        ble.tick()
        time.sleep_ms(50)

