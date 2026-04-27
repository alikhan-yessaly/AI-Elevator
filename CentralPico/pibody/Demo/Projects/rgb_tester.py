from machine import Pin, ADC
from time import sleep, ticks_ms
from pibody import Encoder
from ..module import Module 
from ..projectConfig import ProjectConfig
from ..tester import Tester
from ..hinter import Hinter
import gc

hinter = Hinter()

project_config = ProjectConfig(
    title="RGB Tester",
    modules=[
        Module(Module.BUTTON_BLUE, "A"),
        Module(Module.BUTTON_YELLOW, "B"),
        Module(Module.POTENTIOMETER, "C"),
        Module(Module.ENCODER, "D"),
        Module(Module.SWITCH, "E"),
        Module(Module.TOUCH_SENSOR, "F")
    ],
    led_tower=True
)
class ModeManager:
    def __init__(self, np, adc, encoder, n=8):
        self.np = np
        self.adc = adc
        self.encoder = encoder
        self.n = n
        self.current_mode = 0
        self.current_color = (255, 0, 0)
        self.colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (0, 255, 255), (255, 0, 255),
            (255, 255, 255), (255, 165, 0)
        ]
        self.rainbow_offset = 0
        self.comet_direction = 1
        self.last_update = 0
        self.speed = 0
        self.max_speed = 0
        self.min_speed = 0

        self.modes = [
            ("Solid color", self.mode_solid),
            ("Rainbow", self.mode_rainbow),
            ("Comet", self.mode_comet),
            ("Blinking", self.mode_blink)
        ]

    def update_speed(self):
        if self.last_update != self.current_mode:
            if self.current_mode == 1:
                self.encoder.set(25, min_val=1, max_val=50, incr=1, range_mode=Encoder.RANGE_BOUNDED)
                self.max_speed = 1
                self.min_speed = 50
            elif self.current_mode == 2 or self.current_mode == 3:
                self.encoder.set(120, min_val=50, max_val=200, incr=10, range_mode=Encoder.RANGE_BOUNDED)
                self.max_speed = 50
                self.min_speed = 200
            self.last_update = self.current_mode
        self.speed = self.max_speed + self.min_speed - self.encoder.value()

    def get_brightness(self):
        pot_value = self.adc.read_u16()
        return 0.1 + (pot_value / 65535) * 0.9

    def apply_brightness(self, color):
        bright = self.get_brightness()
        return tuple(int(c * bright) for c in color)

    def mode_solid(self):
        color = self.apply_brightness(self.current_color)
        for i in range(self.n):
            self.np[i] = color
        self.np.write()

    def mode_rainbow(self):
        self.update_speed()
        for i in range(self.n):
            pos = ((i * 256 // self.n) + self.rainbow_offset) % 256
            if pos < 85:
                r, g, b = pos * 3, 255 - pos * 3, 0
            elif pos < 170:
                pos -= 85
                r, g, b = 255 - pos * 3, 0, pos * 3
            else:
                pos -= 170
                r, g, b = 0, pos * 3, 255 - pos * 3
            self.np[i] = self.apply_brightness((r, g, b))
        self.np.write()
        self.rainbow_offset = (self.rainbow_offset + 1) % 256
        sleep(self.speed / 1000)

    def mode_comet(self):
        self.update_speed()
        color = self.apply_brightness(self.current_color)
        tail = 2
        tick = (ticks_ms() // self.speed) % (self.n * 2 - 2)
        head = tick if tick < self.n else (self.n * 2 - 2) - tick
        self.comet_direction = 1 if tick < self.n else -1

        for i in range(self.n):
            self.np[i] = (0, 0, 0)

        for i in range(tail + 1):
            pos = head - i * self.comet_direction
            if 0 <= pos < self.n:
                fade = 1.0 if i == 0 else (tail - i + 1) / (tail + 1)
                self.np[pos] = tuple(int(c * fade) for c in color)

        self.np.write()

    def mode_blink(self):
        self.update_speed()
        color = self.apply_brightness(self.current_color)
        blink_state = (ticks_ms() // (self.speed * 5)) % 2
        for i in range(self.n):
            self.np[i] = color if blink_state else (0, 0, 0)
        self.np.write()

    def mode_off(self):
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
        self.np.write()

    def run_current_mode(self):
        self.modes[self.current_mode][1]()


class NeoPixelTester(Tester):
    def __init__(self):
        super().__init__(project_config)
    def init(self):
        super().init()
        for module in self.modules:
            if module.name == Module.BUTTON_BLUE:
                self.btn_prev = module.getPin(Pin.IN)
            if module.name == Module.BUTTON_YELLOW:
                self.btn_next = module.getPin(Pin.IN)
            if module.name == Module.POTENTIOMETER:
                self.adc = module.getADC()
            if module.name == Module.TOUCH_SENSOR:
                self.btn_color = module.getPin(Pin.IN)
            if module.name == Module.SWITCH:
                self.switch = module.getPin(Pin.IN)
            if module.name == Module.ENCODER:
                self.encoder = Encoder(module.getSlot())
        self.np = self.led_tower
        self.manager = ModeManager(self.np, self.adc, self.encoder, 8)

        self.last_button_press = 0
        self.debounce = 200

    def debounce_check(self):
        return ticks_ms() - self.last_button_press > self.debounce

    def handle_buttons(self):
        if not self.debounce_check():
            return

        if self.btn_prev.value() == 1:
            self.manager.current_mode = (self.manager.current_mode - 1) % len(self.manager.modes)
            print("Mode:", self.manager.modes[self.manager.current_mode][0])
            self.last_button_press = ticks_ms()
            # while self.btn_prev.value() == 1: sleep(0.001)

        if self.btn_next.value() == 1:
            self.manager.current_mode = (self.manager.current_mode + 1) % len(self.manager.modes)
            print("Mode:", self.manager.modes[self.manager.current_mode][0])
            self.last_button_press = ticks_ms()
            # while self.btn_next.value() == 1: sleep(0.001)

        if self.btn_color.value() == 1:
            idx = self.manager.colors.index(self.manager.current_color)
            self.manager.current_color = self.manager.colors[(idx + 1) % len(self.manager.colors)]
            print("Color changed to:", self.manager.current_color)
            self.last_button_press = ticks_ms()
            # while self.btn_color.value() == 1: sleep(0.001)

    def loop(self):
        self.handle_buttons()
        if self.switch.value() == 0:
            self.manager.mode_off()
            sleep(0.1)
            return
        self.manager.run_current_mode()
        sleep(0.005)

        if not self.isRunning:
            hinter.drawModules(project_config)
            return
