from BLE import BLEClient
import bluetooth, time
from pibody import Button
client = BLEClient("Elevator Pico", on_payload=lambda p: print("[Scales]", p), on_connect=lambda: send)
btn = Button("D")
client.start()

def send():
    client.send("Hello Alikhan!")

print("Hi")
while True:
    client.tick()  # reconnects dropped receivers automatically

    if btn.read():
        client.send("Hello Alikhan!")
        time.sleep(1)
    time.sleep_ms(10)