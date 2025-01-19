import torch
import win32con, win32api
import torch.nn as nn
import time
import math
import os
from logic.config_watcher import cfg
from logic.visual import visuals
from logic.shooting import shooting
from logic.buttons import Buttons
import numpy as np
from scipy.optimize import minimize
from scipy.integrate import ode

if cfg.mouse_rzr:
    from logic.rzctl import RZCONTROL

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
        self.prev_x = 0
        self.prev_y = 0
        self.prev_time = None
        self.max_distance = math.sqrt(self.screen_width**2 + self.screen_height**2) / 2
        self.min_speed_multiplier = cfg.mouse_min_speed_multiplier
        self.max_speed_multiplier = cfg.mouse_max_speed_multiplier
        self.prev_distance = None
        self.speed_correction_factor = 0.1  # How much previous speed affects current speed
        self.bScope = False
        self.arch = self.get_arch()
        self.v = 10  # Example initial speed
        self.a = 0.5   # Example initial acceleration
        self.end_time = 10  # Example initial end time
        self.threshold = 1 # Overshoot threshold in pixels
        self.v_min = 5  # Minimum speed
        self.end_time_min = 1  # Minimum end time
        self.overshoot_factor = 0.5  # Factor for velocity reduction
        self.end_time_adjust_threshold = 5  # Threshold for adjusting end_time
        self.buffer_distance = 0.5  # Distance within which to consider overshoot
        self.section_size_x = self.screen_width / 100
        self.section_size_y = self.screen_height / 100
        
        if cfg.mouse_ghub:
            from logic.ghub import gHub
            self.ghub = gHub

        if cfg.mouse_rzr:
            dll_name = "rzctl.dll" 
            script_directory = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_directory, dll_name)
            self.rzr = RZCONTROL(dll_path)
            if not self.rzr.init():
                print("Failed to initialize rzctl")

            
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
    def target_dynamics(self, t, state, a):
        """
        Defines the dynamics of the target: acceleration only in x-direction.
        state = [x, y, vx, vy]
        """
        x, y, vx, vy = state
        return [vx, vy, a, 0]  # acceleration only in x-direction

    def interceptor_dynamics(self, t, state, v, theta):
        """
        Defines the dynamics of the interceptor: constant speed, direction by theta.
        state = [x, y]
        """
        x, y = state
        return [v * np.cos(theta), v * np.sin(theta)]
    
    def predict_target_position(self, target_x, target_y, current_time):
        if self.prev_time is None:
            self.prev_time = current_time
            self.prev_x = target_x
            self.prev_y = target_y
            self.prev_velocity_x = 0
            self.prev_velocity_y = 0
            return target_x, target_y

        delta_time = current_time - self.prev_time
        target_init = [self.prev_x, self.prev_y, (target_x - self.prev_x) / delta_time, (target_y - self.prev_y) / delta_time]
        
        optimal_angle, _ = self.find_optimal_intercept(self.v, target_init, self.a, self.end_time)
        
        predicted_x = self.prev_x + self.v * np.cos(optimal_angle) * self.end_time
        predicted_y = self.prev_y + self.v * np.sin(optimal_angle) * self.end_time

        # Check for overshoot and adjust parameters
        actual_x, actual_y = target_x, target_y
        self.update_parameters(actual_x, actual_y, predicted_x, predicted_y)

        predicted_x, predicted_y = self.buffer_zone(target_x, target_y, predicted_x, predicted_y)

        self.prev_x, self.prev_y = target_x, target_y
        self.prev_time = current_time

        return predicted_x, predicted_y

    def update_parameters(self, actual_x, actual_y, predicted_x, predicted_y):
        overshoot_x = abs(predicted_x - actual_x)
        overshoot_y = abs(predicted_y - actual_y)
        if overshoot_x > self.threshold or overshoot_y > self.threshold:
            self.scale_velocity(max(overshoot_x, overshoot_y) / self.threshold)
            self.adjust_end_time(max(overshoot_x, overshoot_y))

    def scale_velocity(self, overshoot):
        self.v = max(self.v_min, self.v * (1 - overshoot * self.overshoot_factor))

    def adjust_end_time(self, overshoot):
        if overshoot > self.end_time_adjust_threshold:
            self.end_time = max(self.end_time_min, self.end_time * 0.95)  # Reduce end_time by 5%

    def buffer_zone(self, target_x, target_y, predicted_x, predicted_y):
        buffer = self.buffer_distance  # Define based on target speed or size
        if abs(predicted_x - target_x) < buffer or abs(predicted_y - target_y) < buffer:
            # Adjust aim to be slightly behind predicted position
            return (predicted_x - buffer * np.sign(predicted_x - target_x), 
                    predicted_y - buffer * np.sign(predicted_y - target_y))
        return predicted_x, predicted_y

    def continuous_monitor(self, current_x, current_y, target_x, target_y):
        distance = np.linalg.norm(np.array([current_x, current_y]) - np.array([target_x, target_y]))
        if distance > self.buffer_distance and self.is_past_target(current_x, target_x):
            self.emergency_slowdown()

    def is_past_target(self, current_x, target_x):
        # Simple check if moving past target in x-direction; extend for y if needed
        return (current_x > target_x) if (self.prev_x < target_x) else (current_x < target_x)

    def emergency_slowdown(self):
        self.v = self.v_min  # Reduce speed to minimum

    def find_optimal_intercept(self, v, target_init, a, end_time):
        """
        Find the optimal angle for interception using the new logic.
        """
        initial_guess = [np.pi/4]  # Start with 45 degrees as initial guess
        result = minimize(self.cost_function, initial_guess, args=(v, target_init, a, end_time), 
                          method='L-BFGS-B', bounds=[(0, np.pi)])
        return result.x[0], result.fun

    def cost_function(self, params, v, target_init, a, end_time):
        """
        Cost function to minimize. Here we minimize the distance at t = end_time.
        params = [angle in radians]
        """
        theta = params[0]
        target_dynamics = self.target_dynamics
        # Solve target's trajectory
        target = ode(target_dynamics).set_integrator('vode', method='adams')
        target.set_initial_value(target_init, 0).set_f_params(a)
        target_states = [target_init]
        
        dt = 0.01  # time step for integration
        while target.successful() and target.t < end_time:
            target.integrate(target.t + dt)
            target_states.append([target.y[0], target.y[1]])
        interceptor_dynamics = self.interceptor_dynamics
        # Solve interceptor's trajectory
        interceptor = ode(interceptor_dynamics).set_integrator('vode', method='adams')
        interceptor.set_initial_value([0, 0], 0).set_f_params(v, theta)
        interceptor_states = [[0, 0]]
        
        while interceptor.successful() and interceptor.t < end_time:
            interceptor.integrate(interceptor.t + dt)
            interceptor_states.append([interceptor.y[0], interceptor.y[1]])
        
        # Calculate the distance at the end time
        target_pos = target_states[-1][:2]  # x, y of target at end time
        interceptor_pos = interceptor_states[-1]  # x, y of interceptor at end time
        distance = np.linalg.norm(np.array(target_pos) - np.array(interceptor_pos))
        
        return distance


    def calculate_speed_multiplier(self, target_x, target_y, distance):
        # Previous speed multiplier calculation
        normalized_distance = min(distance / self.max_distance, 1)
        base_speed = self.min_speed_multiplier + (self.max_speed_multiplier - self.min_speed_multiplier) * (1 - normalized_distance)

        
        # Calculate the section the target is in
        target_x_section = int((target_x - self.center_x + self.screen_width / 2) / self.section_size_x)
        target_y_section = int((target_y - self.center_y + self.screen_height / 2) / self.section_size_y)
        
        # Calculate the distance from the center in terms of sections
        distance_from_center_x = abs(50 - target_x_section)
        distance_from_center_y = abs(50 - target_y_section)
        
        distance_from_center = max(distance_from_center_x, distance_from_center_y)
        
        # New speed adjustment logic
        if distance_from_center == 0:  # Exact center
            speed_multiplier = 1  # No movement
        elif 3 <= distance_from_center <= 10:  # Between sections 2 and 5 from center
            speed_multiplier = self.max_speed_multiplier  # Maximum speed
        else:
            # Linear reduction of speed as distance from center increases
            speed_reduction = min(distance_from_center - 10, 45) / 100.0  # 45 sections from 5 to 50, hence max 45% reduction
            speed_multiplier = base_speed * (1 - speed_reduction)
        
        if self.prev_distance is not None:
            distance_change = abs(distance - self.prev_distance)
            speed_adjustment = 1 + (distance_change / self.max_distance) * self.speed_correction_factor
            return speed_multiplier * speed_adjustment
        
        return speed_multiplier
    
    def calc_movement(self, target_x, target_y, target_cls):
        if not cfg.AI_mouse_net:
            offset_x = target_x - self.center_x
            offset_y = target_y - self.center_y

            distance = math.sqrt(offset_x**2 + offset_y**2)
            
            speed_multiplier = self.calculate_speed_multiplier(target_x, target_y, distance)

            degrees_per_pixel_x = self.fov_x / self.screen_width
            degrees_per_pixel_y = self.fov_y / self.screen_height
            
            mouse_move_x = offset_x * degrees_per_pixel_x
            mouse_move_y = offset_y * degrees_per_pixel_y

            # Apply smoothing
            alpha = 0.8
            if not hasattr(self, 'last_move_x'):
                self.last_move_x, self.last_move_y = 0, 0
            
            move_x = alpha * mouse_move_x + (1 - alpha) * self.last_move_x
            move_y = alpha * mouse_move_y + (1 - alpha) * self.last_move_y
            
            self.last_move_x, self.last_move_y = move_x, move_y

            # Convert to actual mouse movement
            move_x = (move_x / 360) * (self.dpi * (1 / self.mouse_sensitivity)) * speed_multiplier
            move_y = (move_y / 360) * (self.dpi * (1 / self.mouse_sensitivity)) * speed_multiplier
                
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
        x = x if x is not None else 0
        y = y if y is not None else 0
        
        if x != 0 and y != 0:
            shooting = self.get_shooting_key_state()
            mouse_aim = cfg.mouse_auto_aim
            triggerbot = cfg.triggerbot
            
            if (shooting and not mouse_aim and not triggerbot) or mouse_aim:
                x, y = int(x), int(y)
                
                if not cfg.mouse_ghub and not cfg.arduino_move and not cfg.mouse_rzr:  # Native move
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)
                elif cfg.mouse_ghub and not cfg.arduino_move and not cfg.mouse_rzr:  # ghub move
                    self.ghub.mouse_xy(x, y)
                elif cfg.arduino_move and not cfg.mouse_rzr:  # Arduino move
                    arduino.move(x, y)
                elif cfg.mouse_rzr:  # Razer move
                    self.rzr.mouse_move(x, y, True)
    
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