from .Projects.rgb_tester import NeoPixelTester
from .Projects.dimming_tester import DimmingTester
from .Projects.gyropong_tester import GyroPongTester
from .Projects.joystick_tester import JoystickTester
from .Projects.any_meter_tester import AnyMeterTester
from .hinter import Hinter
from .tester import Tester
from machine import Pin
from pibody import display
import gc 

start_button = Pin(20, Pin.IN) 
select_button = Pin(21, Pin.IN)


class Demo():
    def __init__(self):
        self.hinter = Hinter()
        self.testers = [
            GyroPongTester(),
            DimmingTester(),
            NeoPixelTester(),
            AnyMeterTester(),
            JoystickTester(),
        ]
        self.selected_tester = self.testers[0]
        self.tester_index = 0
        
    def select_tester(self, tester: Tester):
        self.hinter.clear()
        if self.selected_tester is not None:
            self.selected_tester.stop()
        self.selected_tester = tester
        self.hinter.drawModules(self.selected_tester.config)
        
    def cancel_handler(self, pin):
        self.selected_tester.cancel_handler(pin)
        pin.irq(handler=None)  # Disable the cancel handler

    def start_selected_tester(self):
        if self.selected_tester is None:
            print("No tester selected")
            return
        
        gc.collect()
        self.hinter.tester_is_running(self.selected_tester.name)
        select_button.irq(trigger=Pin.IRQ_RISING, handler=self.cancel_handler) 
        try:
            self.selected_tester.start()
        except Exception as e:
            print("Error occurred: ", e)
            self.hinter.show_error(str(e))

    def draw_startup(self):
        display.draw_logo(y=90)
        display.fill_rect(100, 300, 140, 20, display.WHITE)
        arrow_polygon_nodes = [(10, 285) ,(10, 310), (35, 310), (27, 302), (43, 286), (34, 277), (18, 293), (10, 285)]
            
        display.fill_polygon(arrow_polygon_nodes, 0, 0, display.BLACK)
        display.fill_polygon(arrow_polygon_nodes, -80, 320, display.BLACK,4.71238898038)

        display.text("start", 10, 261, fg=display.BLACK, bg=display.WHITE)
        display.text("next", 198, 261, fg=display.BLACK, bg=display.WHITE)

        display.text("Press any button", 56, 290, fg=display.BLACK, bg=display.WHITE)
        display.hline(55, 306, 129, display.BLACK)
        
    def rotate_tester(self):
        self.tester_index = (self.tester_index + 1) % len(self.testers)
        self.select_tester(self.testers[self.tester_index])
        while select_button.value() == 1: pass

    def run(self):
        print("Demo started")
        self.draw_startup()

        while select_button.value() == 0 and start_button.value() == 0:
            pass

        self.select_tester(self.selected_tester)

        while True:
            if select_button.value() == 1:
                self.rotate_tester()
                
            if start_button.value() == 1:
                self.start_selected_tester()
                
