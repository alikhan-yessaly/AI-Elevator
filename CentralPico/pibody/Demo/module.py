from machine import Pin, I2C, SoftI2C, PWM, ADC
png_path = "pibody/Demo/module_pngs/"


SLOT_MAP = {
        "A": (0, 1, 0),
        "B": (2, 3, 1),
        "C": (28, 22),
        "D": (4, 5, 0),
        "E": (6, 7, 1),
        "F": (26, 27, 1),
        "G": (16, 17, 0),
        "H": (18, 19, 1)
    }

class Module():
    def __init__(self, name: str, slot: str):
        if name not in self.getAllModules():
            raise ValueError(f"Module name '{name}' is not valid")

        slot = slot[0].upper()
        if slot not in SLOT_MAP:
            raise ValueError(f"Slot '{slot}' is not valid. Available slots are: {', '.join(SLOT_MAP.keys())}")

        self.name = name
        self.slot = slot
        self.sda = SLOT_MAP[slot][0]
        self.scl = SLOT_MAP[slot][1] 
        self.bus = SLOT_MAP[slot][2] if len(SLOT_MAP[slot]) > 2 else None
        self.I2C = None
        self.SoftI2C = None
        
    def getSlot(self):
        return self.slot
    
    def getPin(self, mode=Pin.IN | Pin.OUT):
        return Pin(self.sda, mode)
    
    def getPWM(self):
        return PWM(Pin(self.sda))

    def getADC(self):
        return ADC(Pin(self.sda))
    
    def get2ADC(self):
        if self.scl is None:
            raise ValueError(f"Slot does not have a second ADC pin defined.")
        return ADC(Pin(self.sda)), ADC(Pin(self.scl))
    
    def getI2C(self):
        if self.bus is None:
            raise ValueError(f"Slot does not have a bus defined.")
        
        if self.I2C is not None:
            self.I2C = I2C(self.bus, scl=Pin(self.scl), sda=Pin(self.sda))
        
        return self.I2C
        
    def getSoftI2C(self):
        if self.SoftI2C is not None:
            self.SoftI2C = SoftI2C(scl=Pin(self.scl), sda=Pin(self.sda))
        return self.SoftI2C
    
    def getSda(self):
        return self.sda 
    
    def getScl(self):
        return self.scl if self.scl is not None else None

    def getPngPath(self):
        return f"{png_path}{self.name}.png"
    
    def __str__(self):
        return self.name

    """Enum for all available modules."""
    BUTTON_BLUE = "button_blue"
    BUTTON_YELLOW = "button_yellow"
    BUZZER = "buzzer"
    LED_G = "led_green"
    LED_R = "led_red"
    LED_Y = "led_yellow"
    MOTION_SENSOR = "motion_sensor"
    POTENTIOMETER = "potentiometer"
    SWITCH = "switch"
    TOUCH_SENSOR = "touch_sensor"
    LIGHT_SENSOR = "light_sensor"
    CLIMATE_SENSOR = "climate_sensor"
    COLOR_SENSOR = "color_sensor"
    DISTANCE_SENSOR = "distance_sensor"
    ENCODER = "encoder"
    GYRO_ACCEL = "gyro_accel"
    JOYSTICK = "joystick"
    SOUND_SENSOR = "sound_sensor"

    @classmethod
    def getAllModules(cls):
        """Returns a list of all module values."""
        return [getattr(cls, attr) for attr in dir(cls) if not attr.startswith("__") and not callable(getattr(cls, attr))]
