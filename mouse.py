import win32con, win32api
from screen import check_target_in_scope
from options import mouse_auto_shoot, mouse_native
import asyncio
from ctypes import windll, c_long, c_ulong, Structure, Union, c_int, POINTER, sizeof, CDLL
from os import path

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

async def mouse_down(key = 1):
    if gmok:
        return gm.press(key)
    if key == 1:
        return SendInput(Mouse(0x0002))
    elif key == 2:
        return SendInput(Mouse(0x0008))
    await asyncio.sleep(0.01)
    mouse_up()

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

async def win32_raw_mouse_move(x=None, y=None, target_x=None, target_y=None, target_w=None, target_h=None):
    if mouse_native == True and x is not None and y is not None:
        await win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

    if mouse_native == False and x is not None and y is not None:
        mouse_xy(x, y)

    if target_x is not None and target_y is not None and mouse_auto_shoot == True:
        bScope = check_target_in_scope(target_x, target_y, target_w, target_h)
    if bScope == False:
        mouse_up()

    if mouse_auto_shoot and bScope and x is not None and y is not None:
        await win32_raw_mouse_click(x=x, y=y)
    else:
        mouse_up()

async def win32_raw_mouse_click(x, y):
    if mouse_native:
        await win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        await win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    else:
        await mouse_down(1)