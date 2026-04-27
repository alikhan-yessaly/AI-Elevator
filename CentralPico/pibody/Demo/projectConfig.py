from .module import Module

class ProjectConfig():
    def __init__(self, title, modules: list[Module], led_tower=False, servo8=False, servo9=False):
        self.title = title
        self.led_tower = led_tower
        self.servo8 = servo8
        self.servo9 = servo9
        self.modules = modules

    def getModules(self):
        return self.modules

    def getModuleBySlot(self, slot):
        slot = slot[0].upper()
        for module in self.modules:
            if module.getSlot() == slot:
                return module
        raise ValueError(f"Module with slot '{slot}' not found")

    def getTitle(self):
        return self.title

    def getLedTower(self):
        return self.led_tower

    def getServo8(self):
        return self.servo8
    
    def getServo9(self):
        return self.servo9