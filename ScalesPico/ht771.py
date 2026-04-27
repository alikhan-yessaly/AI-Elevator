from utime import sleep_us, time
from machine import Pin
from micropython import const


class HX711Exception(Exception):
    pass


class InvalidMode(HX711Exception):
    pass


class DeviceIsNotReady(HX711Exception):
    pass

# lib taken from https://github.com/SergeyPiskunov/micropython-hx711
class HX711(object):
    """
    Micropython driver for Avia Semiconductor's HX711
    24-Bit Analog-to-Digital Converter
    """
    CHANNEL_A_128 = const(1)
    CHANNEL_A_64 = const(3)
    CHANNEL_B_32 = const(2)

    DATA_BITS = const(24)
    MAX_VALUE = const(0x7fffff)
    MIN_VALUE = const(0x800000)
    READY_TIMEOUT_SEC = const(5)
    SLEEP_DELAY_USEC = const(80)

    def __init__(self, d_out: int, pd_sck: int, channel: int = CHANNEL_A_128):
        self.d_out_pin = Pin(d_out, Pin.IN)
        self.pd_sck_pin = Pin(pd_sck, Pin.OUT, value=0)
        self.channel = channel

    def __repr__(self):
        return "HX711 on channel %s, gain=%s" % self.channel

    def _convert_from_twos_complement(self, value: int) -> int:
        """
        Converts a given integer from the two's complement format.
        """
        if value & (1 << (self.DATA_BITS - 1)):
            value -= 1 << self.DATA_BITS
        return value

    def _set_channel(self):
        """
        Input and gain selection is controlled by the
        number of the input PD_SCK pulses
        3 pulses for Channel A with gain 64
        2 pulses for Channel B with gain 32
        1 pulse for Channel A with gain 128
        """
        for i in range(self._channel):
            self.pd_sck_pin.value(1)
            self.pd_sck_pin.value(0)

    def _wait(self):
        """
        If the HX711 is not ready within READY_TIMEOUT_SEC
        the DeviceIsNotReady exception will be thrown.
        """
        t0 = time()
        while not self.is_ready():
            if time() - t0 > self.READY_TIMEOUT_SEC:
                raise DeviceIsNotReady()

    @property
    def channel(self) -> tuple:
        """
        Get current input channel in a form
        of a tuple (Channel, Gain)
        """
        if self._channel == self.CHANNEL_A_128:
            return 'A', 128
        if self._channel == self.CHANNEL_A_64:
            return 'A', 64
        if self._channel == self.CHANNEL_B_32:
            return 'B', 32

    @channel.setter
    def channel(self, value):
        """
        Set input channel
        HX711.CHANNEL_A_128 - Channel A with gain 128
        HX711.CHANNEL_A_64 - Channel A with gain 64
        HX711.CHANNEL_B_32 - Channel B with gain 32
        """
        if value not in (self.CHANNEL_A_128, self.CHANNEL_A_64, self.CHANNEL_B_32):
            raise InvalidMode('Gain should be one of HX711.CHANNEL_A_128, HX711.CHANNEL_A_64, HX711.CHANNEL_B_32')
        else:
            self._channel = value

        if not self.is_ready():
            self._wait()

        for i in range(self.DATA_BITS):
            self.pd_sck_pin.value(1)
            self.pd_sck_pin.value(0)

        self._set_channel()

    def is_ready(self) -> bool:
        """
        When output data is not ready for retrieval,
        digital output pin DOUT is high.
        """
        return self.d_out_pin.value() == 0

    def power_off(self):
        """
        When PD_SCK pin changes from low to high
        and stays at high for longer than 60 us ,
        HX711 enters power down mode.
        """
        self.pd_sck_pin.value(0)
        self.pd_sck_pin.value(1)
        sleep_us(self.SLEEP_DELAY_USEC)

    def power_on(self):
        """
        When PD_SCK returns to low, HX711 will reset
        and enter normal operation mode.
        """
        self.pd_sck_pin.value(0)
        self.channel = self._channel

    def read(self, raw=False):
        """
        Read current value for current channel with current gain.
        if raw is True, the HX711 output will not be converted
        from two's complement format.
        """
        if not self.is_ready():
            self._wait()

        raw_data = 0
        for i in range(self.DATA_BITS):
            self.pd_sck_pin.value(1)
            self.pd_sck_pin.value(0)
            raw_data = raw_data << 1 | self.d_out_pin.value()
        self._set_channel()

        if raw:
            return raw_data
        else:
            return self._convert_from_twos_complement(raw_data)
    
# wrapper for the hx711 library
class Scales(HX711):
    def __init__(self, d_out, pd_sck):
        super(Scales, self).__init__(d_out, pd_sck)
        self.offset = 0
        self.scale = 1.0
        print("Initializing scales")
        try:
            with open("calibration.txt", "r") as f:
                calibration_factor = float(f.read().strip())
                print("Using calibration factor from file:", calibration_factor)
                self.set_scale(calibration_factor)
        except Exception as e:
            print("Calibration file not found, using default factor:", 1)
            self.set_scale(1)

    def reset(self):
        self.power_off()
        self.power_on()

    def tare(self, reads=15, delay_us=500):
        self.offset = self.stable_value(reads=reads, delay_us=delay_us)

    def set_scale(self, scale):
        if scale == 0:
            raise ValueError("Scale factor cannot be zero")
        self.scale = scale

    def start_calibration(self, KNOWN_WEIGHT_GRAMM: float):
        self.tare()
        # read the calibration data from file: remember this is a micropython

        factor = self._calibrate(KNOWN_WEIGHT_GRAMM)
        try:
            with open("calibration.txt", "w") as f:
                f.write(str(factor))
                print("Calibration factor saved to file.")

        except Exception as e:
            print("Error saving calibration factor to file:", e)

        self.scale = factor
        print("Calibration complete. Scale factor set to:", self.scale)

    def _calibrate(self, known_weight_gramm, reads=20, delay_us=500):
        if known_weight_gramm <= 0:
            raise ValueError("Known weight must be > 0 gramm")
        raw = self.stable_value(reads=reads, delay_us=delay_us)
        self.scale = raw / (known_weight_gramm / 1000)
        return self.scale

    def raw_value(self):
        return self.read() - self.offset

    def weight_gramm(self, reads=10, delay_us=500):
        return self.stable_value(reads=reads, delay_us=delay_us) / self.scale * 1000

    def stable_value(self, reads=10, delay_us=500):
        values = []
        for _ in range(reads):
            values.append(self.raw_value())
            sleep_us(delay_us)
        return self._stabilizer(values)

    @staticmethod
    def _stabilizer(values, deviation=10):
        weights = []
        for prev in values:
            if prev == 0:
                weights.append(sum([1 for current in values if current == 0]))
                continue
            weights.append(sum([1 for current in values if abs(prev - current) / (abs(prev) / 100) <= deviation]))
        return sorted(zip(values, weights), key=lambda x: x[1]).pop()[0]
