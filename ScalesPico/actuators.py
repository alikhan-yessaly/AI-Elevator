"""
actuators.py  –  Scales Pico
Controls the gate servo and buzzer.
All hardware objects live here; everything else imports the API functions.
"""

import time
from pibody import Servo, Buzzer, LEDTower
from config import SCALES_PINS, SCALES_SERVO_POSES

# ── Hardware ──────────────────────────────────────────────────────────────────

gate     = Servo(SCALES_PINS["servo"])
buzzer   = Buzzer(SCALES_PINS["buzzer"])
gate_led = LEDTower(SCALES_PINS["gate_led"])

# ── State ─────────────────────────────────────────────────────────────────────

actuator_state = {
    "gate": "closed",   # "open" | "closed"
}

# ── Internal helpers ──────────────────────────────────────────────────────────

def _gate_open():
    gate.on()
    gate.angle(SCALES_SERVO_POSES["open"])
    actuator_state["gate"] = "open"
    gate_led.fill((0, 255, 0))
    gate_led.write()
    time.sleep_ms(SCALES_SERVO_POSES["deinit_ms"])
    gate.off()

def _gate_close():
    gate.on()
    gate.angle(SCALES_SERVO_POSES["closed"])
    actuator_state["gate"] = "closed"
    gate_led.fill((255, 0, 0))
    gate_led.write()
    time.sleep_ms(SCALES_SERVO_POSES["deinit_ms"])
    gate.off()

# ── Public API ────────────────────────────────────────────────────────────────

def close_gate():
    """Close the gate and signal with a double boop."""
    if actuator_state["gate"] == "closed":
        return
    _gate_close()
    buzzer.boop()
    buzzer.boop()

def open_gate():
    """Open the gate and signal with a single beep."""
    if actuator_state["gate"] == "open":
        return
    _gate_open()
    buzzer.beep()

def signal_weigh_complete():
    """3 beeps when a stable weight is accepted."""
    buzzer.beep()
    buzzer.beep()
    buzzer.beep()

def signal_weight_recorded():
    """Double-beep to confirm a weight record has been saved."""
    buzzer.beep()
    buzzer.beep()

def signal_error():
    """Long boop to indicate something went wrong."""
    buzzer.boop()

def get_state():
    return dict(actuator_state)

_gate_close()  # physically close on boot