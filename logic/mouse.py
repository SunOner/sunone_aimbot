import queue
import threading
import time
import torch
import win32con, win32api
from ctypes import *
from os import path
import torch.nn as nn

from logic.buttons import Buttons
from logic.config_watcher import cfg
from logic.visual import visuals

if cfg.arduino_move or cfg.arduino_shoot:
    from logic.arduino import arduino

class GhubMouse:
    def __init__(self):
        self.basedir = path.dirname(path.abspath(__file__))
        self.dlldir = path.join(self.basedir, 'ghub_mouse.dll')
        self.gm = CDLL(self.dlldir)
        self.gmok = self.gm.mouse_open()

    @staticmethod
    def _ghub_SendInput(*inputs):
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = c_int(sizeof(INPUT))
        return windll.user32.SendInput(nInputs, pInputs, cbSize)

    @staticmethod
    def _ghub_Input(structure):
        return INPUT(0, _INPUTunion(mi=structure))

    @staticmethod
    def _ghub_MouseInput(flags, x, y, data):
        return MOUSEINPUT(x, y, data, flags, 0, None)

    @staticmethod
    def _ghub_Mouse(flags, x=0, y=0, data=0):
        return GhubMouse._ghub_Input(GhubMouse._ghub_MouseInput(flags, x, y, data))

    def mouse_xy(self, x, y):
        if self.gmok:
            return self.gm.moveR(x, y)
        return self._ghub_SendInput(self._ghub_Mouse(0x0001, x, y))

    def mouse_down(self, key=1):
        if self.gmok:
            return self.gm.press(key)
        if key == 1:
            return self._ghub_SendInput(self._ghub_Mouse(0x0002))
        elif key == 2:
            return self._ghub_SendInput(self._ghub_Mouse(0x0008))

    def mouse_up(self, key=1):
        if self.gmok:
            return self.gm.release()
        if key == 1:
            return self._ghub_SendInput(self._ghub_Mouse(0x0004))
        elif key == 2:
            return self._ghub_SendInput(self._ghub_Mouse(0x0010))

    def mouse_close(self):
        if self.gmok:
            return self.gm.mouse_close()

LONG = c_long
DWORD = c_ulong
ULONG_PTR = POINTER(DWORD)
            
class MOUSEINPUT(Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))

class _INPUTunion(Union):
    _fields_ = (('mi', MOUSEINPUT),)

class INPUT(Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))

class Mouse_net(nn.Module):
    def __init__(self, arch):
        super(Mouse_net, self).__init__()
        self.fc1 = nn.Linear(10, 128, arch)
        self.fc2 = nn.Linear(128, 128, arch)
        self.fc3 = nn.Linear(128, 64, arch)
        self.fc4 = nn.Linear(64, 2, arch)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x

