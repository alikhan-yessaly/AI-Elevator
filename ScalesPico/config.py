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
AIR_PIN = "F"
COOLER_PIN = "H"
CLIMATE_PIN = "B"
DISTANCE_PIN = "A"
SERVO_PIN = 8

ELEVATOR_PINS = {
    "air": AIR_PIN,
    "cooler": COOLER_PIN,
    "climate": CLIMATE_PIN,
    "distance": DISTANCE_PIN,
    "servo": SERVO_PIN,
}
### ====== Hardware pins ======

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