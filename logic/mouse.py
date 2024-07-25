import torch
import win32con, win32api
import torch.nn as nn
import time
import numpy as np
from scipy.signal import butter, lfilter
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
        
class MouseThread:
    def __init__(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov_x = cfg.mouse_fov_width
        self.fov_y = cfg.mouse_fov_height
        self.disable_prediction = cfg.disable_prediction
        self.prediction_interval = cfg.prediction_interval
        self.bScope_multiplier = cfg.bScope_multiplier
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
        self.mouse_clamp_movement = cfg.mouse_clamp_movement
        self.mouse_max_movement_x = cfg.mouse_max_movement_x
        self.mouse_max_movement_y = cfg.mouse_max_movement_y
        self.mouse_on_target_slow_x = cfg.mouse_on_target_slow_x
        self.mouse_on_target_slow_y = cfg.mouse_on_target_slow_y
        self.filter_order = 3
        self.filter_cutoff = 0.999
        self.filter_b, self.filter_a = butter(self.filter_order, self.filter_cutoff, btype='low', analog=False)
        self.prev_x = 0
        self.prev_y = 0
        self.prev_time = None
        
        self.bScope = False
        
        self.arch = self.get_arch()
        
        if cfg.mouse_ghub:
            from logic.ghub import gHub
            self.ghub = gHub
            
        if cfg.AI_mouse_net:
            self.device = torch.device(self.arch)
            self.model = Mouse_net(arch=self.arch).to(self.device)
            try:
                self.model.load_state_dict(torch.load('mouse_net.pth', map_location=self.device))
            except Exception as e:
                print(e)
                print('Please train mouse_net model, or download latest trained mouse_net.pth model from repository and place in base folder. Instruction here: https://github.com/SunOner/mouse_net')
                exit()
            self.model.eval()

    def get_arch(self):
        if cfg.AI_enable_AMD:
            return f'hip:{cfg.AI_device}'
        if 'cpu' in cfg.AI_device:
            return 'cpu'
        return f'cuda:{cfg.AI_device}'

    def process_data(self, data):
        target_x, target_y, target_w, target_h, target_cls = data
        # draw simple line
        if cfg.AI_mouse_net == False:
            if (cfg.show_window and cfg.show_target_line) or (cfg.show_overlay and cfg.show_target_line):
                visuals.draw_target_line(target_x, target_y, target_cls)
        
        # bScope
        self.bScope = self.check_target_in_scope(target_x, target_y, target_w, target_h, self.bScope_multiplier) if cfg.auto_shoot or cfg.triggerbot else False
        self.bScope = cfg.force_click or self.bScope

        # prediction
        if not self.disable_prediction:
            current_time = time.time()
            target_x, target_y = self.predict_target_position(target_x, target_y, current_time)
            if cfg.AI_mouse_net == False:
                if (cfg.show_window and cfg.show_target_prediction_line) or (cfg.show_overlay and cfg.show_target_prediction_line):
                    visuals.draw_predicted_position(target_x, target_y, target_cls)

        target_x, target_y = self.calc_movement(target_x, target_y, target_cls)

        # history points
        if (cfg.show_window and cfg.show_history_points) or (cfg.show_overlay and cfg.show_history_points):
            visuals.draw_history_point_add_point(target_x, target_y)
        
        shooting.queue.put((self.bScope, self.get_shooting_key_state()))

        self.move_mouse(target_x, target_y)

    def predict_target_position(self, target_x, target_y, current_time):
        # Initialize filter if it's the first frame
        if self.prev_time is None:
            self.prev_x = target_x
            self.prev_y = target_y
            self.prev_velocity_x = 0
            self.prev_velocity_y = 0
            self.filtered_x = [target_x]
            self.filtered_y = [target_y]
            self.prev_time = current_time
            return target_x, target_y
        #delta_time = current_time - self.prev_time
        # velocity_x = (target_x - self.prev_x) / delta_time
        # velocity_y = (target_y - self.prev_y) / delta_time
        
        # acceleration_x = (velocity_x - self.prev_velocity_x) / delta_time
        # acceleration_y = (velocity_y - self.prev_velocity_y) / delta_time

        # prediction_interval = delta_time * self.prediction_interval

        # predicted_x = target_x + velocity_x * prediction_interval + 0.5 * acceleration_x * (prediction_interval ** 2)
        # predicted_y = target_y + velocity_y * prediction_interval + 0.5 * acceleration_y * (prediction_interval ** 2)

        # self.prev_x = target_x
        # self.prev_y = target_y
        # self.prev_velocity_x = velocity_x
        # self.prev_velocity_y = velocity_y
        # target_x = predicted_x
        # target_y = predicted_y


        # Apply IIR filter
        self.filtered_x.append(target_x)
        self.filtered_y.append(target_y)
        filtered_x = lfilter(self.filter_b, self.filter_a, self.filtered_x)[-1]
        filtered_y = lfilter(self.filter_b, self.filter_a, self.filtered_y)[-1]

        # Keep buffer size under control
        self.filtered_x = self.filtered_x[-self.filter_order:]
        self.filtered_y = self.filtered_y[-self.filter_order:]

        self.prev_time = current_time
        return filtered_x, filtered_y
    
    def calc_movement(self, target_x, target_y, target_cls):
        if not cfg.AI_mouse_net:
            # Calculate distance from screen center (normalized to [0, 1])
            #distance_x = abs(target_x - self.center_x) / (self.screen_width / 2)
            #distance_y = abs(target_y - self.center_y) / (self.screen_height / 2)

            # Clamping factors (decrease by 20% per 20% of screen width/height)
            #clamp_x = max(0.2, 1 - distance_x) 
            #clamp_y = max(0.2, 1 - distance_y) 
 
            offset_x = target_x - self.center_x
            offset_y = target_y - self.center_y

            degrees_per_pixel_x = self.fov_x / self.screen_width
            degrees_per_pixel_y = self.fov_y / self.screen_height

            mouse_move_x = offset_x * degrees_per_pixel_x
            move_x = (mouse_move_x / 360) * (self.dpi * (1 / self.mouse_sensitivity))

            mouse_move_y = offset_y * degrees_per_pixel_y
            move_y = (mouse_move_y / 360) * (self.dpi * (1 / self.mouse_sensitivity))
            distance_from_center = np.sqrt((target_x - self.center_x)**2 + (target_y - self.center_y)**2)
            slowdown_radius = 0.2 * min(self.screen_width, self.screen_height) / 2  # 20% of the smaller dimension

            if distance_from_center < slowdown_radius:
            # Apply a scaling factor to the movement when within the slowdown zone
                move_x *= self.mouse_on_target_slow_x  # Adjust the scaling factor as needed
                move_y *= self.mouse_on_target_slow_y  # Adjust the scaling factor as needed
            else:
                move_x = move_x
                move_y = move_y
            # Apply clamping for smooth transition between max and min
            #max_clamp = 2.0  # Maximum clamping at the edge
            #min_clamp = 0.1  # Minimum clamping at the center
            #clamp_range = max_clamp - min_clamp

            #clamped_move_x = clamp_x * move_x * clamp_range + min_clamp * move_x
            #clamped_move_y = clamp_y * move_y * clamp_range + min_clamp * move_y
                        # Additional clamping to maximum movement
            #clamped_move_x = max(-self.max_movement_x, min(clamped_move_x, self.max_movement_x))
            #clamped_move_y = max(-self.max_movement_y, min(clamped_move_y, self.max_movement_y))
            #clamp movement
            if self.mouse_clamp_movement == True:
                move_x = max(-cfg.mouse_max_movement_x, min(move_x, cfg.mouse_max_movement_x))  
                move_y = max(-cfg.mouse_max_movement_y, min(move_y, cfg.mouse_max_movement_y))
            else:
                move_x = move_x
                move_y = move_y

            return move_x, move_y
        else:
            input_data = [
                self.screen_width,
                self.screen_height,
                self.center_x,
                self.center_y,
                self.dpi,
                self.mouse_sensitivity,
                self.fov_x,
                self.fov_y,
                target_x,
                target_y
            ]
            
            input_tensor = torch.tensor(input_data, dtype=torch.float32).to(self.device)
            with torch.no_grad():
                move = self.model(input_tensor).cpu().numpy()
                
            if (cfg.show_window and cfg.show_target_prediction_line) or (cfg.show_overlay and cfg.show_target_prediction_line):
                    visuals.draw_predicted_position(move[0] + self.center_x, move[1] + self.center_y, target_cls)
                    
            return move[0], move[1]
        
    def move_mouse(self, x, y):
        if x is None:
            x = 0
        if y is None:
            y = 0
        
        if x != 0 and y != 0:
            if (self.get_shooting_key_state() and not cfg.mouse_auto_aim and not cfg.triggerbot) or cfg.mouse_auto_aim:
                if not cfg.mouse_ghub and x is not None and y is not None and not cfg.arduino_move:  # Native move
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
                    
                if cfg.mouse_ghub and x is not None and y is not None and not cfg.arduino_move:  # ghub move
                    self.ghub.mouse_xy(int(x), int(y))

                if cfg.arduino_move and x is not None and y is not None:  # Arduino     
                    arduino.move(int(x), int(y))
    
    def get_shooting_key_state(self):
        for key_name in cfg.hotkey_targeting_list:
            key_code = Buttons.KEY_CODES.get(key_name.strip())
            if key_code is not None:
                state = win32api.GetKeyState(key_code) if cfg.mouse_lock_target else win32api.GetAsyncKeyState(key_code)
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

        bScope = self.center_x > x1 and self.center_x < x2 and self.center_y > y1 and self.center_y < y2
            
        if cfg.show_window and cfg.show_bScope_box:
            visuals.draw_bScope(x1, x2, y1, y2, bScope)
        
        return bScope

    def update_settings(self):
        self.dpi = cfg.mouse_dpi
        self.mouse_sensitivity = cfg.mouse_sensitivity
        self.fov_x = cfg.mouse_fov_width
        self.fov_y = cfg.mouse_fov_height
        self.disable_prediction = cfg.disable_prediction
        self.prediction_interval = cfg.prediction_interval
        self.bScope_multiplier = cfg.bScope_multiplier
        self.screen_width = cfg.detection_window_width
        self.screen_height = cfg.detection_window_height
        self.center_x = self.screen_width / 2
        self.center_y = self.screen_height / 2
                
mouse = MouseThread()