import time
from pibody import LEDTower, Servo
from config import ELEVATOR_PINS, SERVO_POSES, AIR_PIN
from telemetry import telemetry

fan         = Servo(AIR_PIN)                           # pin 8, servo-controlled fan
climate_led = LEDTower(ELEVATOR_PINS["climate_led"])  # slot H: heating/cooling indicator
lights      = LEDTower(ELEVATOR_PINS["lights"])        # slot G: cabin lighting
ser         = Servo(ELEVATOR_PINS["servo"])            # pin 9: dispenser
ser.off()                                              # deinit immediately — only powered during dispense()

actuator_state = {
    "fan":       False,
    "heater":    False,
    "cooler":    False,
    "lights":    False,
    "dispenser": False,
}

TEMP_HEAT = 20.0  # °C — below this → heater on
TEMP_COOL = 28.0  # °C — above this → cooler on

# True while LLM has manually set heater or cooler; auto_mode backs off
_climate_manual = False

# ── internal helpers ────────────────────────────────────────────────────────

def _sync_fan():
    on = actuator_state["heater"] or actuator_state["cooler"]
    if on:
        fan.on()         # reinit PWM
        fan.angle(180)   # spin — stay powered, do NOT deinit
    else:
        fan.angle(90)    # send neutral/stop signal
        time.sleep_ms(300)
        fan.off()        # deinit — no PWM while idle, no heat
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

def heater_on():
    global _climate_manual
    _climate_manual = True
    actuator_state["heater"] = True
    actuator_state["cooler"] = False
    _sync_climate_led()
    _sync_fan()

def heater_off():
    global _climate_manual
    _climate_manual = False
    actuator_state["heater"] = False
    _sync_climate_led()
    _sync_fan()

def cooler_on():
    global _climate_manual
    _climate_manual = True
    actuator_state["cooler"] = True
    actuator_state["heater"] = False
    _sync_climate_led()
    _sync_fan()

def cooler_off():
    global _climate_manual
    _climate_manual = False
    actuator_state["cooler"] = False
    _sync_climate_led()
    _sync_fan()

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
    ser.on()
    ser.angle(SERVO_POSES["open"])
    actuator_state["dispenser"] = True
    time.sleep_ms(SERVO_POSES["delay_ms"])
    ser.angle(SERVO_POSES["closed"])
    time.sleep_ms(SERVO_POSES["deinit_ms"])
    ser.off()
    actuator_state["dispenser"] = False

# ── auto mode (runs every tick) ─────────────────────────────────────────────

def auto_mode():
    if _climate_manual:
        return
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
