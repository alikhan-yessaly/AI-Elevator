""" 
Config file for the whole project
"""

from micropython import const


## ================================================
## Pico Central
## ================================================

### ====== BLE configuration ======
BLE_SCALES = "Scales Pico"
BLE_ELEVATOR = "Elevator Pico"

BLE_NAMES = {
    "scales": BLE_SCALES,
    "elevator": BLE_ELEVATOR,
}

BLE_UUIDS = {
    "elevator": {
        "service": "181B",
        "tx": "6E400003-B5A3-F393-E0A9-E50E24DCCA9E",
        "rx": "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",
    },
    "scales": {
        "service": "181A",
        "tx": "6E400013-B5A3-F393-E0A9-E50E24DCCA9E",
        "rx": "6E400012-B5A3-F393-E0A9-E50E24DCCA9E",
    },
}
### ====== BLE configuration ======

### ====== Modules configuration ======
LED_PIN = "D"
BUTTON_PIN = "E"
### ====== Modules configuration ======

### ====== I2S and Audio CONFIGURATION ======
SCK_PIN                  = const(0)
WS_PIN                   = const(1)
SD_PIN                   = const(2)
I2S_ID                   = const(0)
BUFFER_LENGTH_IN_BYTES   = const(16000)

WAV_SAMPLE_SIZE_IN_BITS  = const(16)
SAMPLE_RATE_IN_HZ        = const(16000)
NUM_CHANNELS             = const(1)
WAV_SAMPLE_SIZE_IN_BYTES = const(WAV_SAMPLE_SIZE_IN_BITS // 8)

I2S_CONFIG = {
    'sck': SCK_PIN,
    'ws': WS_PIN,
    'sd': SD_PIN,
    'id': I2S_ID,
    'bits': 32,
    'rate': SAMPLE_RATE_IN_HZ,
    'ibuf': 32000,
    'nch': NUM_CHANNELS,
    'wav_bits': 16
}
### ====== I2S and Audio CONFIGURATION ======

## ================================================
## Pico Central
## ================================================



## ================================================
## Elevator configuration
## ================================================

### ====== Hardware pins ======
AIR_PIN         = 8 #"F"   # air fan
CLIMATE_LED_PIN = "H"   # LEDTower: indicates heating / cooling state
CLIMATE_PIN     = "B"   # climate sensor (temp + humidity)
DISTANCE_PIN    = "A"
SERVO_PIN       = 9     # dispenser servo
LIGHTS_PIN      = "G"   # LEDTower: cabin lighting

ELEVATOR_PINS = {
    "air":         AIR_PIN,
    "climate_led": CLIMATE_LED_PIN,
    "climate":     CLIMATE_PIN,
    "distance":    DISTANCE_PIN,
    "lights":      LIGHTS_PIN,
    "servo":       SERVO_PIN,
}
### ====== Hardware pins ======

SERVO_POSES = {
    "open":      90,    # adjust to your servo's open angle
    "closed":    45,    # adjust to your servo's closed angle
    "delay_ms":  200,   # how long to hold open before closing
    "deinit_ms": 2500,  # wait after close command before deiniting PWM
}
## ================================================
## Elevator configuration
## ================================================



## ================================================
## Scales configuration
## ================================================

KNOWN_WEIGHT_GRAMM = 69.0

### ====== Hardware pins ======
SCALES_PINS = {
    "dt": 0,
    "sck": 1,
    "distance": "F",
    "servo": 9,
    "buzzer": "C",
}
### ====== Hardware pins ======

### ====== Gate & sensor thresholds ======
CAR_PRESENT_MM          = const(100)    # ToF reading <= this means car is present
GATE_CLOSE_DELAY_MS     = const(3000)   # ms to wait after car leaves before closing gate
WEIGHT_STABLE_READS     = const(3)      # consecutive stable reads to accept a weight
WEIGHT_STABLE_TOL_GRAMM = 50.0          # g tolerance for stability check
MIN_CAR_WEIGHT_GRAMM    = 30.0          # g minimum weight to consider a car on scales
### ====== Gate & sensor thresholds ======

### ====== Servo angles ======
SCALES_SERVO_POSES = {
    "open":   90,   # gate open angle
    "closed":  0,   # gate closed angle
}
### ====== Servo angles ======

### ====== Records file ======
RECORDS_FILE = "records.json"
### ====== Records file ======

## ================================================
## Scales configuration
## ================================================
