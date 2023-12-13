from multiprocessing import Lock, Process
from threading import Thread
from logic.screen import check_target_in_scope, screen_x_center, screen_y_center
import numpy as np
import win32con, win32api
from ctypes import windll, c_long, c_ulong, Structure, Union, c_int, POINTER, sizeof, CDLL
from os import path
from logic.config_watcher import mouse_break_force, mouse_wild_mouse, mouse_native, mouse_auto_shoot, mouse_move_by_arduino, mouse_shoot_by_arduino, mouse_smoothing
from logic.pyduino_mk import constants
from logic.pyduino_mk import Arduino

if mouse_move_by_Arduino or mouse_shoot_by_Arduino:
    arduino = Arduino()

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

    def SendInput(*inputs):
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = c_int(sizeof(INPUT))
        return windll.user32.SendInput(nInputs, pInputs, cbSize)

    def Input(structure):
        return INPUT(0, _INPUTunion(mi=structure))

    def MouseInput(flags, x, y, data):
        return MOUSEINPUT(x, y, data, flags, 0, None)

    def Mouse(flags, x=0, y=0, data=0):
        return Input(MouseInput(flags, x, y, data))

    def mouse_xy(x, y):
        if gmok:
            return gm.moveR(x, y)
        return SendInput(Mouse(0x0001, x, y))

    def mouse_down(key = 1):
        if gmok:
            return gm.press(key)
        if key == 1:
            return SendInput(Mouse(0x0002))
        elif key == 2:
            return SendInput(Mouse(0x0008))

    def mouse_up(key = 1):
        if gmok:
            return gm.release()
        if key == 1:
            return SendInput(Mouse(0x0004))
        elif key == 2:
            return SendInput(Mouse(0x0010))

    def mouse_close():
        if gmok:
            return gm.mouse_close()

x0, y0, t0 = None, None, None

sqrt3 = np.sqrt(3)
sqrt5 = np.sqrt(5)

async def win32_raw_mouse_move(x=None, y=None, target_x=None, target_y=None, target_w=None, target_h=None, distance=None):
    bScope = False
    
    if mouse_smoothing >= 0.001 and x is not None and y is not None or mouse_smoothing <= -0.001 and x is not None and y is not None:
        x = x / mouse_smoothing
        y = y / mouse_smoothing

    if mouse_break_force >= 1:
        force = calculate_mouse_braking_force(distance=distance)
        st_x = x
        st_y = y
        if  x is not None and y is not None:
            if distance >= 81:
                x = (x / force) / 4
                y = (y / force) / 4
            if distance <= 80 and distance >= 20:
                x = x / force
                y = y / force
            if distance <= 19:
                x = st_x / 2
                y = st_y / 2

    if mouse_wild_mouse:
        x, y = wind_mouse(screen_x_center, screen_y_center, x,y)

    if mouse_native == True and x is not None and y is not None and mouse_move_by_arduino == False: # Native move
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

    if mouse_native == False and x is not None and y is not None and mouse_move_by_arduino == False: # ghub move
        mouse_xy(int(x), int(y))

    if target_x is not None and target_y is not None and mouse_auto_shoot == True:
        bScope = check_target_in_scope(target_x, target_y, target_w, target_h)

    if mouse_auto_shoot and x is not None and y is not None and mouse_shoot_by_arduino == False: # TODO
        if bScope:
            await win32_raw_mouse_click(x=int(x), y=int(y))
        else:
            mouse_up()

async def win32_raw_mouse_click(x, y):
    if mouse_native and mouse_shoot_by_arduino == False:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, int(x), int(y), 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, int(x), int(y), 0, 0)
    if mouse_native == False and mouse_shoot_by_arduino == False:
        mouse_down(1)

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

def calculate_mouse_braking_force(distance):
    if distance <= 0:
        pass
    return mouse_break_force / distance
