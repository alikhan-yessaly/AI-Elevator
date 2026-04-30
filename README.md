# AI Elevator

Voice-controlled smart grain silo with three Raspberry Pi Pico W boards. Central Pico records voice commands, sends them through STT → LLM, and forwards the result to the Elevator or Scales Pico over BLE. Live telemetry from both peripherals is shown on an ST7789 display.

```
Central Pico  ──BLE──▶  Elevator Pico   (climate, fan, dispenser servo, distance/grain level)
              ──BLE──▶  Scales Pico     (load cell, gate servo, ToF sensor)
```

---

## What you need

- Python 3 + `pip install mpremote pyserial` on host machine
- 3× Raspberry Pi Pico W
- **Central Pico only** requires custom firmware (included as `firmware.uf2`)

---

## Setup

### 1. Flash Central Pico

Hold **BOOTSEL**, plug in Central Pico, drag `firmware.uf2` onto the USB drive that appears.  
Elevator and Scales use standard MicroPython — no custom firmware needed.

### 2. Fill in secrets

Edit `CentralPico/secrets.py`:

```python
SSID     = "wifi_name"
PASSWORD = "wifi_password"
LLM_KEY  = "..."   # LLM API key
LLM_URL  = "..."   # LLM endpoint URL
MODEL    = "..."   # model name
STT_HOST = "..."   # speech-to-text hostname
STT_PATH = "..."   # speech-to-text path
STT_KEY  = "..."   # speech-to-text API key
```

### 3. Deploy code

```bash
./deploy.sh all
```

That's it — all three boards will start running automatically after deploy.

---

## Day-to-day usage

```bash
./deploy.sh central    # redeploy Central only
./deploy.sh elevator   # redeploy Elevator only
./deploy.sh scales     # redeploy Scales only
./deploy.sh all        # redeploy all three
```

To restart all boards without redeploying:

```bash
for PORT in /dev/cu.usbmodem11201 /dev/cu.usbmodem11401 /dev/cu.usbmodem1112201; do
  python3 pico_reset.py "$PORT"
done
```

---

## Serial port / device IDs

Fixed in `deploy.sh` — update if ports change on your machine.

| Board    | Serial ID              | Port                      |
|----------|------------------------|---------------------------|
| Central  | `e6642815e3630e24`     | `/dev/cu.usbmodem1112201` |
| Elevator | `e6642815e35c6f24`     | `/dev/cu.usbmodem11201`   |
| Scales   | `e6642815e3718927`     | `/dev/cu.usbmodem11401`   |

Find IDs for replacement boards with `mpremote devs`.

---

## Rebuilding firmware (Central only)

Only needed if you modify the firmware source. Requires `arm-none-eabi-gcc`.

```bash
ln -sfn "$(pwd)/firmware" /tmp/pico_fw
cp -r firmware/micropython/ports/rp2/cmodules /tmp/cmodules

cd /tmp/pico_fw/micropython/ports/rp2
make BOARD=RPI_PICO_W USER_C_MODULES=/tmp/cmodules

# Copy result back
cp build-RPI_PICO_W/firmware.uf2 /path/to/repo/firmware.uf2
```
