import math
from options import *
from main import screen_x_center, screen_y_center

class Targets:
    def __init__(self, x, y, w, h, cls):
        self.mouse_x = (x - screen_x_center) / mouse_smoothing
        if cls == 7:
            self.mouse_y = (y - screen_y_center) / mouse_smoothing
        else:
            self.mouse_y = (y - screen_y_center - body_y_offset * h) / mouse_smoothing
        self.distance = math.sqrt((x - screen_x_center)**2 + (y - screen_y_center)**2)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cls = cls