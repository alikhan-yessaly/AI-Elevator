from pibody import LED, LEDTower, Servo
from config import ELEVATOR_PINS, SERVO_POSES
from Picos.Elevator.telemetry import telemetry

cooler = LEDTower(ELEVATOR_PINS["cooler"])
lights = LEDTower(ELEVATOR_PINS["lights"])
air = LED(ELEVATOR_PINS["air"])
ser = Servo(ELEVATOR_PINS["servo"])

actuator_state = {
    "air": False,
    "cooler": False,
    "lights": False,
    "dispenser": False,
}

auto_state = {
    "air": True,
    "cooler": True,
    "dispenser": False,
    "lights": False,
}

treshold = {
    "air": 60,
    "cooler": 25.0,
}

_dispense_state = {
    "active": False,
    "ticks_remaining": 0,
}

# API for actuators
def dispense():
    if _dispense_state["active"]:
        return
    ser.angle(SERVO_POSES["open"])
    actuator_state["dispenser"] = True
    _dispense_state["active"] = True
    _dispense_state["ticks_remaining"] = max(1, SERVO_POSES["delay_ms"] // 10000)

def air_on():
    air.on()
    actuator_state["air"] = True
    auto_state["air"] = True
    return actuator_state

def air_off():
    air.off()
    actuator_state["air"] = False
    auto_state["air"] = False
    return actuator_state

def cooler_on():
    cooler.fill((0, 255, 255))
    cooler.write()
    actuator_state["cooler"] = True
    actuator_state["heater"] = False
    auto_state["cooler"] = False
    auto_state["heater"] = False
    return actuator_state

def cooler_off():
    cooler.fill((0, 0, 0))
    cooler.write()
    actuator_state["cooler"] = False
    auto_state["cooler"] = False
    return actuator_state

def heater_on():
    cooler.fill((0, 255, 255))
    cooler.write()
    actuator_state["heater"] = True
    actuator_state["cooler"] = False
    auto_state["heater"] = False
    return actuator_state

def heater_off():
    cooler.fill((0, 0, 0))
    cooler.write()
    actuator_state["heater"] = False
    auto_state["heater"] = False
    return actuator_state

def light_on():
    lights.fill((255, 255, 255))
    lights.write()
    auto_state["lights"] = True
    return actuator_state

def light_off():
    cooler.fill((0, 0, 0))
    cooler.write()
    auto_state["lights"] = False
    return actuator_state

def auto_on():
    auto_state["air"] = True
    auto_state["cooler"] = True
    return auto_state

def auto_off():
    auto_state["air"] = False
    auto_state["cooler"] = False
    return auto_state

# Inner functions
def _air_on():
    air.on()
    actuator_state["air"] = True

def _air_off():
    air.off()
    actuator_state["air"] = False

def _cooler_on():
    cooler.fill((0, 255, 255))
    cooler.write()
    actuator_state["cooler"] = True

def _cooler_off():
    cooler.fill((0, 0, 0))
    cooler.write()
    actuator_state["cooler"] = False

def _servo_close():
    ser.angle(SERVO_POSES["closed"])

def auto_mode():
    if auto_state["air"]:
        if telemetry["hum"] > treshold["air"]:
            _air_on()
        elif telemetry["hum"] < treshold["air"]:
            _air_off()
    if auto_state["cooler"]:
        if telemetry["temp"] < treshold["cooler"]:
            _cooler_on()
        elif telemetry["temp"] > treshold["cooler"]:
            _cooler_off()

    # Servo: close after delay if dispensing, otherwise hold closed
    if _dispense_state["active"]:
        _dispense_state["ticks_remaining"] -= 1
        if _dispense_state["ticks_remaining"] <= 0:
            _servo_close()
            actuator_state["dispenser"] = False
            _dispense_state["active"] = False
    else:
        if actuator_state["dispenser"]:
            _servo_close()
            actuator_state["dispenser"] = False