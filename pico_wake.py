#!/usr/bin/env python3
"""
Send Ctrl-C over serial to interrupt a running MicroPython program and
bring the Pico back to the >>> REPL prompt before mpremote connects.
"""
import sys, time

try:
    import serial
except ImportError:
    print("[wake] pyserial not installed — skipping wake step")
    sys.exit(0)

port    = sys.argv[1]
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

try:
    with serial.Serial(port, 115200, timeout=0.3) as s:
        s.reset_input_buffer()
        # Fire Ctrl-C three times to break out of any running loop
        for _ in range(3):
            s.write(b'\r\x03')
            time.sleep(0.15)

        # Wait for >>> prompt
        deadline = time.time() + timeout
        buf = b''
        while time.time() < deadline:
            chunk = s.read(128)
            if chunk:
                buf += chunk
                if b'>>> ' in buf:
                    print("[wake] Pico at REPL prompt — ready")
                    sys.exit(0)
            time.sleep(0.05)

        print("[wake] Timeout waiting for >>> — proceeding anyway")

except Exception as e:
    print(f"[wake] {e} — skipping wake step")

sys.exit(0)