class MouseThread():
    def __init__(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov_x = cfg.mouse_fov_width
        self.fov_y = cfg.mouse_fov_height
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
        self.prev_x = 0
        self.prev_y = 0
        
        self.bScope = False
        self.button_pressed = False
        
        self.arch = f'cuda:{cfg.AI_device}'
        
        if cfg.AI_enable_AMD:
            self.arch = f'hip:{cfg.AI_device}'
        if 'cpu' in cfg.AI_device:
            self.arch = 'cpu'
        
        if cfg.mouse_ghub:
            self.ghub = GhubMouse()
            
        if cfg.AI_mouse_net:
            self.device = torch.device(f'{self.arch}')
            self.model = Mouse_net(arch=self.arch).to(self.device)
            try:
                self.model.load_state_dict(torch.load('mouse_net.pth', map_location=self.device))
            except Exception as e:
                print(e)
                print('Please train mouse_net model, or download trained mouse_net.pth model from repository and place in base folder. Instruction here: https://github.com/SunOner/mouse_net')
                exit()
            self.model.eval()

    def process_data(self, data):
        target_x, target_y, target_w, target_h = data
        # target_distance = math.sqrt((target_x - self.center_x)**2 + (target_y - self.center_y)**2) # TODO
        self.bScope = self.check_target_in_scope(target_x, target_y, target_w, target_h) if cfg.auto_shoot or cfg.triggerbot else False
        self.bScope = True if cfg.force_click else self.bScope
        x, y = self.predict_target_position(target_x, target_y)
        x, y = self.calc_movement(x, y)
        self.move_mouse(x, y)
        self.shoot(self.bScope)

    def get_shooting_key_state(self):
        for key_name in cfg.hotkey_targeting_list:
            key_code = Buttons.KEY_CODES.get(key_name.strip())
            if key_code is not None:
                if cfg.mouse_lock_target:
                    state = win32api.GetKeyState(key_code)
                else:
                    state = win32api.GetAsyncKeyState(key_code)
                if state < 0 or state == 1:
                    return True
        return False

    def predict_target_position(self, target_x, target_y):
        velocity_x = target_x - self.prev_x
        velocity_y = target_y - self.prev_y
        
        predicted_x = target_x + velocity_x
        predicted_y = target_y + velocity_y

        self.prev_x = target_x
        self.prev_y = target_y

        return predicted_x, predicted_y
    
    def calc_movement(self, target_x, target_y):
        if cfg.AI_mouse_net == False:
            offset_x = target_x - self.center_x
            offset_y = target_y - self.center_y

            degrees_per_pixel_x = self.fov_x / self.screen_width
            degrees_per_pixel_y = self.fov_y / self.screen_height
            
            mouse_move_x = offset_x * degrees_per_pixel_x

            move_x = (mouse_move_x / 360) * (self.dpi * (1 / self.mouse_sensitivity))

            mouse_move_y = offset_y * degrees_per_pixel_y
            move_y = (mouse_move_y / 360) * (self.dpi * (1 / self.mouse_sensitivity))
            
            if cfg.show_window and cfg.show_target_prediction_line:
                visuals.draw_predicted_position(target_x, target_y)
                
            return move_x, move_y
        else:
            input_data = [self.screen_width,
                        self.screen_height,
                        self.center_x,
                        self.center_y,
                        self.dpi,
                        self.mouse_sensitivity,
                        self.fov_x,
                        self.fov_y,
                        target_x,
                        target_y]
            
            input_tensor = torch.tensor(input_data, dtype=torch.float32).to(self.device)
        
            with torch.no_grad():
                move = self.model(input_tensor).cpu().numpy()
            
            return move[0], move[1]
        
    def move_mouse(self, x, y):
        if x == None or y == None:
            pass
        if self.get_shooting_key_state() and cfg.mouse_auto_aim == False and cfg.triggerbot == False or cfg.mouse_auto_aim:
            if cfg.mouse_ghub == False and x is not None and y is not None and cfg.arduino_move == False: # Native move
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
                
            if cfg.mouse_ghub and x is not None and y is not None and cfg.arduino_move == False: # ghub move
                self.ghub.mouse_xy(int(x), int(y))

            if cfg.arduino_move and x is not None and y is not None: # Arduino     
                arduino.move(int(x), int(y))

    def shoot(self, bScope):
        # By GetAsyncKeyState
        if cfg.auto_shoot == True and cfg.triggerbot == False:
            if self.get_shooting_key_state() and bScope or cfg.mouse_auto_aim and bScope:
                if  self.button_pressed == False:
                    if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        self.button_pressed = True
                        
                    if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                        self.ghub.mouse_down()
                        self.button_pressed = True
                        
                    if cfg.arduino_shoot: # arduino
                        arduino.press()
                        self.button_pressed = True

            if self.get_shooting_key_state() == False and self.button_pressed == True or bScope == False and self.button_pressed == True:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    self.button_pressed = False
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_up()
                    self.button_pressed = False
                    
                if cfg.arduino_shoot: # arduino
                    arduino.release()
                    self.button_pressed = False
        
        # By triggerbot
        if cfg.auto_shoot and cfg.triggerbot and bScope or cfg.mouse_auto_aim and bScope:
            if self.button_pressed == False:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    self.button_pressed = True
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_down()
                    self.button_pressed = True
                    
                if cfg.arduino_shoot: # arduino
                    arduino.press()
                    self.button_pressed = True

        if cfg.auto_shoot and cfg.triggerbot and bScope == False:
            if self.button_pressed == True:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    self.button_pressed = False
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_up()
                    self.button_pressed = False
                    
                if cfg.arduino_shoot: # arduino
                    arduino.release() 
                    self.button_pressed = False
                
    def check_target_in_scope(self, target_x, target_y, target_w, target_h):
        x1 = (target_x - target_w)
        x2 = (target_x + target_w)
        y1 = (target_y - target_h)
        y2 = (target_y + target_h)

        if (self.center_x > x1 and self.center_x < x2 and self.center_y > y1 and self.center_y < y2) :
            return True
        else:
            return False

    def Update_settings(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov_x = cfg.mouse_fov_width
        self.fov_y = cfg.mouse_fov_height
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
                
mouse = MouseThread()