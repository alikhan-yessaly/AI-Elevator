from ..module import Module
from ..tester import Tester
from ..hinter import Hinter
from ..projectConfig import ProjectConfig
from machine import Pin
from pibody import ClimateSensor, ColorSensor, DistanceSensor, Display
import time
from pibody import display

hinter = Hinter()

project_config = ProjectConfig(
    title="Any Meter",
    modules=[
        Module(Module.CLIMATE_SENSOR, "A"),
        Module(Module.COLOR_SENSOR, 'B'),
        Module(Module.SOUND_SENSOR, 'C'),
        Module(Module.TOUCH_SENSOR, 'D'),
        Module(Module.DISTANCE_SENSOR, 'E')
    ],
    led_tower=True
)

Modes = [
    "Color Sensor",
    "Sound Sensor",
    "Distance Sensor",
    "Climate Sensor"
]

x = 10
y = 32
length = 200
height = 9
border = True

###--- Climate Sensor Tester ---###
### If we want we can add humidity and pressure
temp_min = 20
temp_max = 30
color_temp_min = (255, 255, 0)
color_temp_max = (255, 0, 0)

def lerp_color(color1, color2, t):
    return tuple(int(color1[i] + (color2[i] - color1[i]) * t) for i in range(3))

def map_range(x, in_min, in_max, out_min, out_max):
    if x < in_min:
        return out_min
    if x > in_max:
        return out_max
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def show_value(np, value, min_val, max_val, color_start, color_end=None):
    length = map_range(value, min_val, max_val, 0, np.n)
    for i in range(np.n):
        if i < length:
            if color_end is not None:
                t = i / max(length - 1, 1)
                c = lerp_color(color_start, color_end, t)
            else:
                c = color_start
            np[i] = c
        else:
            np[i] = (0, 0, 0)
    np.write()

def get_color_by_temperature(temp, temp_min=temp_min, temp_max=temp_max):
    if temp > temp_max:
        return (255, 0, 0)
    elif temp < temp_min:
        return (255, 255, 0)
    else:
        ratio = (temp - temp_min) / (temp_max - temp_min)
        green = int(255 * (1 - ratio))
        return (255, green, 0)

def climatesensor_mode(np, data, data_max=temp_max, data_min=temp_min, color_data_min=color_temp_min, color_data_max=color_temp_max):
    val = max(min(data, data_max), data_min)
    show_value(np, val, data_min, data_max, color_data_min, color_data_max)

    color = get_color_by_temperature(data)
    display.text("Temperature: " + str(data) + "C      ", x, y + 9)
    display.linear_bar(x, y, length, value=val, min_value=data_min, max_value=data_max, height=height, border=True, color=display.color(*color))
###--- Climate Sensor Tester ---###


###--- Color Sensor Tester ---###
def colorsensor_mode(np, r, g, b, leds_num=8):
    for i in range(leds_num):
        np[i] = (r, g, b)
    np.write()

    display.linear_bar(x, y + 4, length, value=2, min_value=0, max_value=1, border=True, height=height + 8, color=display.color(r, g, b))
###--- Color Sensor Tester ---###


###--- Sound Sensor Tester ---###
max_deviation = 0

def soundsensor_mode(np, mic_value, decay_rate=1000, leds_num=8):
    global max_deviation
    deviation = abs(mic_value - 32768)
    if deviation > max_deviation:
        max_deviation = deviation
    else:
        max_deviation -= decay_rate
    
    max_deviation = max(max_deviation, 0)
    display.linear_bar(x, y, length, value=max_deviation, min_value=0, max_value=32768, border=True, height=height, color=display.YELLOW)

    fill_value = int(max_deviation / 32768 * leds_num) + 1
    fill_value = min(fill_value, leds_num) 

    for i in range(fill_value):
        color = (0, 50, 0) if i < 5 else (50, 0, 0)
        if i == fill_value - 1:
            color = (50, 20, 0)
        np[i] = color
    for i in range(fill_value, 8):
        np[i] = (0, 0, 0)
    np.write()
