"""
actuators.py  –  Scales Pico
Controls the gate servo and buzzer.
All hardware objects live here; everything else imports the API functions.
"""

from pibody import Servo, Buzzer
from config import SCALES_PINS, SCALES_SERVO_POSES

# ── Hardware ──────────────────────────────────────────────────────────────────

gate  = Servo(SCALES_PINS["servo"])
buzzer = Buzzer(SCALES_PINS["buzzer"])

# ── State ─────────────────────────────────────────────────────────────────────

actuator_state = {
    "gate": "closed",   # "open" | "closed"
}

# ── Internal helpers ──────────────────────────────────────────────────────────

def _gate_open():
    gate.angle(SCALES_SERVO_POSES["open"])
    actuator_state["gate"] = "open"

def _gate_close():
    gate.angle(SCALES_SERVO_POSES["closed"])
    actuator_state["gate"] = "closed"

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

close_gate()