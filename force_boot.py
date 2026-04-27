#!/usr/bin/env python3
"""
Force-deploys boot.py by triggering a soft reset (Ctrl+D) and immediately
spamming Ctrl+A to catch the raw REPL window during the ~1s import phase
before BLE starts on ElevatorPico.
Usage: python3 force_boot.py <serial_port>
"""
import sys, time, serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/cu.usbmodem11201"

RAW_CMD = (
    b"f=open('/boot.py','w');f.write('import time\\ntime.sleep(3)\\n')"
    b";f.close();print('BOOT_OK')\x04"
)

def read_available(ser):
    time.sleep(0.02)
    return ser.read_all()

def try_write_boot(ser):
    ser.write(RAW_CMD)
    buf = b''
    deadline = time.time() + 2.0
    while time.time() < deadline:
        chunk = ser.read(128)
        if chunk:
            buf += chunk
            if b'BOOT_OK' in buf:
                return True
    return False

with serial.Serial(PORT, 115200, timeout=0.05) as ser:
    print(f"Opened {PORT}")
    read_available(ser)

    for attempt in range(3):
        print(f"\n=== Attempt {attempt+1}: soft reset + immediate raw REPL spam ===")

        # Step 1: interrupt whatever is running
        ser.write(b'\x03\x03')
        time.sleep(0.1)
        read_available(ser)

        # Step 2: soft reset via Ctrl+D (works in normal REPL without raw REPL)
        print("  Sending soft reset (Ctrl+D)...")
        ser.write(b'\x04')
        time.sleep(0.05)

        # Step 3: Spam Ctrl+A during the reboot+import window (~1.5 seconds)
        # Device is running: MicroPython init -> boot.py -> main.py imports
        # During imports, USB is active and Ctrl+A may be accepted
        print("  Spamming Ctrl+A during boot window...")
        found = False
        deadline = time.time() + 2.5
        while time.time() < deadline:
            ser.write(b'\x01')   # Ctrl+A = raw REPL entry
            time.sleep(0.02)
            buf = ser.read_all()
            if buf and b'>' in buf:
                print(f"  Raw REPL detected! (response: {buf[:40]!r})")
                found = True
                break

        if found:
            print("  Writing boot.py...")
            if try_write_boot(ser):
                print("\nboot.py written successfully!")
                print("Now run: ./deploy.sh elevator")
                sys.exit(0)
            else:
                print("  Write failed, retrying...")
        else:
            print("  Raw REPL not caught in boot window.")
            time.sleep(0.5)

    print("\nAll attempts failed.")
    print("Please PHYSICALLY unplug and replug the Elevator Pico, then immediately run:")
    print(f"  python3 force_boot.py {PORT}")
    print("That gives a clean boot without main.py running first.")
