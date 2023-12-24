import math
import queue
import threading
import time
from logic.screen import screen_x_center, screen_y_center, check_target_in_scope
import numpy as np
import win32con, win32api
from ctypes import windll, c_long, c_ulong, Structure, Union, c_int, POINTER, sizeof, CDLL
from os import path
from logic.keyboard import *
from logic.config_watcher import *
if mouse_move_by_arduino or mouse_shoot_by_arduino:
    from logic.arduino import ArduinoMouse
    Arduino = ArduinoMouse()

if mouse_native == False:
    basedir = path.dirname(path.abspath(__file__))
    dlldir = path.join(basedir, 'ghub_mouse.dll')
    dlldir2 = path.join(basedir, 'LogitechGkey.dll')
    LONG = c_long
    DWORD = c_ulong
    ULONG_PTR = POINTER(DWORD)
    gm = CDLL(dlldir)
    gmok = gm.mouse_open()

    class MOUSEINPUT(Structure):
        _fields_ = (('dx', LONG),
                    ('dy', LONG),
                    ('mouseData', DWORD),
                    ('dwFlags', DWORD),
                    ('time', DWORD),
                    ('dwExtraInfo', ULONG_PTR))


    class _INPUTunion(Union):
        _fields_ = (('mi', MOUSEINPUT), ('mi', MOUSEINPUT))


    class INPUT(Structure):
        _fields_ = (('type', DWORD),
                    ('union', _INPUTunion))

    def ghub_SendInput(*inputs):
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = c_int(sizeof(INPUT))
        return windll.user32.SendInput(nInputs, pInputs, cbSize)

    def ghub_Input(structure):
        return INPUT(0, _INPUTunion(mi=structure))

    def ghub_MouseInput(flags, x, y, data):
        return MOUSEINPUT(x, y, data, flags, 0, None)

    def ghub_Mouse(flags, x=0, y=0, data=0):
        return ghub_Input(ghub_MouseInput(flags, x, y, data))

    def ghub_mouse_xy(x, y):
        if gmok:
            return gm.moveR(x, y)
        return ghub_SendInput(ghub_Mouse(0x0001, x, y))

    def ghub_mouse_down(key = 1):
        if gmok:
            return gm.press(key)
        if key == 1:
            return ghub_SendInput(ghub_Mouse(0x0002))
        elif key == 2:
            return ghub_SendInput(ghub_Mouse(0x0008))

    def ghub_mouse_up(key = 1):
        if gmok:
            return gm.release()
        if key == 1:
            return ghub_SendInput(ghub_Mouse(0x0004))
        elif key == 2:
            return ghub_SendInput(ghub_Mouse(0x0010))

    def ghub_mouse_close():
        if gmok:
            return gm.mouse_close()

if mouse_wild_mouse:
    sqrt3 = np.sqrt(3)
    sqrt5 = np.sqrt(5)
def wind_mouse(start_x, start_y, dest_x, dest_y, G_0=9, W_0=3, M_0=15, D_0=12, move_mouse=lambda x,y: None):
    current_x,current_y = start_x,start_y
    v_x = v_y = W_x = W_y = 0
    try:
        while (dist:=np.hypot(dest_x - start_x, dest_y - start_y)) >= 1:
            W_mag = min(W_0, dist)
            if dist >= D_0:
                W_x = W_x/sqrt3 + (2*np.random.random()-1)*W_mag/sqrt5
                W_y = W_y/sqrt3 + (2*np.random.random()-1)*W_mag/sqrt5
            else:
                W_x /= sqrt3
                W_y /= sqrt3
                if M_0 < 3:
                    M_0 = np.random.random()*3 + 3
                else:
                    M_0 /= sqrt5
            v_x += W_x + G_0*(dest_x-start_x)/dist
            v_y += W_y + G_0*(dest_y-start_y)/dist
            v_mag = np.hypot(v_x, v_y)
            if v_mag > M_0:
                v_clip = M_0/2 + np.random.random()*M_0/2
                v_x = (v_x/v_mag) * v_clip
                v_y = (v_y/v_mag) * v_clip
            start_x += v_x
            start_y += v_y
            move_x = int(np.round(start_x))
            move_y = int(np.round(start_y))
            if current_x != move_x or current_y != move_y:
                move_mouse(current_x:=move_x,current_y:=move_y)
        return current_x,current_y
    except:
        return 0, 0

class MouseThread(threading.Thread):
    def __init__(self, frame_ready_event):
        super(MouseThread, self).__init__()
        self.queue = queue.Queue()
        self.daemon = True
        self.frame_ready_event = frame_ready_event
        self.start()

    def run(self):
        while True:
            data = self.queue.get()
            if data == None:
                self.frame_ready_event.set()
            else:
                shooting_key = win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(hotkey_targeting))
                (x, y, target_x, target_y, target_w, target_h, distance) = data

                slow_down_factor = min(distance, 4)

                x = x / slow_down_factor
                y = y / slow_down_factor
                
                if mouse_smoothing != 0 and x is not None and y is not None or mouse_smoothing != 0 and x is not None and y is not None:
                    x = x / mouse_smoothing
                    y = y / mouse_smoothing

                if shooting_key == -32768 and mouse_auto_aim == False:
                    if mouse_wild_mouse:
                        x, y = wind_mouse(screen_x_center, screen_y_center, x,y)

                    if mouse_native == True and x is not None and y is not None and mouse_move_by_arduino == False: # Native move
                        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

                    if mouse_native == False and x is not None and y is not None and mouse_move_by_arduino == False: # ghub move
                        ghub_mouse_xy(int(x), int(y))

                    if mouse_move_by_arduino and x is not None and y is not None:
                        Arduino.move(int(x), int(y))
                
                self.frame_ready_event.set()