from pibody import WiFi, Button
from recorder import init_i2s, reinit_i2s, record_to_wav, MAX_REC_BYTES
from sdcard import SDCard
from secrets import STT_KEY, SSID, PASSWORD, LLM_KEY, LLM_URL, MODEL, STT_HOST, STT_PATH
from ai.stt import STT
from ai.llm import LLM
from ai.system_prompts import system_prompt
from ui.ui import UI
from BLE import (BLEMultiClient, _Slot,
                 _ELEVATOR_SVC_UUID, _ELEVATOR_TX_UUID, _ELEVATOR_RX_UUID,
                 _SCALES_SVC_UUID,   _SCALES_TX_UUID,   _SCALES_RX_UUID)
from TelemetryData import ElevatorData, ScalesData

import os
import gc
import time

WAV_FILE = "/sd/recording.wav"

button = Button("E")

# ── UI initialised first so every subsequent failure can show on screen ───────
ui = UI()

# ── SD card ───────────────────────────────────────────────────────────────────
_sd_ok = False
try:
    sd = SDCard()
    os.mount(sd, "/sd")
    _sd_ok = True
    print("[SD] Mounted OK")
except Exception as e:
    ui.status_message("SD: " + str(e), error=True)

# ── I2S microphone ────────────────────────────────────────────────────────────
audio_in = None
try:
    gc.collect()
    audio_in = init_i2s()
    print("[I2S] Ready")
except Exception as e:
    ui.status_message("Mic: " + str(e), error=True)

# ── WiFi / AI clients ─────────────────────────────────────────────────────────
wifi = WiFi()
llm  = LLM(key=LLM_KEY, url=LLM_URL, model=MODEL, system_prompt=system_prompt)
stt  = STT(host=STT_HOST, path=STT_PATH, api_key=STT_KEY)

# ── State ─────────────────────────────────────────────────────────────────────
_wifi_ok      = False
_elevator_ble = False
_scales_ble   = False
_ui_dirty     = False   # set True by BLE IRQ callbacks; cleared in main loop


def _redraw_status():
    ui.state(_wifi_ok, _elevator_ble, _scales_ble)


def _set_elevator_ble(connected):
    # Called from BLE IRQ context — only set flags, never touch display here.
    global _elevator_ble, _ui_dirty
    _elevator_ble = connected
    _ui_dirty     = True


def _set_scales_ble(connected):
    global _scales_ble, _ui_dirty
    _scales_ble = connected
    _ui_dirty   = True


def update_elevator(data):
    try:
        ui.elevator_data = ElevatorData(
            temperature=data['t'], humidity=data['h'],
            volume=data['v'],      weight=data['w'],
            cooling=data.get('cool', False),
            heating=data.get('heat', False))
        ui.update()
    except Exception as e:
        print("Elevator data error:", e)


def update_scales(data):
    try:
        ui.scales_data = ScalesData(weight=data['w'], car_presence=data.get('car', False))
        ui.update()
    except Exception as e:
        print("Scales data error:", e)


def ensure_wifi():
    global _wifi_ok
    if wifi.is_connected():
        if not _wifi_ok:
            _wifi_ok = True
            _redraw_status()
        return True
    _wifi_ok = False
    _redraw_status()
    ui.status_message("Переподключаюсь к WiFi...")
    ok = wifi.ensure_connected(SSID, PASSWORD, retries=5, delay=3)
    _wifi_ok = ok
    ui.status_message("WiFi подключён" if ok else "WiFi недоступен", error=not ok)
    _redraw_status()
    return ok


