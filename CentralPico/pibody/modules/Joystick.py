from ADCExt import ADC 
from machine import Pin

MODULE_NAME = "Joystick"

class Joystick():
    def __init__(self, pinX, pinY):
        self.X = None
        self.Y = None 

        if pinX is not None:
            try:
                self.X = ADC(Pin(pinX))
            except Exception as e:
                print(f"[{MODULE_NAME}] Failed to init X axis on pin {pinX}: {e}")
        if pinY is not None:
            try:
                self.Y = ADC(Pin(pinY))
            except Exception as e:
                print(f"[{MODULE_NAME}] Failed to init Y axis on pin {pinY}: {e}")

    def read(self):
        return (self.read_x(), self.read_y())
    
    def read_x(self):
        if self.X is None:
            return None
        return self.X.read()

    def read_y(self):
        if self.Y is None:
            return None
        return self.Y.read()