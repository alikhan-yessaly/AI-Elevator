from pibody import WiFi, Buzzer, LED, Button, SoundSensor, Switch, display
from recorder import record_raw, play_raw, convert_raw_to_wav
from secrets import STT_KEY, SSID, PASSWORD, LLM_KEY, LLM_URL, MODEL, STT_HOST, STT_PATH
from ai.stt import STT
from ai.llm import LLM
from ai.system_prompts import system_prompt
import os

WAV_FILE = "recording.wav"

mode_switch = Switch("A")
busy_led    = LED("B")
buzzer      = Buzzer("C")
btn         = Button("D")
rec_led     = LED("E")
mic         = SoundSensor("F")._analog

wifi = WiFi()
display.print(f"Connecting to {SSID}")

try:
    wifi.connect(SSID, PASSWORD)
except Exception as e:
    display.print("WiFi Connection Failed")
    raise e

llm = LLM(key=LLM_KEY, url=LLM_URL, model=MODEL, system_prompt=system_prompt)
stt = STT(host=STT_HOST, path=STT_PATH, api_key=STT_KEY)

try:
    os.remove("WAV_FILE")
except:
    pass

display.print("Press the button to start recording")

def record():
    rec_led.on()
    status = record_raw(mic, btn)
    rec_led.off()
    if status < 0:
        display.print("Maximum record time reached")

def audio_to_command(verbose=False):
    busy_led.on()    
    convert_raw_to_wav(dest_file=WAV_FILE)
    text = stt.transcribe_from_file(WAV_FILE)
    if verbose:
        print(text)
        display.print(text)

    response = llm.ask(text)
    busy_led.off()
    return response


while True:
    while not btn.read():
        pass
    
    record()
    
    command = audio_to_command(True)
    print(command)
    display.print("LLM:", command)

    

