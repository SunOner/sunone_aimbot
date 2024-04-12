import cv2
import bettercam
from screeninfo import get_monitors
from logic.config_watcher import cfg

class Capture():
    def __init__(self):
        self.Warnings()
        self.print_startup_messages()
        
        self._custom_region = []
        self._offset_x = None
        self._offset_y = None
        
        self.screen_x_center = int(cfg.detection_window_width / 2)
        self.screen_y_center = int(cfg.detection_window_height / 2)

        self.prev_detection_window_width = cfg.detection_window_width
        self.prev_detection_window_height = cfg.detection_window_height
        self.prev_bettercam_capture_fps = cfg.bettercam_capture_fps
        
        if cfg.Bettercam_capture:
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64, region=self.Calculate_screen_offset())
            if self.bc.is_capturing == False:
                self.bc.start(region=self.Calculate_screen_offset(custom_region=[] if len(self._custom_region) <=0 else self._custom_region, x_offset=None if self._offset_x == None else self._offset_x, y_offset = None if self._offset_y == None else self._offset_y), target_fps=cfg.bettercam_capture_fps)
        
        if cfg.Obs_capture:
            if cfg.Obs_camera_id == 'auto':
                camera_id = self.find_obs_virtual_camera()
                if camera_id == -1:
                    print('OBS Virtual Camera not found')
                    exit(0)
            elif cfg.Obs_camera_id.isdigit:
                camera_id = int(cfg.Obs_camera_id)
            self.obs_camera = cv2.VideoCapture(camera_id)
            self.obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.detection_window_width)
            self.obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.detection_window_height)
            self.obs_camera.set(cv2.CAP_PROP_FPS, cfg.Obs_capture_fps)
        
    def get_new_frame(self):
        if cfg.Bettercam_capture:
            return self.bc.get_latest_frame()
        
        if cfg.Obs_capture:
            ret_val, img = self.obs_camera.read()
            if ret_val:
                return img
            else:
                print('OBS Virtual Camera not found')
                exit(0)
    
    def restart(self):
        if cfg.Bettercam_capture and self.prev_detection_window_height != cfg.detection_window_height or cfg.Bettercam_capture and self.prev_detection_window_width != cfg.detection_window_width or cfg.Bettercam_capture and self.prev_bettercam_capture_fps != cfg.bettercam_capture_fps:
            self.bc.stop()
            del self.bc
            
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64)
            self.bc.start(self.Calculate_screen_offset(), target_fps=cfg.bettercam_capture_fps)

            self.screen_x_center = cfg.detection_window_width / 2
            self.screen_y_center = cfg.detection_window_height / 2

            self.prev_detection_window_width = cfg.detection_window_width
            self.prev_detection_window_height = cfg.detection_window_height

            print('Capture reloaded')
            
    def Calculate_screen_offset(self, custom_region = [], x_offset=None, y_offset=None):
        if x_offset is None:
            x_offset = 0
        if y_offset is None:
            y_offset = 0
        
        if len(custom_region) <= 0:
            left, top = self.get_primary_display_resolution()
        else:
            left, top = custom_region
        
        left = left / 2 - cfg.detection_window_width / 2 + x_offset
        top = top / 2 - cfg.detection_window_height / 2 - y_offset
        width = left + cfg.detection_window_width
        height = top + cfg.detection_window_height
        
        return (int(left), int(top), int(width), int(height))
    
    def get_primary_display_resolution(self):
        _ = get_monitors()
        for m in _:
            if m.is_primary:
                return m.width, m.height
            
    def find_obs_virtual_camera(self):
        max_tested = 20
        obs_camera_name = 'DSHOW'
        
        for i in range(max_tested):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not cap.isOpened():
                continue
            backend_name = cap.getBackendName()
            if backend_name == obs_camera_name:
                print(f'OBS Virtual Camera found at index {i}')
                cap.release()
                return i
            cap.release()
        return -1
    
    def print_startup_messages(self):
        version = 0
        try:
            with open('./version', 'r') as f:
                lines = f.read().split('\n')
                version = lines[0].split('=')[1]
        except:
            print('(version file is not found)')

        print(f'Yolov8 Aimbot is started! (Version {version})\n\n',
                'Hotkeys:\n',
                f'[{cfg.hotkey_targeting}] - Aiming at the target\n',
                f'[{cfg.hotkey_exit}] - EXIT\n',
                f'[{cfg.hotkey_pause}] - PAUSE AIM\n',
                f'[{cfg.hotkey_reload_config}] - Reload config\n')
        
    def Warnings(self):
        # FATAL ERRORS
        if cfg.Bettercam_capture == False and cfg.Obs_capture == False:
            print('Use at least one image capture method.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
            exit(0)
        if cfg.Bettercam_capture and cfg.Obs_capture:
            print('Only one capture method is possible.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
            exit(0)
        # WARNINGS
        if '.pt' in cfg.AI_model_name:
            print('WARNING: Export the model to `.engine` for better performance!')
        if cfg.mouse_ghub == False and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print('WARNING: win32api is detected in some games.')
        if cfg.mouse_ghub and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print('WARNING: ghub is detected in some games.')
        if cfg.show_window:
            print('WARNING: An open debug window can affect performance.')
        if cfg.bettercam_capture_fps >= 120:
            print('WARNING: A large number of frames per second can affect the behavior of automatic aiming. (Shaking).')
        if cfg.detection_window_width >= 600:
            print('WARNING: The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance.')
        if cfg.detection_window_height >= 600:
            print('WARNING: The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance.')
        if cfg.arduino_move == False:
            print('WARNING: Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.arduino_shoot == False and cfg.auto_shoot:
            print('WARNING: Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.AI_conf <= 0.15:
            print('WARNING: A small value of `AI_conf ` can lead to a large number of false positives.')
            
    def Quit(self):
        if cfg.Bettercam_capture and self.bc.is_capturing:
            self.bc.stop()
            
capture = Capture()