import configparser

class Config():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.Read(verbose=False)
    
    def Read(self, verbose=False):
        self.config.read('./config.ini')
        self.config_Detection_window = self.config['Detection window']
        self.detection_window_width = int(self.config_Detection_window['detection_window_width'])
        self.detection_window_height = int(self.config_Detection_window['detection_window_height'])
        
        self.config_Bettercam_Capture = self.config['Bettercam Capture']
        self.Bettercam_capture = self.config_Bettercam_Capture.getboolean('Bettercam_capture')
        self.bettercam_capture_fps = int(self.config_Bettercam_Capture['bettercam_capture_fps'])
        self.bettercam_monitor_id = int(self.config_Bettercam_Capture['bettercam_monitor_id'])
        self.bettercam_gpu_id = int(self.config_Bettercam_Capture['bettercam_gpu_id'])

        self.config_Obs_capture = self.config['Obs capture']
        self.Obs_capture = self.config_Obs_capture.getboolean('Obs_capture')
        self.Obs_camera_id = int(self.config_Obs_capture['Obs_camera_id'])
        self.Obs_capture_fps = int(self.config_Obs_capture['Obs_capture_fps'])
        
        self.config_Aim_settings = self.config['Aim settings']
        self.body_y_offset = float(self.config_Aim_settings['body_y_offset'])
        self.hideout_targets = self.config_Aim_settings.getboolean('hideout_targets')
        self.disable_headshot = self.config_Aim_settings.getboolean('disable_headshot')
        
        self.config_Hotkeys_settings = self.config['Hotkeys settings']
        self.hotkey_targeting = str(self.config_Hotkeys_settings['hotkey_targeting'])
        self.hotkey_exit = str(self.config_Hotkeys_settings['hotkey_exit'])
        self.hotkey_pause = str(self.config_Hotkeys_settings['hotkey_pause'])
        self.hotkey_reload_config = str(self.config_Hotkeys_settings['hotkey_reload_config'])
        
        self.config_Mouse_settings = self.config['Mouse settings']
        self.mouse_dpi = float(self.config_Mouse_settings['mouse_dpi'])
        self.mouse_sensitivity = float(self.config_Mouse_settings['mouse_sensitivity'])
        self.mouse_fov = float(self.config_Mouse_settings['mouse_fov'])
        self.mouse_lock_target = self.config_Mouse_settings.getboolean('mouse_lock_target')
        self.mouse_auto_shoot = self.config_Mouse_settings.getboolean('mouse_auto_shoot')
        self.mouse_auto_aim = self.config_Mouse_settings.getboolean('mouse_auto_aim')
        self.mouse_native = self.config_Mouse_settings.getboolean('mouse_native')
        self.mouse_triggerbot = self.config_Mouse_settings.getboolean('mouse_triggerbot')
        self.mouse_move_by_arduino = self.config_Mouse_settings.getboolean('mouse_move_by_arduino')
        self.mouse_shoot_by_arduino = self.config_Mouse_settings.getboolean('mouse_shoot_by_arduino')
        
        self.config_AI_options = self.config['AI options']
        self.AI_model_path = str(self.config_AI_options['AI_model_path'])
        self.AI_image_size = int(self.config_AI_options['AI_image_size'])
        self.AI_conf = float(self.config_AI_options['AI_conf'])
        self.AI_iou = float(self.config_AI_options['AI_iou'])
        self.AI_device = str(self.config_AI_options['AI_device'])
        self.AI_max_det = int(self.config_AI_options['AI_max_det'])
        
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

        if verbose:
            print('Config reloaded')
