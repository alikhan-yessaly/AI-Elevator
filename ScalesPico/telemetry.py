from config import SCALES_PINS, CAR_PRESENT_MM
from ht771 import Scales
from pibody import Distance

telemetry = {
    "weight":           None,   # current weight on scales in grams
    "car_present":      False,  # True when ToF reads <= CAR_PRESENT_MM
    "distance_mm":      None,   # raw ToF reading in mm
    "car_in_territory": False,  # True while a loading session is active
}

# ── Scales ────────────────────────────────────────────────────────────────────

def init_scales(scales):
    if not scales.is_ready():
        print("Scales not ready")
        while not scales.is_ready():
            pass
    print("Taring scales...")
    scales.tare()
    print("Tare complete.")
    return scales


scales = Scales(SCALES_PINS["dt"], SCALES_PINS["sck"])

from machine import Pin
indicator = Pin("LED", Pin.OUT)
indicator.on()
print("Initializing scales...")
scales = init_scales(scales)
indicator.off()
print("Scales initialized")

# ── Distance sensor ───────────────────────────────────────────────────────────

distance_sensor = Distance(SCALES_PINS["distance"])

# ── Telemetry update functions ────────────────────────────────────────────────

def get_weight():
    """Read current weight from the load cell (grams)."""
    try:
        telemetry["weight"] = scales.weight_gramm()
    except Exception as e:
        print("Weight read error:", e)
        telemetry["weight"] = None
    return telemetry["weight"]


def get_distance():
    """Read ToF sensor and update car_present flag."""
    mm = distance_sensor.read()
    if mm < 30 or mm > 300:
        return  # invalid reading, keep previous telemetry values
    telemetry["distance_mm"] = mm
    telemetry["car_present"] = mm <= CAR_PRESENT_MM
    return mm


def get_telemetry():
    """Refresh all telemetry fields. Called periodically from main loop."""
    get_weight()
    get_distance()
    print("[telemetry] weight=%.1fg  distance=%smm  car_present=%s" % (
        telemetry["weight"] if telemetry["weight"] is not None else -1,
        telemetry["distance_mm"],
        telemetry["car_present"],
    ))
    return telemetry