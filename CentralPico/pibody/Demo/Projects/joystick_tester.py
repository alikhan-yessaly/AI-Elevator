from ..tester import Tester
from ..module import Module
from ..hinter import Hinter
from ..projectConfig import ProjectConfig
import math

hinter = Hinter()

project_config = ProjectConfig(
    title="Joystick",
    modules=[
        Module(Module.JOYSTICK, "F")
    ],
    servo8=True,
    servo9=True
)

def angle_to_duty(angle):
    min_u16 = int((0.5 / 20) * 65535)
    max_u16 = int((2.5 / 20) * 65535)
    return int(min_u16 + (max_u16 - min_u16) * angle / 180)

def joystick_to_angle(raw_val):
    norm = raw_val / 65535
    eased = 0.5 - 0.5 * math.cos(norm * math.pi)  # плавность
    return int(eased * 180)

class JoystickTester(Tester):
    def __init__(self):
        super().__init__(project_config)

    def init(self):
        super().init()
        for module in self.modules:
            if module.name == Module.JOYSTICK:
                self.adc1, self.adc2 = module.get2ADC()
        self.servo.freq(50)
        self.servo9.freq(50)

    def loop(self):
        raw_x = self.adc1.read_u16()
        raw_y = self.adc2.read_u16()

        angle0 = joystick_to_angle(raw_x)
        angle1 = joystick_to_angle(raw_y)

        self.servo.duty_u16(angle_to_duty(angle0))
        self.servo9.duty_u16(angle_to_duty(angle1))

        if not self.isRunning:
            hinter.drawModules(project_config)
            return

