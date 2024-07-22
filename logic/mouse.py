import torch
import win32con, win32api
import torch.nn as nn
import time
import numpy as np
from logic.config_watcher import cfg
from logic.visual import visuals
from logic.shooting import shooting
from logic.buttons import Buttons
from filterpy.kalman import UnscentedKalmanFilter, MerweScaledSigmaPoints

if cfg.arduino_move or cfg.arduino_shoot:
    from logic.arduino import arduino

class Mouse_net(nn.Module): # Mouse net
    def __init__(self, arch): # Initialize
        super(Mouse_net, self).__init__() # Super
        self.fc1 = nn.Linear(10, 128, arch) # Fully connected layer 1
        self.fc2 = nn.Linear(128, 128, arch) # Fully connected layer 2
        self.fc3 = nn.Linear(128, 64, arch) # Fully connected layer 3
        self.fc4 = nn.Linear(64, 2, arch) # Fully connected layer 4

    def forward(self, x):
        x = torch.relu(self.fc1(x)) # ReLU activation function layer 1
        x = torch.relu(self.fc2(x)) # ReLU activation function layer 2
        x = torch.relu(self.fc3(x)) # ReLU activation function layer 3
        x = self.fc4(x) # Fully connected layer 4
        return x # Return x
 
class MouseThread:
    def __init__(self):
        # Get values from config
        self.dpi = cfg.mouse_dpi # DPI
        self.mouse_sensitivity = cfg.mouse_sensitivity # Mouse sensitivity
        self.fov_x = cfg.mouse_fov_width # Field of view x
        self.fov_y = cfg.mouse_fov_height # Field of view y
        self.disable_prediction = cfg.disable_prediction # Disable prediction
        self.prediction_interval = cfg.prediction_interval # Prediction interval
        self.bScope_multiplier = cfg.bScope_multiplier # bScope multiplier
        self.screen_width = cfg.detection_window_width # Screen width
        self.screen_height = cfg.detection_window_height # Screen height
        self.dpi_sensitivity_factor = (self.dpi * (1 / self.mouse_sensitivity)) / 360
        #Define the center of screen
        self.center_x = self.screen_width / 2 # Center x
        self.center_y = self.screen_height / 2 # Center y
        
        # Define Adjustment values
        self.non_AI_vertical_offset = cfg.non_AI_vertical_offset # Add or subtract lower is higer -10.0 to lower 10 and 10.0 to raise 10
        self.non_AI_horizontal_offset = cfg.non_AI_horizontal_offset # Add or subtract lower is higer -10.0 to lower 10 and 10.0 to raise 10
        self.smoothing_factor = cfg.smoothing_factor  # Add small amount mouse smoothing
        self.Mouse_net_vertical_offset = cfg.Mouse_net_vertical_offset # Add or subtract lower is higer -10.0 to lower 10 and 10.0 to raise 10
        self.Mouse_net_horizontal_offset = cfg.Mouse_net_horizontal_offset # Add or subtract lower is higer -10.0 to lower 10 and 10.0 to raise 10
        self.max_movement_x = cfg.max_x_movement  # Max horizontal movement allowed per frame
        self.max_movement_y = cfg.max_y_movement # Max vertical movement allowed per frame
        self.mouse_sensitivity_x = cfg.mouse_sensitivity_x
        self.mouse_sensitivity_y = cfg.mouse_sensitivity_y
        self.ukf_x = self.create_ukf() 
        self.ukf_y = self.create_ukf() 
        self.last_measurement_time = time.time()
        # Default values for the purpouse of naming as a value
        self.prev_x = 0 # Previous x default
        self.prev_y = 0 # Previous y default
        self.prev_time = None # Previous time default
        self.last_mouse_pos = None #mouse position default
        self.prev_velocity_x = 0 # velocity x default
        self.prev_velocity_y = 0 # velocity y default
        self.last_target_x = None  # Initialize last target x position
        self.last_target_y = None  # Initialize last target y position
        self.bScope = False # bScope default
        #Inference device
        self.arch = self.get_arch() # Get device for inference
        
        # For gHub mouse
        if cfg.mouse_ghub:
            from logic.ghub import gHub
            self.ghub = gHub

        # For AI mouse net    
        if cfg.AI_mouse_net:
            self.device = torch.device(self.arch) # Get device for AI mouse net
            self.model = Mouse_net(arch=self.arch).to(self.device) # Load model to device
            try:
                self.model.load_state_dict(torch.load('mouse_net.pth', map_location=self.device)) # Load mouse_net.pth model
            except Exception as e: # If model not found
                print(e) # Print error
                print('Please train mouse_net model, or download latest trained mouse_net.pth model from repository and place in base folder. Instruction here: https://github.com/SunOner/mouse_net')
                exit()
            self.model.eval() # Set model to evaluation mode
        # For Arduino mouse_net
        if cfg.arduino_move:
            arduino.move(0, 0)
        # For gHub mouse_net
        if cfg.mouse_ghub:
            self.ghub.mouse_xy(0, 0)


    # Get device for inference
    def get_arch(self):
        if cfg.AI_enable_AMD:
            return f'hip:{cfg.AI_device}'
        if 'cpu' in cfg.AI_device:
            return 'cpu'
        return f'cuda:{cfg.AI_device}'
    
    def create_ukf(self):
        # Directly create the UKF object with MerweScaledSigmaPoints
        ukf = UnscentedKalmanFilter(
            dim_x=3, 
            dim_z=1, 
            dt=1/cfg.bettercam_capture_fps, 
            hx=self.hx, 
            fx=self.fx, 
            points=MerweScaledSigmaPoints(3, alpha=.1, beta=2., kappa=0)  
        )
        ukf.x = np.array([0., 0., 0.])    # Initial state (position, velocity, acceleration)
        ukf.P = np.diag([100., 100., 1.])  # Initial covariance matrix
        ukf.R = np.array([[100.]])         # Measurement noise
        ukf.Q = np.diag([0.01, 0.01, 0.001])  # Process noise (tune these values)
        return ukf
    
    def fx(self, x, dt):
        # State transition function (constant acceleration model)
        F = np.array([[1, dt, 0.5*dt*dt],
                      [0, 1, dt],
                      [0, 0, 1]])
        return F @ x

    def hx(self, x):
        # Measurement function (we only measure position)
        return np.array([x[0]])
    
    # Main loop      
    def process_data(self, data):  # Process data
        
        if data is None:  # Check if data is None
           return  # Return immediately if there's no valid data
        target_x, target_y, target_w, target_h, target_cls = data  # Unpack coordinates of the bounding box
        if target_x is None or target_y is None:
            return

        
        # draw simple line
        if (cfg.show_window and cfg.show_target_line) or (cfg.show_overlay and cfg.show_target_line):
            visuals.draw_target_line(target_x, target_y, target_cls)    # Draw target line
        
        # bScope
        self.bScope = self.check_target_in_scope(target_x, target_y, target_w, target_h, self.bScope_multiplier) if cfg.auto_shoot or cfg.triggerbot else False # Check target in scope
        self.bScope = cfg.force_click or self.bScope # Force click

        # prediction
        if not self.disable_prediction:
            current_time = time.time() # Get current time
            
            target_x, target_y = self.predict_target_position(target_x, target_y, current_time) # Predict target position
            
            if (cfg.show_window and cfg.show_target_prediction_line) or (cfg.show_overlay and cfg.show_target_prediction_line): # Draw prediction line
                visuals.draw_predicted_position(target_x, target_y, target_cls) # Draw predicted position
      
        move_x, move_y = self.calc_movement(target_x, target_y, target_w, target_h) # Pass all parameters
        target_x, target_y = self.calc_movement(target_x, target_y, target_w, target_h) # Pass all parameters




        # history points
        if (cfg.show_window and cfg.show_history_points) or (cfg.show_overlay and cfg.show_history_points):  # Draw history points
            visuals.draw_history_point_add_point(target_x, target_y) # Add point to history points
        
        shooting_key_state = self.get_shooting_key_state()
        shooting.queue.put((self.bScope, shooting_key_state)) 

        self.move_mouse(target_x, target_y, shooting_key_state)

    def predict_target_position(self, target_x, target_y, current_time): # Predict target position
        if self.prev_time is None: # First frame
            self.prev_time = current_time  # Set current time as previous time
            self.prev_x = target_x # Set target x as previous x
            self.prev_y = target_y # Set target y as previous y
            self.prev_velocity_x = 0 # Set velocity x as 0
            self.prev_velocity_y = 0 # Set velocity y as 0
            return target_x, target_y   # Return target x and target y

        delta_time = current_time - self.prev_time # Calculate delta time


        # Calculate velocity 
        velocity_x = (target_x - self.prev_x) / delta_time
        velocity_y = (target_y - self.prev_y) / delta_time

        acceleration_x = (velocity_x - self.prev_velocity_x) / delta_time # Calculate acceleration x
        acceleration_y = (velocity_y - self.prev_velocity_y) / delta_time # Calculate acceleration y

        prediction_interval = delta_time * self.prediction_interval # Calculate prediction interval

        predicted_x = target_x + velocity_x * prediction_interval + 0.5 * acceleration_x * (prediction_interval ** 2) # x = x0 + v0t + 0.5at^2
        predicted_y = target_y + velocity_y * prediction_interval + 0.5 * acceleration_y * (prediction_interval ** 2) # y = y0 + v0t + 0.5at^2

        self.prev_x = target_x # Set target x as previous x
        self.prev_y = target_y # Set target y as previous y
        self.prev_velocity_x = velocity_x # Set velocity x as previous velocity x
        self.prev_velocity_y = velocity_y # Set velocity y as previous velocity y
        self.prev_time = current_time # Set current time as previous time
        return predicted_x, predicted_y # Return predicted x and predicted y
    
    def calc_movement(self, target_x, target_y, target_w, target_h): # Calculate movement
        if not cfg.AI_mouse_net: # If AI mouse net is disabled

            move_x = ((target_x - self.center_x) / self.screen_width) * self.fov_x * self.dpi_sensitivity_factor * self.mouse_sensitivity_x + self.non_AI_horizontal_offset
            move_y = ((target_y - self.center_y) / self.screen_height) * self.fov_y * self.dpi_sensitivity_factor * self.mouse_sensitivity_y + self.non_AI_vertical_offset
                        #clamp movement
            move_x = max(-self.max_movement_x, min(move_x, self.max_movement_x))  
            move_y = max(-self.max_movement_y, min(move_y, self.max_movement_y))
                            # Get current time for delta time calculation
            if self.ukf_x is None:
                self.ukf_x = self.create_ukf()
            if self.ukf_y is None:
                self.ukf_y = self.create_ukf() 

                # Get current time for delta time calculation
                current_time = time.time()
                delta_time = current_time - self.last_measurement_time

                # Predict and Update with UKF
                self.ukf_x.predict(dt=delta_time)  # Now safe to call predict
                self.ukf_x.update(move_x)
                self.ukf_y.predict(dt=delta_time)
                self.ukf_y.update(move_y)

                move_x = self.ukf_x.x[0]
                move_y = self.ukf_y.x[0]
                self.last_measurement_time = current_time
                
            return move_x, move_y

        else:
                input_data = [ # Input data
                    self.screen_width,  # Screen width
                    self.screen_height, # Screen height
                    self.center_x, # Center x
                    self.center_y, # Center y
                    self.dpi, # DPI
                    self.mouse_sensitivity, # Mouse sensitivity
                    self.fov_x, # FOV x
                    self.fov_y, # FOV y
                    target_x, # Target x
                    target_y # Target y
                ]
                
                input_tensor = torch.tensor(input_data, dtype=torch.float32).to(self.device) # Convert input data to tensor
                with torch.no_grad(): # Disable gradient calculation
                    move = self.model(input_tensor).cpu().numpy() # Calculate move

                # Clamp AND Adjust axis 0
                move[0] = np.clip(move[0], -self.max_movement_x, self.max_movement_x) + self.Mouse_net_horizontal_offset  # Limit movement x and adjust aim left and right
                move[1] = np.clip(move[1], -self.max_movement_y, self.max_movement_y) + self.Mouse_net_vertical_offset  # Limit movement x and adjust aim up and down

                return move[0], move[1] # Return move x and move y in numpy array

    def move_mouse(self, x, y, shooting_key_state):
        x = x if x is not None else 0
        y = y if y is not None else 0

        if (shooting_key_state and not cfg.mouse_auto_aim and not cfg.triggerbot) or cfg.mouse_auto_aim:
            if not cfg.mouse_ghub and not cfg.arduino_move:
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
            elif cfg.mouse_ghub:
                self.ghub.mouse_xy(int(x), int(y))
            else:  # cfg.arduino_move
                arduino.move(int(x), int(y))
    
    def get_shooting_key_state(self): # Get shooting key state
        for key_name in cfg.hotkey_targeting_list: # For key name in hotkey targeting list
            key_code = Buttons.KEY_CODES.get(key_name.strip()) # Get key code
            if key_code is not None: # If key code is not None
                state = win32api.GetKeyState(key_code) if cfg.mouse_lock_target else win32api.GetAsyncKeyState(key_code) # Get key state
                if state < 0 or state == 1: # If state is less than 0 or equal to 1
                    return True # Return True
        return False # Return False
      
    def check_target_in_scope(self, target_x, target_y, target_w, target_h, reduction_factor): # Check target in scope
        reduced_w = target_w * reduction_factor / 2 # Calculate reduced w
        reduced_h = target_h * reduction_factor / 2 # Calculate reduced h

        x1 = target_x - reduced_w # Calculate x1
        x2 = target_x + reduced_w # Calculate x2
        y1 = target_y - reduced_h # Calculate y1
        y2 = target_y + reduced_h # Calculate y2

        bScope = self.center_x > x1 and self.center_x < x2 and self.center_y > y1 and self.center_y < y2 # Check if target in scope
            
        if cfg.show_window and cfg.show_bScope_box: # Draw bScope box
            visuals.draw_bScope(x1, x2, y1, y2, bScope) # Draw bScope box
        
        return bScope # Return bScope

    def update_settings(self): # Update settings
        self.mouse_sensitivity_x = cfg.mouse_sensitivity_x
        self.mouse_sensitivity_y = cfg.mouse_sensitivity_y
        self.dpi = cfg.mouse_dpi # DPI
        self.mouse_sensitivity = cfg.mouse_sensitivity # Mouse sensitivity
        self.fov_x = cfg.mouse_fov_width # Field of view x
        self.fov_y = cfg.mouse_fov_height # Field of view y
        self.disable_prediction = cfg.disable_prediction # Disable prediction
        self.prediction_interval = cfg.prediction_interval # Prediction interval
        self.bScope_multiplier = cfg.bScope_multiplier # bScope multiplier
        self.screen_width = cfg.detection_window_width # Screen width
        self.screen_height = cfg.detection_window_height # Screen height
        self.center_x = self.screen_width / 2 # Center x
        self.center_y = self.screen_height / 2 # Center y

            
mouse = MouseThread()