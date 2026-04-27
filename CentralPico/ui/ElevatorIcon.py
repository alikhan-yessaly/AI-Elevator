from pibody import display


silhouette = [
    (0, 21), (0, 102), (4, 102), (4, 106), (8, 106), (8, 110), (13, 110), (13, 119),
    (8, 119), (8, 127), (4, 127), (4, 140), (8, 140), (8, 136), (13, 136), (13, 123),
    (17, 123), (17, 119), (21, 119), (21, 123), (25, 123), (25, 127), (30, 127), (30, 140),
    (38, 140), (38, 132), (51, 132), (51, 140), (59, 140), (59, 127), (64, 127), (64, 123),
    (68, 123), (68, 119), (72, 119), (72, 123), (76, 123), (76, 136), (81, 136), (81, 140),
    (85, 140), (85, 127), (81, 127), (81, 119), (76, 119), (76, 110), (81, 110), (81, 106),
    (85, 106), (85, 102), (89, 102), (89, 21), (85, 21), (85, 17), (76, 17), (76, 13),
    (68, 13), (68, 8), (59, 8), (59, 4), (51, 4), (51, 0), (38, 0), (38, 4),
    (30, 4), (30, 8), (21, 8), (21, 13), (13, 13), (13, 17), (4, 17), (4, 21)
]

inside = [
    (81, 76), (81, 34), (8, 34), (8, 98), (13, 98), (13, 102), (17, 102), (17, 106),
    (21, 106), (21, 110), (25, 110), (25, 115), (30, 115), (30, 119), (34, 119), (34, 123),
    (38, 123), (38, 127), (51, 127), (51, 123), (55, 123), (55, 119), (59, 119), (59, 115),
    (64, 115), (64, 110), (68, 110), (68, 106), (72, 106), (72, 102), (76, 102), (76, 98),
    (81, 98)
]

cap = [
    (64, 17), (59, 17), (59, 13), (51, 13), (51, 8), (38, 8), (38, 13), (30, 13),
    (30, 17), (21, 17), (21, 21), (13, 21), (13, 30), (76, 30), (76, 21), (68, 21),
    (68, 17)
]

def find_xy(x, y):
    display.hline(x-4, y, 2, display.RED)
    display.hline(x+3, y, 2, display.RED)
    display.vline(x, y-4, 2, display.RED)
    display.vline(x, y+3, 2, display.RED)
    display.pixel(x, y, display.RED)


_CAP_GREY = display.color(100, 100, 100)


class ElevatorIcon():
    def __init__(self, pivot_x=0, pivot_y=0, level=0) -> None:
        self.pivot_x        = pivot_x
        self.pivot_y        = pivot_y
        self._last_level    = 0
        self._last_cap_color = _CAP_GREY

        self.draw_elevator()
        self.fill_elevator(level)

    def __call__(self, level, cooling=False, heating=False):
        self.fill_elevator(level)
        self._update_cap(cooling, heating)

    def _cap_color(self, cooling, heating):
        if cooling:
            return display.BLUE
        if heating:
            return display.RED
        return _CAP_GREY

    def _update_cap(self, cooling, heating):
        color = self._cap_color(cooling, heating)
        if color != self._last_cap_color:
            self._last_cap_color = color
            display.fill_polygon(cap, self.pivot_x, self.pivot_y, color)

    def draw_elevator(self):
        display.fill_polygon(silhouette, self.pivot_x, self.pivot_y, display.WHITE)
        display.fill_polygon(cap,        self.pivot_x, self.pivot_y, _CAP_GREY)
        display.fill_polygon(inside,     self.pivot_x, self.pivot_y, display.BLACK)




    def _draw_segment(self, i, color):
        if i < 7:
            display.fill_rect(
                (37 - i*4) + self.pivot_x,
                (123 - i * 4) + self.pivot_y,
                16 + i * 8,
                4,
                color
            )
        else:
            display.fill_rect(
                8 + self.pivot_x,
                (123 - i * 4) + self.pivot_y,
                74,
                4,
                color
            )


    def fill_elevator(self, level):
        level = round(level * 23 / 100)

        if level == self._last_level:
            return

        if level > self._last_level:
            # draw only new parts
            for i in range(self._last_level, level):
                self._draw_segment(i, display.color(255, i * 10, 50))

        else:
            # erase only removed parts
            for i in range(level, self._last_level):
                self._draw_segment(i, display.BLACK)

        self._last_level = level

