from ADCExt import ADC
from PinExt import Pin

# TODO: Add either read_u16() to analog pin, or expose analog pin altogether
MODULE_NAME = "SoundSensor"
class SoundSensor:
    def __init__(self, analog_pin, digital_pin):
        """
            Sound Sensor Module can return analog or digital value of sound. Threshold of Digital value of sound is defined by a switch on a module.
        """
        self._digital = Pin(digital_pin, Pin.IN)

        self._analog = None
        try:
            self._analog = ADC(analog_pin)
        except:
            print(f"[{MODULE_NAME}] Can't initialize analog port in this slot. Recommended to use sound sensor on slots C or F. Ignore it if you plan on using only read_digital() method")

    
    def read_digital(self) -> int: 
        """
            Returns digital value of sound sensor: 0 or 1
        """
        return self._digital.value()
    
    def read_analog(self, normalized=True) -> float:
        """
            Returns analog value of sound sensor: from 0 to 1.
        """
        return self._analog.read() if normalized else self._analog.read_u16()
    
    
    def read(self) -> tuple:
        """
            Returns tuple with digital and analog values of sound sensor. (d, a)
        """
        d = self.read_digital()
        a = self.read_analog()
        return (d, a)