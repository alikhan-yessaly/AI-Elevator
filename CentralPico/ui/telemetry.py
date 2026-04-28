from pibody import display
from TelemetryData import ElevatorData, ScalesData


class TelemetryDisplayer:
    def __init__(self, elevator_pivot, scales_pivot, line_width=120):
        self.LINE_WIDTH = line_width
        
        self.elevator_px = elevator_pivot[0]
        self.elevator_py = elevator_pivot[1]

        self.scales_px = scales_pivot[0]
        self.scales_py = scales_pivot[1]



    def render_elevator(self, data: ElevatorData):
        x = self.elevator_px
        y = self.elevator_py
        display.text("Температура: " + str(data.temperature) + " C  ", x, y)
        y += 13
        display.linear_bar(x, y+8, self.LINE_WIDTH, value=data.temperature, min_value=20, max_value=30, height=8, border=True, color=display.RED)
        y += 4
        y += 13
        display.text("Влажность: " + str(data.humidity) + " %  ", x, y)
        y += 13
        display.linear_bar(x, y+8, self.LINE_WIDTH, value=data.humidity, min_value=0, max_value=100, height=8, border=True, color=display.CYAN)
        y += 4
        y += 13
        display.text("Объем Зерна: " + str(data.volume) + " %  ", x, y)
        y += 13
        display.linear_bar(x, y+8, self.LINE_WIDTH, value=data.volume, min_value=0, max_value=100, height=8, border=True, color=display.YELLOW)
        

    def render_scales(self, data: ScalesData):
        x = self.scales_px
        y = self.scales_py
        display.text("Вес машины: " + str(data.weight) + " г  ", x, y)
        y += 13
        display.linear_bar(x, y+8, self.LINE_WIDTH, value=data.weight, min_value=0, max_value=300, height=8, border=True, color=display.RED)
        y += 15
        display.text("Последний груз:", x, y)
        y += 13
        if data.last_car_id:
            display.text("Маш.№" + str(data.last_car_id) + ": " + str(round(data.last_net_weight)) + " г  ", x, y)
        else:
            display.text("нет данных          ", x, y)

