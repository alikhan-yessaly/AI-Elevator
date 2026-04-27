from pibody import WiFi, Buzzer, LED, Button, SoundSensor, Switch, display
from recorder import record_raw, play_raw, convert_raw_to_wav
from secrets import STT_KEY, SSID, PASSWORD, LLM_KEY, LLM_URL, MODEL, STT_HOST, STT_PATH
from ai.stt import STT
from ai.llm import LLM
from ai.system_prompts import system_prompt
from ui.ui import UI

from BLE import BLEMultiClient, _Slot, _ELEVATOR_SVC_UUID, _ELEVATOR_TX_UUID, _ELEVATOR_RX_UUID, _SCALES_SVC_UUID, _SCALES_TX_UUID, _SCALES_RX_UUID
from TelemetryData import ElevatorData, ScalesData

from machine import Pin
import time
WAV_FILE = "recording.wav"

pb_switch    = Pin(0,  Pin.IN, Pin.PULL_DOWN)
dispense_btn = Pin(20, Pin.IN, Pin.PULL_DOWN)
gate_btn     = Pin(21, Pin.IN, Pin.PULL_DOWN)
busy_led    = LED("B")
buzzer      = Buzzer("C")
btn         = Button("D")
rec_led     = LED("E")
mic         = SoundSensor("F")._analog

wifi = WiFi()
ui = UI()
llm = LLM(key=LLM_KEY, url=LLM_URL, model=MODEL, system_prompt=system_prompt)
stt = STT(host=STT_HOST, path=STT_PATH, api_key=STT_KEY)

wifi_state = "Нет"
ble_state = "Нет"
_dispense_pending = False
_dispense_last_ms = 0
_gate_pending     = False
_gate_last_ms     = 0

def _on_dispense_irq(pin):
    global _dispense_pending, _dispense_last_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _dispense_last_ms) >= 1000:
        _dispense_pending = True
        _dispense_last_ms = now

def _on_gate_irq(pin):
    global _gate_pending, _gate_last_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _gate_last_ms) >= 1000:
        _gate_pending = True
        _gate_last_ms = now

dispense_btn.irq(trigger=Pin.IRQ_RISING, handler=_on_dispense_irq)
gate_btn.irq(trigger=Pin.IRQ_RISING, handler=_on_gate_irq)

def update_ble_state(state):
    global ble_state
    ble_state = state
    
def update_elevator(data):
    try:
        ui.elevator_data = ElevatorData(temperature=data['t'], humidity=data['h'], volume=data['v'], weight=data['w'])
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
    if wifi.is_connected():
        return True
    ui.status_message(f"Переподключаюсь к {SSID}...")
    ok = wifi.ensure_connected(SSID, PASSWORD, retries=5, delay=3)
    if ok:
        global wifi_state
        wifi_state = "Есть"
        ui.status_message(f"Подключился к {SSID}")
    else:
        ui.status_message("WiFi недоступен", error=True)
    return ok

ui.status_message("Подключаюсь к BLE...")
elevator_slot = _Slot(
    "Elevator Pico",
    service_uuid=_ELEVATOR_SVC_UUID,
    tx_uuid=_ELEVATOR_TX_UUID,
    rx_uuid=_ELEVATOR_RX_UUID,
    on_payload=update_elevator,
    on_connect=lambda: update_ble_state("Есть"),
    on_disconnect=lambda: update_ble_state("Нет"),
)
scales_slot = _Slot(
    "Scales Pico",
    service_uuid=_SCALES_SVC_UUID,
    tx_uuid=_SCALES_TX_UUID,
    rx_uuid=_SCALES_RX_UUID,
    on_payload=update_scales,
)
ble_client = BLEMultiClient([elevator_slot, scales_slot])
ble_client.start()

ui.status_message(f"Подключаюсь к {SSID}...")
if wifi.ensure_connected(SSID, PASSWORD, retries=10, delay=3):
    wifi_state = "Есть"
    ui.status_message(f"Подключился к {SSID}")
else:
    ui.status_message("WiFi недоступен — работаю без сети", error=True)



try:
    while True:
        ble_client.tick()

        if _dispense_pending:
            _dispense_pending = False
            ok = ble_client.send("Elevator Pico", "dispense()")
            if ok:
                ui.status_message("Команда выдачи отправлена")
            else:
                ui.status_message("BLE не подключён", error=True)

        if _gate_pending:
            _gate_pending = False
            ok = ble_client.send("Scales Pico", "open_gate()")
            if ok:
                ui.status_message("Ворота открываются")
            else:
                ui.status_message("BLE не подключён", error=True)

        if btn.read():
            ui.state(wifi_state, ble_state)
            ui.clear_bottom()

            # Recording
            rec_led.on()
            ui.recording_LED()
            status = record_raw(mic, btn)
            if status < 0:
                ui.status_message("Maximum record time reached", True)
            ui.clear_bottom()
            rec_led.off()
            if pb_switch():
                play_raw(buzzer)

            ble_client.tick()

            # Thinking — guard every network call with a WiFi check
            busy_led.on()
            ui.status_large("Думаю...")
            try:
                convert_raw_to_wav(dest_file=WAV_FILE)
                ble_client.tick()

                if not ensure_wifi():
                    ui.status_message("Нет WiFi — пропускаю", error=True)
                    busy_led.off()
                    continue

                text = stt.transcribe_from_file(WAV_FILE)
                ble_client.tick()
                ui.clear_bottom()
                ui.heard(text)

                if not ensure_wifi():
                    ui.status_message("Нет WiFi — пропускаю", error=True)
                    busy_led.off()
                    continue

                response = llm.ask(text)
                ble_client.tick()
                ui.command(response)

                send_ok = ble_client.send("Elevator Pico", response)
                if send_ok:
                    ui.status_message("Успешно отправлено BLE")
                else:
                    ui.status_message("Не удалось отправить BLE")
            except Exception as e:
                print("Pipeline error:", e)
                ui.status_message("Ошибка: " + str(e), error=True)

            busy_led.off()
except KeyboardInterrupt:
    ble_client.stop()

