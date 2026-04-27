import time
from Helpers.ble_transport import BLETransport
from Picos.Scales.telemetry import get_telemetry, telemetry
from Picos.Scales.weighing_flow import tick, flow_state
from config import BLE_NAMES


def build_payload():
    return {
            "w":        telemetry.get("weight"),
            "car":      telemetry.get("car_present"),
            "dist":     telemetry.get("distance_mm"),
            "grain":    telemetry.get("last_grain_weight"),
            "net":      flow_state.get("net_weight"),
#         "flow": {
#             "state":    flow_state.get("state"),
#             "id":       flow_state.get("car_id"),
#             "tare":     flow_state.get("tare_weight"),
#             "gross":    flow_state.get("gross_weight"),
#             "net":      flow_state.get("net_weight"),
#         },
    }


def main():
    ble = BLETransport(
        name=BLE_NAMES["scales"],
        mode="peripheral",
        notify_interval_ms=500,
        payload_provider=build_payload,
    )
    ble.start()

    while True:
        get_telemetry()         # refresh every loop iteration
        tick()                  # advance the weighing state machine
        ble.tick()
        print("[main] state=%s  weight=%s  car=%s  dist=%s" % (
            flow_state.get("state"),
            telemetry.get("weight"),
            telemetry.get("car_present"),
            telemetry.get("distance_mm"),
        ))
        time.sleep_ms(50)