#!/usr/bin/env python3
"""
Resets a Pico W via serial without needing raw REPL.
Sends burst Ctrl+C to reach the >>> prompt, then Ctrl+D for soft reset.
Exits 0 on success, 1 on failure.
Usage: python3 pico_reset.py <serial_port>
"""
import sys, time, serial

PORT = sys.argv[1]

def open_port(port, retries=10):
    for _ in range(retries):
        try:
            return serial.Serial(port, 115200, timeout=0.1)
        except serial.SerialException:
            time.sleep(0.3)
    return None

s = open_port(PORT)
if not s:
    print(f"Cannot open {PORT}", file=sys.stderr)
    sys.exit(1)

print(f"[reset] Opened {PORT}")
time.sleep(0.1)
s.read_all()

# Burst Ctrl+C until >>> prompt or timeout
print("[reset] Waiting for >>> prompt...")
buf = b''
deadline = time.time() + 5.0
while time.time() < deadline:
    s.write(b'\x03')
    time.sleep(0.01)
    chunk = s.read(128)
    if chunk:
        buf += chunk
        if b'>>> ' in buf:
            print("[reset] Got >>>")
            break
else:
    print("[reset] No >>> prompt - attempting reset anyway")

# Soft reset via Ctrl+D
print("[reset] Sending soft reset (Ctrl+D)...")
time.sleep(0.1)
s.read_all()
s.write(b'\x04')
time.sleep(0.2)
s.close()
print("[reset] Done. Device rebooting.")
