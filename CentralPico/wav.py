def create_wav_header(sample_rate, bits, channels, num_samples):
    datasize = num_samples * channels * bits // 8
    o  = b"RIFF"
    o += (datasize + 36).to_bytes(4, "little")
    o += b"WAVE"
    o += b"fmt "
    o += (16).to_bytes(4, "little")
    o += (1).to_bytes(2, "little")
    o += channels.to_bytes(2, "little")
    o += sample_rate.to_bytes(4, "little")
    o += (sample_rate * channels * bits // 8).to_bytes(4, "little")
    o += (channels * bits // 8).to_bytes(2, "little")
    o += bits.to_bytes(2, "little")
    o += b"data"
    o += datasize.to_bytes(4, "little")
    return o
