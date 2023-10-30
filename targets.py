import math
from options import *
from main import screen_x_center, screen_y_center
class Player:
    def __init__(self, x, y, w, h, xyxy):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.xyxy = xyxy
        self.distance = float(math.sqrt((self.x - screen_x_center)**2 + (self.y - screen_y_center)**2))

        
class Head:
    def __init__(self, x, y, w, h, xyxy):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.xyxy = xyxy
        self.distance = float(math.sqrt((self.x - screen_x_center)**2 + (self.y - screen_y_center)**2))