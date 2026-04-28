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
gate.off()                                  # deinit immediately — only powered during gate moves
buzzer   = Buzzer(SCALES_PINS["buzzer"])
gate_led = LEDTower(SCALES_PINS["gate_led"])

# ── State ─────────────────────────────────────────────────────────────────────

actuator_state = {
    "gate": "closed",   # "open" | "closed"
}

manual_gate_active = False   # True while GP21/BLE manual override holds the gate

# ── Internal helpers ──────────────────────────────────────────────────────────

def _gate_open():
    gate.on()
    gate.angle(SCALES_SERVO_POSES["open"])
    actuator_state["gate"] = "open"
    gate_led.fill((0, 255, 0))
    gate_led.write()
    buzzer.beep()                                    # sound with movement
    time.sleep_ms(SCALES_SERVO_POSES["deinit_ms"])
    gate.off()

def _gate_close():
    gate.on()
    gate.angle(SCALES_SERVO_POSES["closed"])
    actuator_state["gate"] = "closed"
    gate_led.fill((255, 0, 0))
    gate_led.write()
    buzzer.boop()                                    # sound with movement
    buzzer.boop()
    time.sleep_ms(SCALES_SERVO_POSES["deinit_ms"])
    gate.off()

# ── Public API ────────────────────────────────────────────────────────────────

def close_gate():
    if actuator_state["gate"] == "closed":
        return
    _gate_close()

def open_gate():
    if actuator_state["gate"] == "open":
        return
    _gate_open()

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

def manual_open_gate(duration_ms=5000):
    """Open gate for a fixed duration without triggering the weighing flow."""
    global manual_gate_active
    manual_gate_active = True
    _gate_open()                 # beep + move + deinit
    time.sleep_ms(duration_ms)
    _gate_close()                # boop boop + move + deinit
    manual_gate_active = False

def get_state():
    return dict(actuator_state)

_gate_close()  # physically close on boot