# ── BLE ───────────────────────────────────────────────────────────────────────
ui.status_message("Инициализация BLE...")
elevator_slot = _Slot(
    "Elevator Pico",
    service_uuid=_ELEVATOR_SVC_UUID,
    tx_uuid=_ELEVATOR_TX_UUID,
    rx_uuid=_ELEVATOR_RX_UUID,
    on_payload=update_elevator,
    on_connect=lambda: _set_elevator_ble(True),
    on_disconnect=lambda: _set_elevator_ble(False),
)
scales_slot = _Slot(
    "Scales Pico",
    service_uuid=_SCALES_SVC_UUID,
    tx_uuid=_SCALES_TX_UUID,
    rx_uuid=_SCALES_RX_UUID,
    on_payload=update_scales,
    on_connect=lambda: _set_scales_ble(True),
    on_disconnect=lambda: _set_scales_ble(False),
)
ble_client = BLEMultiClient([elevator_slot, scales_slot])
ble_client.start()

# ── Initial WiFi (3 retries — don't block BLE scan for 30 s) ─────────────────
ui.status_message("Подключаюсь к WiFi...")
if wifi.ensure_connected(SSID, PASSWORD, retries=3, delay=2):
    _wifi_ok = True
    ui.status_message("WiFi подключён")
else:
    ui.status_message("WiFi недоступен — работаю без сети", error=True)

_redraw_status()

# ── Main loop ─────────────────────────────────────────────────────────────────
_last_status_ms = 0

try:
    while True:
        now = time.ticks_ms()
        ble_client.tick()

        # Flush pending BLE state change to display (IRQ-safe: only set flag in IRQ)
        if _ui_dirty:
            _ui_dirty = False
            _redraw_status()

        # Refresh status bar every 2 s and detect silent WiFi drops
        if time.ticks_diff(now, _last_status_ms) >= 2000:
            _last_status_ms = now
            live = wifi.is_connected()
            if live != _wifi_ok:
                _wifi_ok = live
            _redraw_status()

        # ── Hardware not ready — attempt recovery then yield ──────────────────
        if not _sd_ok:
            try:
                sd = SDCard()
                os.mount(sd, "/sd")
                _sd_ok = True
                ui.status_message("SD подключена")
                _redraw_status()
            except Exception:
                time.sleep_ms(5)
                continue

        if audio_in is None:
            audio_in = reinit_i2s(None)
            if audio_in is None:
                ui.status_message("Нет микрофона", error=True)
                time.sleep_ms(5)
                continue
            ui.status_message("Микрофон готов")

        # ── Button pressed → recording pipeline ───────────────────────────────
        if button.read():
            ui.clear_bottom()
            _redraw_status()
            ui.recording_LED()

            try:
                n_bytes = record_to_wav(audio_in, button.read, WAV_FILE)
            except Exception as e:
                print("[REC] Error:", e)
                ui.status_message("Ошибка записи: " + str(e), error=True)
                audio_in = reinit_i2s(audio_in)
                time.sleep_ms(200)
                continue

            ui.clear_bottom()

            if n_bytes == 0:
                audio_in = reinit_i2s(audio_in)
                ui.status_message("Запись пуста", error=True)
                continue

            if n_bytes >= MAX_REC_BYTES:
                ui.status_message("Достигнут лимит записи")

            ble_client.tick()

            # ── STT → LLM → BLE ───────────────────────────────────────────────
            ui.status_large("Думаю...")
            try:
                if not ensure_wifi():
                    ui.status_message("Нет WiFi — пропускаю", error=True)
                    continue

                text = stt.transcribe_from_file(WAV_FILE)
                ble_client.tick()
                ui.clear_bottom()
                ui.heard(text)

                if not ensure_wifi():
                    ui.status_message("Нет WiFi — пропускаю", error=True)
                    continue

                response = llm.ask(text)
                ble_client.tick()
                ui.command(response)

                send_ok = ble_client.send("Elevator Pico", response)
                ui.status_message(
                    "Успешно отправлено BLE" if send_ok else "Не удалось отправить BLE",
                    error=not send_ok)

            except Exception as e:
                print("[Pipeline] Error:", e)
                ui.status_message("Ошибка: " + str(e), error=True)

        time.sleep_ms(5)

except KeyboardInterrupt:
    ble_client.stop()
