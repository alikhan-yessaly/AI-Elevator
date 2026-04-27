"""
calibrate.py  –  Run this once via Thonny / serial REPL to calibrate the scales.
After it completes, calibration.txt is saved and main.py will use it on every boot.

Steps:
  1. Make sure the scales are EMPTY and stable.
  2. Run this script.
  3. When prompted, place the known weight and press Enter.
  4. Done — calibration.txt is written.
"""

from time import sleep_us
from config import SCALES_PINS, KNOWN_WEIGHT_GRAMM
from ht771 import Scales

scales = Scales(SCALES_PINS["dt"], SCALES_PINS["sck"])

print("\n=== Scales Calibration ===")
print("Make sure the scales are EMPTY.")
input("Press Enter when ready to tare...")

print("Taring (reading empty scales)...")
scales.tare(reads=20)
print("Tare complete. Offset set to:", scales.offset)

print("\nPlace the known weight of %.1f g on the scales." % KNOWN_WEIGHT_GRAMM)
input("Press Enter when weight is placed and stable...")

print("Reading raw signal with weight...")
raw_readings = []
for _ in range(20):
    raw_readings.append(scales.read())  # raw HX711 value, no offset subtraction
    sleep_us(500)

raw_median = sorted(raw_readings)[len(raw_readings) // 2]
net = raw_median - scales.offset    # signal caused by the weight only

print("Raw median : %d" % raw_median)
print("Offset     : %d" % scales.offset)
print("Net signal : %d" % net)

if net == 0:
    print("\nERROR: Net signal is 0 — was the weight already on during taring?")
    print("Please restart and tare with EMPTY scales.")
else:
    factor = net / (KNOWN_WEIGHT_GRAMM / 1000)
    print("Factor     : %.4f" % factor)

    try:
        with open("calibration.txt", "w") as f:
            f.write(str(factor))
        print("\nCalibration complete!")
        print("Saved to calibration.txt — you can now run main.py normally.")
    except Exception as e:
        print("ERROR saving calibration file:", e)