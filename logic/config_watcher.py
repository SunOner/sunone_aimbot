import configparser

class Config():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.Read(verbose=False)
    
    def Read(self, verbose=False):
        self.config.read('./config.ini')
        # Detection window
        self.config_Detection_window = self.config['Detection window']
        self.detection_window_width = int(self.config_Detection_window['detection_window_width'])
        self.detection_window_height = int(self.config_Detection_window['detection_window_height'])
        # Capture Methods
        self.config_Bettercam_Capture = self.config['Capture Methods']
        self.Bettercam_capture = self.config_Bettercam_Capture.getboolean('Bettercam_capture')
        self.bettercam_capture_fps = int(self.config_Bettercam_Capture['bettercam_capture_fps'])
        self.bettercam_monitor_id = int(self.config_Bettercam_Capture['bettercam_monitor_id'])
        self.bettercam_gpu_id = int(self.config_Bettercam_Capture['bettercam_gpu_id'])
        
        self.config_Obs_capture = self.config['Capture Methods']
        self.Obs_capture = self.config_Obs_capture.getboolean('Obs_capture')
        self.Obs_camera_id = str(self.config_Obs_capture['Obs_camera_id'])
        self.Obs_capture_fps = int(self.config_Obs_capture['Obs_capture_fps'])
        # Aim
        self.config_Aim = self.config['Aim']
        self.body_y_offset = float(self.config_Aim['body_y_offset'])
        self.hideout_targets = self.config_Aim.getboolean('hideout_targets')
        self.disable_headshot = self.config_Aim.getboolean('disable_headshot')
        # Hotkeys
        self.config_Hotkeys_settings = self.config['Hotkeys']
        self.hotkey_targeting = str(self.config_Hotkeys_settings['hotkey_targeting'])
        self.hotkey_targeting_list = self.hotkey_targeting.split(',')
        self.hotkey_exit = str(self.config_Hotkeys_settings['hotkey_exit'])
        self.hotkey_pause = str(self.config_Hotkeys_settings['hotkey_pause'])
        self.hotkey_reload_config = str(self.config_Hotkeys_settings['hotkey_reload_config'])
        self.hotkey_turn_off_mask = str(self.config_Hotkeys_settings['hotkey_turn_off_mask'])
        # Mouse
        self.config_Mouse = self.config['Mouse']
        self.mouse_dpi = int(self.config_Mouse['mouse_dpi'])
        self.mouse_sensitivity = float(self.config_Mouse['mouse_sensitivity'])
        self.mouse_fov_width = int(self.config_Mouse['mouse_fov_width'])
        self.mouse_fov_height = int(self.config_Mouse['mouse_fov_height'])
        self.mouse_lock_target = self.config_Mouse.getboolean('mouse_lock_target')
        self.mouse_auto_shoot = self.config_Mouse.getboolean('mouse_auto_shoot')
        self.mouse_auto_aim = self.config_Mouse.getboolean('mouse_auto_aim')
        self.mouse_ghub = self.config_Mouse.getboolean('mouse_ghub')
        self.mouse_triggerbot = self.config_Mouse.getboolean('mouse_triggerbot')
        self.mouse_force_click = self.config_Mouse.getboolean('mouse_force_click')
        # Arduino
        self.config_Arduino = self.config['Arduino']
        self.arduino_move = self.config_Arduino.getboolean('arduino_move')
        self.arduino_shoot = self.config_Arduino.getboolean('arduino_shoot')
        self.arduino_port = str(self.config_Arduino['arduino_port'])
        self.arduino_baudrate = int(self.config_Arduino['arduino_baudrate'])
        # AI
        self.config_AI = self.config['AI']
        self.AI_model_name = str(self.config_AI['AI_model_name'])
        self.AI_image_size = int(self.config_AI['AI_image_size'])
        self.AI_conf = float(self.config_AI['AI_conf'])
        self.AI_device = str(self.config_AI['AI_device'])
        self.AI_enable_AMD = self.config_AI.getboolean('AI_enable_AMD')
        self.AI_mouse_net = self.config_AI.getboolean('AI_mouse_net')
        # Overlay
        self.config_Overlay = self.config['Overlay']
        self.show_overlay_detector = self.config_Overlay.getboolean('show_overlay_detector')
        self.show_overlay_boxes = self.config_Overlay.getboolean('show_overlay_boxes')
        self.show_overlay_line = self.config_Overlay.getboolean('show_overlay_line')
        self.show_overlay_mask = self.config_Overlay.getboolean('show_overlay_mask')
        # Debug window
        self.config_Debug_window = self.config['Debug window']
        self.show_window = self.config_Debug_window.getboolean('show_window')
        self.show_speed = self.config_Debug_window.getboolean('show_speed')
        self.show_fps = self.config_Debug_window.getboolean('show_fps')
        self.show_boxes = self.config_Debug_window.getboolean('show_boxes')
        self.show_labels = self.config_Debug_window.getboolean('show_labels')
        self.show_conf = self.config_Debug_window.getboolean('show_conf')
        self.show_target_line = self.config_Debug_window.getboolean('show_target_line')
        self.debug_window_always_on_top = self.config_Debug_window.getboolean('debug_window_always_on_top')
        self.debug_window_scale_percent = int(self.config_Debug_window['debug_window_scale_percent'])
        self.debug_window_name = str(self.config_Debug_window['debug_window_name'])
        # Exclude Detection Mask
        self.config_Exclude_Mask = self.config['Exclude Mask']
        self.mask_enabled = self.config_Exclude_Mask.getboolean('mask_enabled')
        self.mask_points = str(self.config_Exclude_Mask['mask_points']).split(',')
        
        if verbose:
            print('Config reloaded')
            
    def save_mask_points(self, mask_points):
        self.config.set('Exclude Mask', 'mask_points', ','.join(map(str, mask_points)))
        with open('./config.ini', 'w') as configfile:
            self.config.write(configfile)
    
    def read_mask_points(self):
        mask_points_str = self.config.get('Exclude Mask', 'mask_points', fallback='')
        mask_points = []
        try:
            points = mask_points_str.replace(' ', '').split('),(')
            points[0] = points[0].lstrip('(')
            points[-1] = points[-1].rstrip(')')
            for point_str in points:
                point = tuple(map(int, point_str.split(',')))
                mask_points.append(point)
            return mask_points
        except Exception as e:
            print(f'Invalid mask points format in config. Should be (x1, y1),(x2, y2),...\n{e}')
            return []