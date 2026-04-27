import time
from pibody import LED, LEDTower, Servo
from config import ELEVATOR_PINS, SERVO_POSES
from telemetry import telemetry

fan         = LED(ELEVATOR_PINS["air"])               # slot F
climate_led = LEDTower(ELEVATOR_PINS["climate_led"])  # slot H: heating/cooling indicator
lights      = LEDTower(ELEVATOR_PINS["lights"])        # slot G: cabin lighting
ser         = Servo(ELEVATOR_PINS["servo"])            # pin 9: dispenser

actuator_state = {
    "fan":       False,
    "heater":    False,
    "cooler":    False,
    "lights":    False,
    "dispenser": False,
}

TEMP_HEAT = 20.0  # °C — below this → heater on
TEMP_COOL = 28.0  # °C — above this → cooler on

# ── internal helpers ────────────────────────────────────────────────────────

def _sync_fan():
    on = actuator_state["heater"] or actuator_state["cooler"]
    fan.on() if on else fan.off()
    actuator_state["fan"] = on

def _sync_climate_led():
    if actuator_state["heater"]:
        climate_led.fill((255, 80, 0))   # orange = heat
    elif actuator_state["cooler"]:
        climate_led.fill((0, 200, 255))  # cyan = cool
    else:
        climate_led.fill((0, 0, 0))
    climate_led.write()

# ── public command API (from central LLM) ───────────────────────────────────

def light_on():
    lights.fill((255, 255, 255))
    lights.write()
    actuator_state["lights"] = True
    return actuator_state

def light_off():
    lights.fill((0, 0, 0))
    lights.write()
    actuator_state["lights"] = False
    return actuator_state

def dispense():
    ser.angle(SERVO_POSES["open"])
    actuator_state["dispenser"] = True
    time.sleep_ms(SERVO_POSES["delay_ms"])
    ser.angle(SERVO_POSES["closed"])
    actuator_state["dispenser"] = False

# ── auto mode (runs every tick) ─────────────────────────────────────────────

def auto_mode():
    temp = telemetry.get("temp")
    if temp is None:
        return
    if temp < TEMP_HEAT:
        actuator_state["heater"] = True
        actuator_state["cooler"] = False
    elif temp > TEMP_COOL:
        actuator_state["cooler"] = True
        actuator_state["heater"] = False
    else:
        actuator_state["heater"] = False
        actuator_state["cooler"] = False
    _sync_climate_led()
    _sync_fan()
