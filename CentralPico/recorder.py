import machine
import utime
import array
import gc
import os

gc.collect()

SAMPLE_RATE = 16000
MAX_REC_SECONDS = 15
CHUNK_SIZE = 1024

RAW_FILE = "recording.raw"

SAMPLE_INTERVAL_US = 1_000_000 // SAMPLE_RATE  # 62 µs


# =========================
# 1. RECORD RAW (8-bit)
# =========================
def record_raw(mic, button, filename=RAW_FILE):
    """
        This function records sound from mic module until button returns value 1 and stores recording in filename in flash memory.
    """
    max_samples = SAMPLE_RATE * MAX_REC_SECONDS
    print(f"Recording seconds to RAW file (8-bit)...")

    # 'B' = unsigned 8-bit int
    chunk = array.array('B', [0] * CHUNK_SIZE)
    prev_val = 0
    samples_written = 0

    try:
        os.remove(filename)
    except:
        pass

    with open(filename, 'wb') as f:
        while button.read():
            t = utime.ticks_us()
            for i in range(CHUNK_SIZE):
                # read_u16() returns 0–65535; shift down to 0–255
                raw = mic.read_u16() >> 8
                smoothed = (raw + prev_val) // 2
                chunk[i] = smoothed
                prev_val = smoothed

                t = utime.ticks_add(t, SAMPLE_INTERVAL_US)
                utime.sleep_us(max(0, utime.ticks_diff(t, utime.ticks_us())))

            f.write(chunk)
            samples_written += CHUNK_SIZE

            if samples_written >= max_samples:
                return -1
    return 0


# =========================
# 2. PLAY RAW (8-bit)
# =========================
def play_raw(buzzer, filename=RAW_FILE):
    print("Playing RAW (8-bit)...")
    buzzer.freq(200000)  # carrier frequency

    chunk = bytearray(CHUNK_SIZE)

    with open(filename, 'rb') as f:
        while True:
            n = f.readinto(chunk)
            if not n:
                break

            t = utime.ticks_us()
            for i in range(n):
                # Shift 0–255 up to 0–65535 for PWM
                buzzer.duty_u16(chunk[i] << 8)

                t = utime.ticks_add(t, SAMPLE_INTERVAL_US)
                utime.sleep_us(max(0, utime.ticks_diff(t, utime.ticks_us())))

    buzzer.duty_u16(0)
    print("Playback done!")


# =========================
# 3. CONVERT RAW → WAV (8-bit)
# =========================
def convert_raw_to_wav(dest_file, soucre_file=RAW_FILE):
    print("Converting RAW → WAV (8-bit)...")

    try:
        os.remove(dest_file)
    except:
        pass

    size = os.stat(soucre_file)[6]  # raw file size in bytes

    BITS_PER_SAMPLE = 8
    NUM_CHANNELS = 1
    BLOCK_ALIGN = NUM_CHANNELS * (BITS_PER_SAMPLE // 8)  # = 1
    BYTE_RATE = SAMPLE_RATE * BLOCK_ALIGN                 # = 16000

    with open(dest_file, 'wb') as f:
        # === WAV HEADER ===
        f.write(b'RIFF')
        f.write((36 + size).to_bytes(4, 'little'))
        f.write(b'WAVE')

        # fmt chunk
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))              # chunk size
        f.write((1).to_bytes(2, 'little'))               # PCM format
        f.write((NUM_CHANNELS).to_bytes(2, 'little'))    # mono
        f.write((SAMPLE_RATE).to_bytes(4, 'little'))     # sample rate
        f.write((BYTE_RATE).to_bytes(4, 'little'))       # byte rate
        f.write((BLOCK_ALIGN).to_bytes(2, 'little'))     # block align
        f.write((BITS_PER_SAMPLE).to_bytes(2, 'little')) # bits per sample

        # data chunk
        f.write(b'data')
        f.write((size).to_bytes(4, 'little'))

        # === COPY AUDIO DATA ===
        with open(soucre_file, 'rb') as r:
            while True:
                chunk = r.read(CHUNK_SIZE)  # 1 byte per sample
                if not chunk:
                    break
                f.write(chunk)

    print(f"WAV file ready! Size: {size}")