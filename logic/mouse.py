import torch
import win32con, win32api
import torch.nn as nn
import time

from logic.config_watcher import cfg
from logic.visual import visuals
from logic.shooting import shooting
from logic.buttons import Buttons

if cfg.arduino_move or cfg.arduino_shoot:
    from logic.arduino import arduino

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
        self.disable_prediction = cfg.disable_prediction
        self.bScope_multiplier = cfg.bScope_multiplier
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2

        self.prev_x = 0
        self.prev_y = 0
        self.prev_time = None
        
        self.bScope = False
        
        self.arch = f'cuda:{cfg.AI_device}'
        
        if cfg.AI_enable_AMD:
            self.arch = f'hip:{cfg.AI_device}'
        if 'cpu' in cfg.AI_device:
            self.arch = 'cpu'
        
        if cfg.mouse_ghub:
            from logic.ghub import gHub
            self.ghub = gHub
            
        if cfg.AI_mouse_net:
            self.device = torch.device(f'{self.arch}')
            self.model = Mouse_net(arch=self.arch).to(self.device)
            try:
                self.model.load_state_dict(torch.load('mouse_net.pth', map_location=self.device))
            except Exception as e:
                print(e)
                print('Please train mouse_net model, or download latest trained mouse_net.pth model from repository and place in base folder. Instruction here: https://github.com/SunOner/mouse_net')
                exit()
            self.model.eval()

    def process_data(self, data):
        target_x, target_y, target_w, target_h = data
        
        # draw simple line
        if cfg.show_window and cfg.show_target_line or cfg.show_overlay and cfg.show_target_line:
            visuals.draw_target_line(target_x, target_y)
        
        # bScope
        self.bScope = self.check_target_in_scope(target_x, target_y, target_w, target_h, self.bScope_multiplier) if cfg.auto_shoot or cfg.triggerbot else False
        self.bScope = True if cfg.force_click else self.bScope

        # prediction
        if not self.disable_prediction:
            current_time = time.time()
            target_x, target_y = self.predict_target_position(target_x, target_y, current_time)
            
            if cfg.show_window and cfg.show_target_prediction_line or cfg.show_overlay and cfg.show_target_prediction_line:
                visuals.draw_predicted_position(target_x, target_y)

        target_x, target_y = self.calc_movement(target_x, target_y)

        # history points
        if cfg.show_window and cfg.show_history_points or cfg.show_overlay and cfg.show_history_points:
            visuals.draw_history_point_add_point(target_x, target_y)
        
        shooting.queue.put((self.bScope, self.get_shooting_key_state()))

        self.move_mouse(target_x, target_y)

    def predict_target_position(self, target_x, target_y, current_time):
        if self.prev_time is None:
            self.prev_time = current_time
            self.prev_x = target_x
            self.prev_y = target_y
            return target_x, target_y

        delta_time = current_time - self.prev_time

        velocity_x = (target_x - self.prev_x) / delta_time
        velocity_y = (target_y - self.prev_y) / delta_time

        predicted_x = target_x + velocity_x * delta_time
        predicted_y = target_y + velocity_y * delta_time

        self.prev_x = target_x
        self.prev_y = target_y
        self.prev_time = current_time

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
        if x == None:
            x = 0
        if y == None:
            y = 0
            
        if self.get_shooting_key_state() and cfg.mouse_auto_aim == False and cfg.triggerbot == False or cfg.mouse_auto_aim:
            if cfg.mouse_ghub == False and x is not None and y is not None and cfg.arduino_move == False: # Native move
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
                
            if cfg.mouse_ghub and x is not None and y is not None and cfg.arduino_move == False: # ghub move
                self.ghub.mouse_xy(int(x), int(y))

            if cfg.arduino_move and x is not None and y is not None: # Arduino     
                arduino.move(int(x), int(y))
    
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
      
    def check_target_in_scope(self, target_x, target_y, target_w, target_h, reduction_factor):
        reduced_w = target_w * reduction_factor / 2
        reduced_h = target_h * reduction_factor / 2

        x1 = target_x - reduced_w
        x2 = target_x + reduced_w
        y1 = target_y - reduced_h
        y2 = target_y + reduced_h

        bScope = None
        if (self.center_x > x1 and self.center_x < x2 and self.center_y > y1 and self.center_y < y2):
            bScope = True
        else:
            bScope = False
            
        if cfg.show_window and cfg.show_bScope_box:
            visuals.draw_bScope(x1, x2, y1, y2, bScope)
        
        return bScope

    def Update_settings(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov_x = cfg.mouse_fov_width
        self.fov_y = cfg.mouse_fov_height
        self.disable_prediction = cfg.disable_prediction
        self.bScope_multiplier = cfg.bScope_multiplier
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
                
mouse = MouseThread()