###--- Sound Sensor Tester ---###


###--- Distance Sensor Tester ---###
min_dist = 50
max_dist = 300

def get_color_by_distance(dist, min_dist=min_dist, max_dist=max_dist):
    if dist > max_dist:
        return (0, 255, 0)
    elif dist < min_dist:
        return (255, 0, 0) 
    else:
        ratio = (dist - min_dist) / (max_dist - min_dist)
        red = int(255 * (1 - ratio))
        green = int(255 * ratio)
        return (red, green, 0)
    
def display_bar(np, dist, leds_num=8, min_dist=min_dist, max_dist=max_dist):
    dist = max(min_dist, min(dist, max_dist))
    level = int((dist - min_dist) / (max_dist - min_dist) * leds_num)
    color = get_color_by_distance(dist)
    display.linear_bar(x, y, length, value=dist, min_value=min_dist, max_value=max_dist, height=height, border=True, color=display.color(*color))
    for i in range(leds_num):
        np[i] = color if i < level else (0, 0, 0)
    np.write()

def distance_mode(np, sensor, dist, leds_num=8):
    if sensor.is_valid(dist):
        display_bar(np, dist)
        display.text("Distance: " + str(dist) + "/300 mm           ", x, y + 9)
    else:
        display.linear_bar(x, y, length, value=0, min_value=min_dist, max_value=max_dist, height=height, border=True, color=0)
        display.text("Distance: Invalid value     ", x, y + 9)
        for i in range(leds_num):
            np[i] = (0, 0, 0)
        np.write()
###--- Distance Sensor Tester ---###


class AnyMeterTester(Tester):
    def __init__(self):
        super().__init__(project_config)

    def init(self):
        super().init()
        for module in self.modules:
            if module.name == Module.SOUND_SENSOR:
                self.sound_sensor = module.getADC()
            if module.name == Module.TOUCH_SENSOR:
                self.touch = module.getPin(Pin.IN)
            if module.name == Module.DISTANCE_SENSOR:
                self.distance_sensor = DistanceSensor(module.getSlot())
            if module.name == Module.CLIMATE_SENSOR:
                self.climate_sensor = ClimateSensor(module.getSlot())
            if module.name == Module.COLOR_SENSOR:
               self.color_sensor = ColorSensor(module.getSlot())
        self.mode = 0
        self.last_touch = 0
        
    def loop(self):
        display.text("Press 'Touch'", 10, 284)
        display.text("to change sensor", 10, 300)
        
        if self.touch.value() == 1 and (time.ticks_ms() - self.last_touch) > 500:
            self.mode = (self.mode + 1) % len(Modes)
            self.last_touch = time.ticks_ms()
            print(f"Mode changed to: {Modes[self.mode]}")
            display.fill_rect(x - 3, y - 9, x + length + 10, y + 35, 0)
        

        # Color Sensor Tester
        elif self.mode == 0:
            try:
                r, g, b = self.color_sensor.readRGB()
                colorsensor_mode(self.led_tower, r, g, b)
                display.text("Color Sensor is working   ", x, y - 22)
            except Exception as e:
                print(f"Error starting tester: {e}")
                

        # Sound Sensor Tester
        elif self.mode == 1:
            mic_value = self.sound_sensor.read_u16()
            soundsensor_mode(self.led_tower, mic_value)
            display.text("Sound Sensor is working     ", x, y - 22)

        # Distance Sensor Tester
        elif self.mode == 2:
            try:
                distance = self.distance_sensor.read()
                distance_mode(self.led_tower, self.distance_sensor, distance)
                display.text("Distance Sensor is working", x, y - 22)
            except Exception as e:
                print(f"Error starting tester: {e}")
        
        # Climate Sensor Tester
        elif self.mode == 3:
            try:
                data = self.climate_sensor.read()
                climatesensor_mode(self.led_tower, data["temperature"])
                display.text("Climate Sensor is working ", x, y - 22)
            except Exception as e:
                print(f"Error starting tester: {e}")

        if not self.isRunning:
            hinter.drawModules(project_config)
            return

