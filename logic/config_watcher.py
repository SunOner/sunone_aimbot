import configparser
import random

from logic.logger import logger

class Config():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.window_name = self.get_random_window_name()
        self.Read(verbose=False)
    
    def Read(self, verbose=False):
        try:
            with open("config.ini", "r", encoding="utf-8",) as f:
                self.config.read_file(f)
        except FileNotFoundError:
            logger.error("[Config] Config file not found!")
            quit()
        except Exception as e:
            logger.error(f"[Config] Unknown exception: {str(e)}")
            
        # Detection window
        self.config_Detection_window = self.config["Detection window"]
        self.detection_window_width = int(self.config_Detection_window["detection_window_width"])
        self.detection_window_height = int(self.config_Detection_window["detection_window_height"])
        self.circle_capture = self.config_Detection_window.getboolean("circle_capture")
        
        # Capture Global
        self.config_Capture_Global = self.config["Capture Methods"]
        self.capture_fps = int(self.config_Capture_Global["capture_fps"])
        
        # Capture Method Bettercam
        self.config_Bettercam_Capture = self.config["Capture Methods"]
        self.Bettercam_capture = self.config_Bettercam_Capture.getboolean("Bettercam_capture")
        self.bettercam_monitor_id = int(self.config_Bettercam_Capture["bettercam_monitor_id"])
        self.bettercam_gpu_id = int(self.config_Bettercam_Capture["bettercam_gpu_id"])
        
        # Capture Method Obs
        self.config_Obs_capture = self.config["Capture Methods"]
        self.Obs_capture = self.config_Obs_capture.getboolean("Obs_capture")
        self.Obs_camera_id = str(self.config_Obs_capture["Obs_camera_id"])
        
        # Capture Method mss
        self.config_mss_capture = self.config["Capture Methods"]
        self.mss_capture = self.config_mss_capture.getboolean("mss_capture")
        
        # Aim
        self.config_Aim = self.config["Aim"]
        self.body_y_offset = float(self.config_Aim["body_y_offset"])
        self.hideout_targets = self.config_Aim.getboolean("hideout_targets")
        self.disable_headshot = self.config_Aim.getboolean("disable_headshot")
        self.disable_prediction = self.config_Aim.getboolean("disable_prediction")
        self.prediction_interval = float(self.config_Aim["prediction_interval"])
        self.third_person = self.config_Aim.getboolean("third_person")
        
        # Hotkeys
        self.config_Hotkeys_settings = self.config["Hotkeys"]
        self.hotkey_targeting = str(self.config_Hotkeys_settings["hotkey_targeting"])
        self.hotkey_targeting_list = self.hotkey_targeting.split(",")
        self.hotkey_exit = str(self.config_Hotkeys_settings["hotkey_exit"])
        self.hotkey_pause = str(self.config_Hotkeys_settings["hotkey_pause"])
        self.hotkey_reload_config = str(self.config_Hotkeys_settings["hotkey_reload_config"])
        
        # Mouse
        self.config_Mouse = self.config["Mouse"]
        self.mouse_dpi = int(self.config_Mouse["mouse_dpi"])
        self.mouse_sensitivity = float(self.config_Mouse["mouse_sensitivity"])
        self.mouse_fov_width = int(self.config_Mouse["mouse_fov_width"])
        self.mouse_fov_height = int(self.config_Mouse["mouse_fov_height"])
        self.mouse_min_speed_multiplier = float(self.config_Mouse["mouse_min_speed_multiplier"])
        self.mouse_max_speed_multiplier = float(self.config_Mouse["mouse_max_speed_multiplier"])
        self.mouse_lock_target = self.config_Mouse.getboolean("mouse_lock_target")
        self.mouse_auto_aim = self.config_Mouse.getboolean("mouse_auto_aim")
        self.mouse_ghub = self.config_Mouse.getboolean("mouse_ghub")
        self.mouse_rzr = self.config_Mouse.getboolean("mouse_rzr")
        
        # Shooting
        self.config_Shooting = self.config["Shooting"]
        self.auto_shoot = self.config_Shooting.getboolean("auto_shoot")
        self.triggerbot = self.config_Shooting.getboolean("triggerbot")
        self.force_click = self.config_Shooting.getboolean("force_click")
        self.bScope_multiplier = float(self.config_Shooting["bScope_multiplier"])
        
        # Arduino
        self.config_Arduino = self.config["Arduino"]
        self.arduino_move = self.config_Arduino.getboolean("arduino_move")
        self.arduino_shoot = self.config_Arduino.getboolean("arduino_shoot")
        self.arduino_port = str(self.config_Arduino["arduino_port"])
        self.arduino_baudrate = int(self.config_Arduino["arduino_baudrate"])
        self.arduino_16_bit_mouse = self.config_Arduino.getboolean("arduino_16_bit_mouse")
        
        # AI
        self.config_AI = self.config["AI"]
        self.AI_model_name = str(self.config_AI["AI_model_name"])
        self.ai_model_image_size = int(self.config_AI["ai_model_image_size"])
        self.AI_conf = float(self.config_AI["AI_conf"])
        self.AI_device = str(self.config_AI["AI_device"])
        self.AI_enable_AMD = self.config_AI.getboolean("AI_enable_AMD")
        self.disable_tracker = self.config_AI.getboolean("disable_tracker")
        
        # Overlay
        self.config_overlay = self.config["overlay"]
        self.show_overlay = self.config_overlay.getboolean("show_overlay")
        self.overlay_show_borders = self.config_overlay.getboolean("overlay_show_borders")
        self.overlay_show_boxes = self.config_overlay.getboolean("overlay_show_boxes")
        self.overlay_show_target_line = self.config_overlay.getboolean("overlay_show_target_line")
        self.overlay_show_target_prediction_line = self.config_overlay.getboolean("overlay_show_target_prediction_line")
        self.overlay_show_labels = self.config_overlay.getboolean("overlay_show_labels")
        self.overlay_show_conf = self.config_overlay.getboolean("overlay_show_conf")
        
        # Debug window
        self.config_Debug_window = self.config["Debug window"]
        self.show_window = self.config_Debug_window.getboolean("show_window")
        self.show_detection_speed = self.config_Debug_window.getboolean("show_detection_speed")
        self.show_window_fps = self.config_Debug_window.getboolean("show_window_fps")
        self.show_boxes = self.config_Debug_window.getboolean("show_boxes")
        self.show_labels = self.config_Debug_window.getboolean("show_labels")
        self.show_conf = self.config_Debug_window.getboolean("show_conf")
        self.show_target_line = self.config_Debug_window.getboolean("show_target_line")
        self.show_target_prediction_line = self.config_Debug_window.getboolean("show_target_prediction_line")
        self.show_bScope_box = self.config_Debug_window.getboolean("show_bScope_box")
        self.show_history_points = self.config_Debug_window.getboolean("show_history_points")
        self.debug_window_always_on_top = self.config_Debug_window.getboolean("debug_window_always_on_top")
        self.spawn_window_pos_x = int(self.config_Debug_window["spawn_window_pos_x"])
        self.spawn_window_pos_y = int(self.config_Debug_window["spawn_window_pos_y"])
        self.debug_window_scale_percent = int(self.config_Debug_window["debug_window_scale_percent"])
        self.debug_window_screenshot_key = str(self.config_Debug_window["debug_window_screenshot_key"])
        self.debug_window_name = self.window_name
        
        if verbose:
            logger.info("[Config] Config reloaded")
            
    def get_random_window_name(self):
        try:
            with open("window_names.txt", "r", encoding="utf-8") as file:
                window_names = file.read().splitlines()
            return random.choice(window_names) if window_names else "Calculator"
        except FileNotFoundError:
            logger.error("[Config] window_names.txt file not found, using default window name.")
            return "Calculator"
        except Exception as e:
            logger.error(f"[Config] Unknown exception: {str(e)}")
            return "Calculator"

cfg = Config()