from .projectConfig import ProjectConfig
from pibody import LEDTower
from machine import PWM, Pin
import gc


class Tester():
    def __init__(self, project_config: ProjectConfig):
        self.config = project_config
        self.name = project_config.getTitle()
        self.isRunning = False

    def loop(self):
        pass

    def init(self):
        project_config = self.config
        self.name = project_config.getTitle()

        config = self.config
        self.modules = config.getModules()

        if config.getLedTower():
            self.led_tower = LEDTower(8)

        if config.getServo8():
            self.servo = PWM(Pin(8))

        if config.getServo9():
            self.servo9 = PWM(Pin(9))  

    def start(self):
        self.init()
        print(f"Starting tester: {self.name}")
        self.isRunning = True
        while self.isRunning:
            self.loop()
            gc.collect()

    def stop(self):
        self.led_tower = None
        self.servo = None
        self.servo9 = None
        self = None
        gc.collect()

    def cancel_handler(self, pin):
        if not self.isRunning:
            return
        self.isRunning = False
        print("Test cancelled")
