"""
ble_test.py  –  Run via mpremote on Central Pico only.
Scans for Elevator Pico and Scales Pico, connects to both sequentially,
and prints a SUCCESS message when both handles are live.
"""
import bluetooth, time

_IRQ_SCAN_RESULT           = 5
_IRQ_SCAN_DONE             = 6
_IRQ_PERIPHERAL_CONNECT    = 7
_IRQ_PERIPHERAL_DISCONNECT = 8

TARGETS = [b"Elevator Pico", b"Scales Pico"]

found     = {}   # name -> (addr_type, addr_bytes)
connected = {}   # conn_handle -> name
connect_queue = []  # (addr_type, addr_bytes) to connect next

ble = bluetooth.BLE()
ble.active(True)

def _adv_name(data):
    i = 0
    while i < len(data):
        n = data[i]
        if n == 0:
            break
        if data[i + 1] in (0x08, 0x09):
            return bytes(data[i + 2 : i + 1 + n])
        i += 1 + n
    return None

def irq(event, data):
    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        name = _adv_name(bytes(adv_data))
        if name in TARGETS and name not in found:
            found[name] = (addr_type, bytes(addr))
            print("[scan] found", name)

    elif event == _IRQ_SCAN_DONE:
        print("[scan] done —", len(found), "target(s) located")
        for name in TARGETS:
            if name in found:
                connect_queue.append((name, found[name]))
        # kick off first connection
        _connect_next()

    elif event == _IRQ_PERIPHERAL_CONNECT:
        conn_handle, addr_type, addr = data
        addr_b = bytes(addr)
        for name, (at, a) in found.items():
            if a == addr_b:
                connected[conn_handle] = name
                print("[conn] CONNECTED handle=%d  device=%s" % (conn_handle, name))
        # kick off next connection if any remain
        _connect_next()

    elif event == _IRQ_PERIPHERAL_DISCONNECT:
        conn_handle, _, _ = data
        name = connected.pop(conn_handle, b"?")
        print("[conn] disconnected", name)

def _connect_next():
    if connect_queue:
        name, (at, addr) = connect_queue.pop(0)
        print("[conn] connecting to", name)
        ble.gap_connect(at, addr)

ble.irq(irq)
print("[scan] starting 8-second scan …")
ble.gap_scan(8000, 30000, 30000)

for _ in range(200):
    time.sleep_ms(100)
    if len(connected) >= 2:
        break

print()
if len(connected) >= 2:
    print("SUCCESS: both connections live simultaneously!")
else:
    print("PARTIAL: %d/2 connected" % len(connected))
for h, n in connected.items():
    print("  handle=%d  %s" % (h, n))
