from pibody import Climate, Distance
from config import ELEVATOR_PINS

telemetry = {
    "temp": None,
    "hum": None,
    "dist": None,
}

try:
    climate = Climate(ELEVATOR_PINS["climate"])
except:
    climate = None
    telemetry["temp"] = 24.5
    telemetry["hum"] = 40.0

try:
    distance = Distance(ELEVATOR_PINS["distance"])
except:
    distance = None
    telemetry["dist"] = 70

def _dist_to_pct(mm):
    if mm is None:
        return None
    pct = (275 - mm) / (275 - 50) * 100
    return max(0, min(100, int(pct)))

def get_telemetry():
    if climate is not None:
        telemetry["temp"] = round(climate.read_temperature(), 1)
        telemetry["hum"] = round(climate.read_humidity(), 1)
    if distance is not None:
        raw = round(distance.read(), 1)
        telemetry["dist"] = _dist_to_pct(raw)
    return telemetry