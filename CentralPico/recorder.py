from machine import Pin, I2S
import os
import gc

SAMPLE_RATE   = 16000
BITS          = 16
CHANNELS      = 1
MAX_SECONDS   = 15
IBUF          = 4096
READ_BUF_SIZE = 1024  # ~32ms per chunk at 16kHz 16-bit mono

MAX_REC_BYTES = MAX_SECONDS * SAMPLE_RATE * (BITS // 8) * CHANNELS

_SCK_PIN = 0
_WS_PIN  = 1
_SD_PIN  = 2
_I2S_ID  = 0


def init_i2s():
    return I2S(
        _I2S_ID,
        sck    = Pin(_SCK_PIN),
        ws     = Pin(_WS_PIN),
        sd     = Pin(_SD_PIN),
        mode   = I2S.RX,
        bits   = BITS,
        format = I2S.MONO,
        rate   = SAMPLE_RATE,
        ibuf   = IBUF,
    )


def reinit_i2s(audio_in):
    """Deinit the existing I2S instance and create a fresh one. Returns new instance or None."""
    try:
        if audio_in is not None:
            audio_in.deinit()
    except Exception:
        pass
    try:
        gc.collect()
        return init_i2s()
    except Exception as e:
        print("[I2S] reinit failed:", e)
        return None


def record_to_wav(audio_in, is_recording, wav_path):
    """
    Blocking I2S recording.
    Calls is_recording() each ~32ms chunk; stops when it returns falsy or max time hit.
    Writes a complete 16-bit mono WAV directly to wav_path.
    Returns total audio bytes written (0 = empty, >= MAX_REC_BYTES = auto-stopped).
    """
    from wav import create_wav_header
    gc.collect()

    buf   = bytearray(READ_BUF_SIZE)
    mv    = memoryview(buf)
    total = 0

    try:
        os.remove(wav_path)
    except OSError:
        pass

    # Warmup: discard first buffer so the mic stabilises before we open the file
    audio_in.readinto(mv)

    with open(wav_path, "wb") as f:
        f.seek(44)  # leave room for the 44-byte WAV header
        while is_recording() and total < MAX_REC_BYTES:
            n = audio_in.readinto(mv)
            if n > 0:
                try:
                    f.write(mv[:n])
                except OSError as e:
                    print("[REC] SD write error:", e)
                    break
                total += n

        if total > 0:
            num_samples = total // ((BITS // 8) * CHANNELS)
            f.seek(0)
            f.write(create_wav_header(SAMPLE_RATE, BITS, CHANNELS, num_samples))

    gc.collect()
    return total
