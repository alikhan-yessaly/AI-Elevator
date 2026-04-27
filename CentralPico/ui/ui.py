from pibody import display
from ui.ElevatorIcon import ElevatorIcon
from ui.telemetry import TelemetryDisplayer
from TelemetryData import ElevatorData, ScalesData

from machine import Timer
class UI:
    def __init__(self):
        self.elevator_icon = ElevatorIcon(0, 40, 0)
        self.elevator_data = ElevatorData()
        self.scales_data = ScalesData()
        title = "Умное Хранилище"
        display.text(title, (240 - len(title) * 12) // 2, 5, fg=display.WHITE, font=display.font_large)
        self.td = TelemetryDisplayer(elevator_pivot=(100, 40), scales_pivot=(100, 140))
        self.update()
    
    def __call__(self):
        self.update()

    def update(self):
        volume = self.elevator_data.volume
        self.elevator_icon(volume)
        self.td.render_elevator(self.elevator_data)
        self.td.render_scales(self.scales_data)

    def _print_line(self, message, y, background=display.BLACK, text_color=display.WHITE):
        offset = 5
        max_chars = (240 - offset) // 8  # 28 chars per line
        line_height = 20

        words = message.split(" ")
        lines = []
        current_line = ""

        for word in words:
            # If adding word exceeds line
            if len(current_line) + len(word) + (1 if current_line else 0) > max_chars:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # word itself longer than line → hard split
                    lines.append(word[:max_chars])
                    current_line = word[max_chars:]
            else:
                if current_line:
                    current_line += " "
                current_line += word

        if current_line:
            lines.append(current_line)

        # Draw lines
        for i, line in enumerate(lines):
            y_offset = y + i * line_height
            display.fill_rect(0, y_offset, 240, line_height, background)
            display.text(line, offset, y_offset + 2, fg=text_color, bg=background)

    def status_message(self, message, error = False):
        print(message)

        background = display.WHITE if not error else display.RED
        text_color = display.BLACK if not error else display.WHITE

        self._print_line(message, 300, background, text_color)

    def state(self, wifi, ble):
        message = f"WiFi: {wifi}. BLE: {ble}."
        print(message)
        self._print_line(message, 190, text_color=display.WHITE)

    def heard(self, message):
        message = f"Я услышал: {message}"
        print(message)
        self._print_line(message, 210)

    def command(self, message):
        message = f"Отправляю команду: {message}"
        print(message)
        self._print_line(message, 250)

    def status_large(self, message):
        display.fill_rect(60, 225, 180, 32, display.BLACK)
        display.text(message, 60, 225, font=display.font_bold)

    def recording_LED(self):
        display.fill_circle(20, 240, 20, display.RED)
        self.status_large("Слушаю...")
    
    def clear_bottom(self):
        display.fill_rect(0, 210, 240, 90, display.BLACK)

# ui = UI()

# ui.elevator_data = ElevatorData(25, 50, 80)
# ui.scales_data = ScalesData(400, True)
# ui.update()