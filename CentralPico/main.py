from pibody import WiFi, Buzzer, LED, Button, SoundSensor, Switch, display
from recorder import record_raw, play_raw, convert_raw_to_wav
from secrets import STT_KEY, SSID, PASSWORD, LLM_KEY, LLM_URL, MODEL, STT_HOST, STT_PATH
from ai.stt import STT
from ai.llm import LLM
from ai.system_prompts import system_prompt
from ui.ui import UI

from BLE import BLEClient
from TelemetryData import ElevatorData

from machine import Pin
WAV_FILE = "recording.wav"

pb_switch = Pin("A1", Pin.IN, Pin.PULL_DOWN)
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

def update_ble_state(state):
    global ble_state
    ble_state = state
    
def update_elevator(data):
    print(data)
    try:
        ui.elevator_data = ElevatorData(temperature=data['t'], humidity=data['h'], volume=data['v'], weight=data['w'])
        ui.update()
    except Exception as e:
        print("Key Error")
        print(e)

ui.status_message(f"Подключаюсь к BLE...")
ble_client = BLEClient(
    "Elevator Pico", 
    on_payload=update_elevator, 
    on_connect = lambda: update_ble_state("Есть"), 
    on_disconnect=lambda: update_ble_state("Нет")
)

ble_client.start()

ui.status_message(f"Подключаюсь к {SSID}...")
try:
    wifi.connect(SSID, PASSWORD)
except Exception as e:
    ui.status_message("Не получилось подключиться", error=True)
    raise e

wifi_state = "Есть"
ui.status_message(f"Успешно подключился к {SSID}")



while True:
    ble_client.tick()
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

        # Thinking
        busy_led.on()    
        ui.status_large("Думаю...")
        convert_raw_to_wav(dest_file=WAV_FILE)
        text = stt.transcribe_from_file(WAV_FILE)
        ui.clear_bottom()
        ui.heard(text)    
        response = llm.ask(text)
        status = ble_client.send(response)
        ui.command(response)
        if status:
            ui.status_message("Успешно отправлено BLE")
        else:
            ui.status_message("Не удалось отпправить BLE")

        busy_led.off()
        # Sending

