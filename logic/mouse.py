import queue
import threading
import win32con, win32api
from ctypes import windll, c_long, c_ulong, Structure, Union, c_int, POINTER, sizeof, CDLL
from os import path
from logic.keyboard import *
from logic.config_watcher import *
from run import cfg

if cfg.mouse_move_by_arduino or cfg.mouse_shoot_by_arduino:
    from logic.arduino import ArduinoMouse
    Arduino = ArduinoMouse()

if cfg.mouse_native == False:
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

class MouseThread(threading.Thread):
    def __init__(self):
        super(MouseThread, self).__init__()
        self.queue = queue.Queue(maxsize=1)
        self.daemon = True
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov = cfg.mouse_fov
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
        self.start()

    def run(self):
        while True:
            data = self.queue.get()
            if data is None:
                pass
            else:
                self.process_data(data)

    def process_data(self, data):
        shooting_key = self.get_shooting_key_state()
        x, y, target_x, target_y, target_w, target_h, distance = data
        bScope = self.check_target_in_scope(target_x, target_y, target_w, target_h) if cfg.mouse_auto_shoot or cfg.mouse_triggerbot else False
        x, y = self.adjust_mouse_movement(x, y, distance, target_x, target_y)
        self.move_mouse(x, y, shooting_key)
        self.shoot(bScope)

    def get_shooting_key_state(self):
        if cfg.mouse_lock_target:
            return win32api.GetKeyState(Keyboard.KeyCodes.get(cfg.hotkey_targeting))
        return win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(cfg.hotkey_targeting))

    def adjust_mouse_movement(self, x, y, distance, target_x, target_y):
        offset_x = target_x - self.center_x
        offset_y = target_y - self.center_y

        degrees_per_pixel_x = self.fov / self.screen_width

        mouse_move_x = offset_x * degrees_per_pixel_x

        mouse_dpi_move_x = (mouse_move_x / 360) * (self.dpi * (1 / self.mouse_sensitivity))

        mouse_move_y = offset_y * degrees_per_pixel_x
        mouse_dpi_move_y = (mouse_move_y / 360) * (self.dpi * (1 / self.mouse_sensitivity))
        
        return mouse_dpi_move_x, mouse_dpi_move_y
    
    def Update_settings(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov = cfg.mouse_fov
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        
    def check_target_in_scope(self, target_x, target_y, target_w, target_h):
        x = cfg.detection_window_width / 2
        y = cfg.detection_window_height / 2
        x1 = (target_x - target_w)
        x2 = (target_x + target_w)
        y1 = (target_y - target_h)
        y2 = (target_y + target_h)

        if (x > x1 and x < x2 and y > y1 and y < y2) :
            return True
        else :
            return False

    def move_mouse(self, x, y, shooting_key):
        if x == None or y == None:
            pass
        if shooting_key == -32768 or shooting_key == 1 and cfg.mouse_auto_aim == False and cfg.mouse_triggerbot == False or cfg.mouse_auto_aim:
            if cfg.mouse_native == True and x is not None and y is not None and cfg.mouse_move_by_arduino == False: # Native move
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

            if cfg.mouse_native == False and x is not None and y is not None and cfg.mouse_move_by_arduino == False: # ghub move
                ghub_mouse_xy(int(x), int(y))

            if cfg.mouse_move_by_arduino and x is not None and y is not None:
                Arduino.move(int(x), int(y))
    
    def shoot(self, bScope):
        # By GetAsyncKeyState
        if cfg.mouse_auto_shoot == True and cfg.mouse_triggerbot == False:
            if win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(cfg.hotkey_targeting)) == -32768 and bScope:
                if cfg.mouse_native and cfg.mouse_shoot_by_arduino == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                if cfg.mouse_native == False and cfg.mouse_shoot_by_arduino == False: #ghub
                    ghub_mouse_down()
                if cfg.mouse_shoot_by_arduino: # arduino
                    Arduino.press()

            if win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(cfg.hotkey_targeting)) == 0 or bScope == False:
                if cfg.mouse_native and cfg.mouse_shoot_by_arduino == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                if cfg.mouse_native == False and cfg.mouse_shoot_by_arduino == False: #ghub
                    ghub_mouse_up()
                if cfg.mouse_shoot_by_arduino: # arduino
                    Arduino.release()
            
        # By triggerbot
        if cfg.mouse_auto_shoot and cfg.mouse_triggerbot and bScope:
            if cfg.mouse_native and cfg.mouse_shoot_by_arduino == False: # native
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            if cfg.mouse_native == False and cfg.mouse_shoot_by_arduino == False: #ghub
                ghub_mouse_down()
            if cfg.mouse_shoot_by_arduino: # arduino
                Arduino.press()

        if cfg.mouse_auto_shoot and cfg.mouse_triggerbot and bScope == False:
            if cfg.mouse_native and cfg.mouse_shoot_by_arduino == False: # native
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if cfg.mouse_native == False and cfg.mouse_shoot_by_arduino == False: #ghub
                ghub_mouse_up()
            if cfg.mouse_shoot_by_arduino: # arduino
                Arduino.release()