"""
weighing_flow.py  –  Scales Pico
State machine that drives the full weighing cycle:

  IDLE
    │  car approaches (ToF ≤ threshold) AND car_in_territory is False
    ▼
  ARRIVING          – open gate, car_in_territory = True, wait for car to pass sensor
    │  car gone from sensor for GATE_CLOSE_DELAY_MS → gate closes
    ▼
  WEIGHING_EMPTY    – car on scales, collect stable empty weight
    │  stable → 3 beeps → save tare, open gate
    ▼
  LOADING           – car at elevator, operator loads manually
    │  weight becomes stable on scales → 3 beeps → open gate
    ▼
  EXITING           – car passing through gate
    │  car gone from sensor for GATE_CLOSE_DELAY_MS → close gate → save record
    ▼
  IDLE

While car_in_territory is True, gate stays closed for any new arriving car.
"""

import json
import time
from config import (
    GATE_CLOSE_DELAY_MS,
    WEIGHT_STABLE_READS,
    WEIGHT_STABLE_TOL_GRAMM,
    MIN_CAR_WEIGHT_GRAMM,
    RECORDS_FILE,
)
from telemetry import telemetry
from actuators import (
    open_gate, close_gate,
    signal_weigh_complete,
    signal_weight_recorded,
    signal_error,
)

# ── States ─────────────────────────────────────────────────────────────────────

STATE_IDLE            = "idle"
STATE_ARRIVING        = "arriving"
STATE_WEIGHING_EMPTY  = "weighing_empty"
STATE_LOADING         = "loading"
STATE_EXITING         = "exiting"

# ── Shared flow state (broadcast via BLE) ─────────────────────────────────────

flow_state = {
    "state":        STATE_IDLE,
    "car_id":       None,
    "tare_weight":  None,
    "gross_weight": None,
    "net_weight":   None,
}

# ── Internal bookkeeping ───────────────────────────────────────────────────────

_stable_buf      = []
_gate_close_tick = None
_next_id         = 1


def _load_next_id():
    global _next_id
    try:
        with open(RECORDS_FILE, "r") as f:
            records = json.load(f)
        if records:
            _next_id = max(r["id"] for r in records) + 1
    except Exception:
        _next_id = 1


_load_next_id()

# ── Stability helpers ──────────────────────────────────────────────────────────

def _push_weight(w):
    _stable_buf.append(w)
    if len(_stable_buf) > WEIGHT_STABLE_READS:
        _stable_buf.pop(0)


def _is_stable():
    if len(_stable_buf) < WEIGHT_STABLE_READS:
        return False
    return (max(_stable_buf) - min(_stable_buf)) <= WEIGHT_STABLE_TOL_GRAMM


def _stable_mean():
    if not _stable_buf:
        return 0.0
    return sum(_stable_buf) / len(_stable_buf)


def _clear_stable():
    _stable_buf.clear()

# ── Record persistence ─────────────────────────────────────────────────────────

def _save_record(car_id, tare_g, gross_g, net_g):
    try:
        try:
            with open(RECORDS_FILE, "r") as f:
                records = json.load(f)
        except Exception:
            records = []

        # timestamp as ISO-like string: YYYY-MM-DD HH:MM:SS (ticks_ms as fallback)
        try:
            import utime
            t = utime.localtime()
            timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (
                t[0], t[1], t[2], t[3], t[4], t[5]
            )
        except Exception:
            timestamp = str(time.ticks_ms())

        records.append({
            "id":        car_id,
            "tare_g":    round(tare_g,  1),
            "gross_g":   round(gross_g, 1),
            "net_g":     round(net_g,   1),
            "timestamp": timestamp,
        })

        with open(RECORDS_FILE, "w") as f:
            json.dump(records, f)

        print("Record saved: id=%d  tare=%.1fg  gross=%.1fg  net=%.1fg  ts=%s"
              % (car_id, tare_g, gross_g, net_g, timestamp))
        return True
    except Exception as e:
        print("Error saving record:", e)
        signal_error()
        return False

# ── Transition helper ──────────────────────────────────────────────────────────

def _set_state(s):
    flow_state["state"] = s
    _clear_stable()
    print("Flow →", s)

# ── Main tick ──────────────────────────────────────────────────────────────────

def tick():
    global _gate_close_tick, _next_id

    state           = flow_state["state"]
    car_present     = telemetry.get("car_present", False)
    car_in_territory = telemetry.get("car_in_territory", False)
    weight          = telemetry.get("weight")

    # ── IDLE ──────────────────────────────────────────────────────────────────
    if state == STATE_IDLE:
        # Only open gate if no session is currently active
        if car_present and not car_in_territory:
            flow_state["car_id"]       = _next_id
            flow_state["tare_weight"]  = None
            flow_state["gross_weight"] = None
            flow_state["net_weight"]   = None
            _next_id += 1
            telemetry["car_in_territory"] = True
            open_gate()
            _set_state(STATE_ARRIVING)
            _gate_close_tick = None

    # ── ARRIVING ──────────────────────────────────────────────────────────────
    elif state == STATE_ARRIVING:
        if not car_present:
            if _gate_close_tick is None:
                _gate_close_tick = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), _gate_close_tick) >= GATE_CLOSE_DELAY_MS:
                close_gate()
                _gate_close_tick = None
                _set_state(STATE_WEIGHING_EMPTY)
        else:
            _gate_close_tick = None

    # ── WEIGHING_EMPTY ────────────────────────────────────────────────────────
    elif state == STATE_WEIGHING_EMPTY:
        if weight is not None:
            if weight >= MIN_CAR_WEIGHT_GRAMM:
                _push_weight(weight)
                if _is_stable() and flow_state["tare_weight"] is None:
                    tare = _stable_mean()   # compute BEFORE clearing
                    flow_state["tare_weight"] = round(tare, 1)
                    print("Empty car weight accepted: %.1f g — waiting for car to leave" % tare)
                    signal_weigh_complete()
            else:
                # Weight dropped — car has left scales
                if flow_state["tare_weight"] is not None:
                    print("Car left scales, tare=%.1f g — waiting for return" % flow_state["tare_weight"])
                    flow_state["state"] = STATE_LOADING  # bypass _set_state to avoid clearing tare
                    _clear_stable()

    # ── LOADING ───────────────────────────────────────────────────────────────
    elif state == STATE_LOADING:
        if weight is not None and weight >= MIN_CAR_WEIGHT_GRAMM:
            _push_weight(weight)
            if _is_stable():
                gross = _stable_mean()      # compute BEFORE _set_state clears buffer
                net   = gross - flow_state["tare_weight"]
                flow_state["gross_weight"] = round(gross, 1)
                flow_state["net_weight"]   = round(net,   1)
                print("Loaded car weight accepted: %.1f g  net cargo: %.1f g" % (gross, net))
                signal_weigh_complete()
                open_gate()
                _gate_close_tick = None
                _set_state(STATE_EXITING)

    # ── EXITING ───────────────────────────────────────────────────────────────
    elif state == STATE_EXITING:
        if not car_present:
            if _gate_close_tick is None:
                _gate_close_tick = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), _gate_close_tick) >= GATE_CLOSE_DELAY_MS:
                close_gate()
                _save_record(
                    flow_state["car_id"],
                    flow_state["tare_weight"],
                    flow_state["gross_weight"],
                    flow_state["net_weight"],
                )
                signal_weight_recorded()
                telemetry["car_in_territory"] = False
                _gate_close_tick = None
                _set_state(STATE_IDLE)
        else:
            _gate_close_tick = None