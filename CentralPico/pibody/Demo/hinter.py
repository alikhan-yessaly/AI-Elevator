from pibody import display
from pibody.Demo.module import Module
from pibody.Demo.projectConfig import ProjectConfig
import gc
import time


SLOTS_COORDS = {
    "A": (10, 0),
    "B": (10, 90),
    "C": (10, 180),
    "D": (150, 0),
    "E": (150, 90),
    "F": (150, 180)
}

png_path = "pibody/Demo/module_pngs/"

def safe_draw_png(path, x, y, retries=10, delay=0.1):
    for attempt in range(retries):
        try:
            gc.collect()  # clean memory before each try
            display.png(path, x, y)
            return True  # success
        except MemoryError:
            print("MemoryError — retrying ({}/{})...".format(attempt + 1, retries))
            gc.collect()
            time.sleep(delay)
    print("Failed to draw PNG after {} retries.".format(retries))
    return False

    
class Hinter():
    def __init__(self):
        self.clear()

    def tester_is_running(self, tester_name):
        self.clear()
        text_color = display.color(120, 255, 50)  # Green color
        display.text(f"{tester_name}", 10, 120, display.font_bold, text_color, display.BLACK)
        display.text("is running", 10, 150, display.font_bold, text_color, display.BLACK)
        display.text("GP21", 204, 300, display.font_small, fg=display.CYAN)
        display.text("cancel", 154, 300, display.font_small)

    def clear(self):
        display.fill(display.BLACK)

    def drawModule(self, module :Module, slot):
        x, y = SLOTS_COORDS[slot]
        safe_draw_png(module.getPngPath(), x, y)

    def drawModules(self, config: ProjectConfig):
        title = config.getTitle()
        led_tower = config.getLedTower()
        servo8 = config.getServo8()
        servo9 = config.getServo9()
        modules = config.getModules()


        display.fill(display.BLACK)  # Clear the screen
        for module in modules:
            slot = module.getSlot()

            if slot in SLOTS_COORDS:
                self.drawModule(module, slot)
            else:
                print(f"Invalid slot: {slot}")

        display.text(title, 10, 265, display.font_bold, display.WHITE, display.BLACK)
        display.text("GP20", 10, 300, display.font_small, fg=display.CYAN)
        display.text("start", 44, 300, display.font_small)
        display.text("GP21", 204, 300, display.font_small, fg=display.CYAN)
        display.text("next", 170, 300, display.font_small)
        if led_tower:
            display.png(f"{png_path}led_tower.png", 110, 0)
        if servo8 or servo9:
            display.png(f"{png_path}servo.png", 90, 200)
            txt = "8" if servo8 else ""
            txt += "/" if servo8 and servo9 else ""
            txt += "9" if servo9 else ""
            display.text(font=display.font_small, text=txt, x=110, y=250, fg=display.WHITE, bg=display.BLACK)

    def show_error(self, message):
        self.clear()
        text_color = display.color(120, 100, 20)
        
        lines = [message[i:i+28] for i in range(0, len(message), 28)]
        for i, line in enumerate(lines):
            display.text(font=display.font_small, text=line, x=10, y=20 + i * 20, fg=text_color, bg=display.BLACK)
        display.text("GP20", 10, 300, display.font_small, fg=display.CYAN)
        display.text("start", 44, 300, display.font_small)
        display.text("GP21", 204, 300, display.font_small, fg=display.CYAN)
        display.text("next", 170, 300, display.font_small)
        
