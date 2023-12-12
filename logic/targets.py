import math
from logic.config_watcher import mouse_smoothing, body_y_offset
from run import screen_x_center, screen_y_center

class Targets:
    def __init__(self, x, y, w, h, cls):
        self.mouse_x = (x - screen_x_center)
        if cls == 7:
            self.mouse_y = (y - screen_y_center)
        else:
            self.mouse_y = (y - screen_y_center - body_y_offset * h)
        self.distance = math.sqrt((x - screen_x_center)**2 + (y - screen_y_center)**2)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cls = cls