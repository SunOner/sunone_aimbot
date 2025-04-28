import cv2
import bettercam
import mss
from screeninfo import get_monitors
import threading
import queue
import numpy as np

from logic.config_watcher import cfg
from logic.logger import logger

class Capture(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.name = "Capture"
        
        self.print_startup_messages()
        
        self._custom_region = []
        self._offset_x = None
        self._offset_y = None
        
        self.screen_x_center = int(cfg.detection_window_width / 2)
        self.screen_y_center = int(cfg.detection_window_height / 2)

        self.prev_detection_window_width = cfg.detection_window_width
        self.prev_detection_window_height = cfg.detection_window_height
        self.prev_bettercam_capture_fps = cfg.capture_fps
        
        self.frame_queue = queue.Queue(maxsize=1)
        
        self.sct = None
        
        self.running = True
    
        if cfg.Bettercam_capture:
            self.setup_bettercam()
        elif cfg.Obs_capture:
            self.setup_obs()
        elif cfg.mss_capture:
            left, top, w, h = self.calculate_mss_offset()
            self.monitor = {"left": left, "top": top, "width": w, "height": h}

    def setup_bettercam(self):
        self.bc = bettercam.create(
            device_idx=cfg.bettercam_monitor_id,
            output_idx=cfg.bettercam_gpu_id,
            output_color="BGR",
            max_buffer_len=16,
            region=self.calculate_screen_offset()
        )
        if not self.bc.is_capturing:
            self.bc.start(
                region=self.calculate_screen_offset(
                    custom_region=[] if len(self._custom_region) == 0 else self._custom_region,
                    x_offset=self._offset_x if self._offset_x is not None else 0,
                    y_offset=self._offset_y if self._offset_y is not None else 0
                ),
                target_fps=cfg.capture_fps
            )

    def setup_obs(self):
        camera_id = self.find_obs_virtual_camera() if cfg.Obs_camera_id == 'auto' else int(cfg.Obs_camera_id) if cfg.Obs_camera_id.isdigit() else None
        if camera_id is None:
            logger.info('[Capture] OBS Virtual Camera not found')
            exit(0)
        
        self.obs_camera = cv2.VideoCapture(camera_id)
        self.obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.detection_window_width)
        self.obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.detection_window_height)
        self.obs_camera.set(cv2.CAP_PROP_FPS, cfg.capture_fps)

    def setup_mss(self):
        left, top, width, height = self.calculate_mss_offset()
        self.monitor = {"left": left, "top": top, "width": width, "height": height}

    def run(self):
        if cfg.mss_capture and self.sct is None:
            self.sct = mss.mss()
        try:
            while self.running:
                frame = self.capture_frame()
                if frame is not None:
                    if self.frame_queue.full():
                        self.frame_queue.get()
                    self.frame_queue.put(frame, block=False)
        finally:
            if cfg.mss_capture and self.sct is not None:
                self.sct.close()
            
    def capture_frame(self):
        if cfg.Bettercam_capture:
            return self.bc.get_latest_frame()
        
        if cfg.Obs_capture:
            ret_val, img = self.obs_camera.read()
            return img if ret_val else None

        if cfg.mss_capture:
            screenshot = self.sct.grab(self.monitor)
            img = np.frombuffer(screenshot.bgra, np.uint8).reshape((screenshot.height, screenshot.width, 4))
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def get_new_frame(self):
        try:
            return self.frame_queue.get(timeout=1)
        except queue.Empty:
            return None
    
    def restart(self):
        if cfg.Bettercam_capture and (
            self.prev_detection_window_height != cfg.detection_window_height or 
            self.prev_detection_window_width != cfg.detection_window_width or 
            self.prev_bettercam_capture_fps != cfg.capture_fps
        ):
            self.bc.stop()
            del self.bc
            self.setup_bettercam()

            self.screen_x_center = cfg.detection_window_width / 2
            self.screen_y_center = cfg.detection_window_height / 2

            self.prev_detection_window_width = cfg.detection_window_width
            self.prev_detection_window_height = cfg.detection_window_height

            logger.info('[Capture] Capture reloaded')
            
    def calculate_screen_offset(self, custom_region=[], x_offset=None, y_offset=None):
        if x_offset is None:
            x_offset = 0
        if y_offset is None:
            y_offset = 0
        
        if not custom_region:
            left, top = self.get_primary_display_resolution()
        else:
            left, top = custom_region
        
        left = left / 2 - cfg.detection_window_width / 2 + x_offset
        top = top / 2 - cfg.detection_window_height / 2 - y_offset
        width = cfg.detection_window_width
        height = cfg.detection_window_height
        
        return (int(left), int(top), int(width), int(height))

    def calculate_mss_offset(self):
        x, y = self.get_primary_display_resolution()
        left = x / 2 - cfg.detection_window_width / 2
        top = y / 2 - cfg.detection_window_height / 2
        return int(left), int(top), int(cfg.detection_window_width), int(cfg.detection_window_height)

    def get_primary_display_resolution(self):
        for m in get_monitors():
            if m.is_primary:
                return m.width, m.height
            
    def find_obs_virtual_camera(self):
        max_tested = 20
        obs_camera_name = 'DSHOW'
        
        for i in range(max_tested):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not cap.isOpened():
                continue
            if cap.getBackendName() == obs_camera_name:
                logger.info(f'[Capture] OBS Virtual Camera found at index {i}')
                cap.release()
                return i
            cap.release()
        return -1
    
    def print_startup_messages(self):
        version = 0
        try:
            with open('./version', 'r') as f:
                version = f.readline().split('=')[1].strip()
        except FileNotFoundError:
            logger.info('(version file is not found)')
        except Exception as e:
            logger.info(f'Error with read version file: {str(e)}')

        logger.info(f"""
Sunone Aimbot is started! (Version {version})
Hotkeys:
[{cfg.hotkey_targeting}] - Aiming at the target
[{cfg.hotkey_exit}] - EXIT
[{cfg.hotkey_pause}] - PAUSE AIM
[{cfg.hotkey_reload_config}] - Reload config
""")
    
    def convert_to_circle(self, image):
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.ellipse(mask, (width // 2, height // 2), (width // 2, height // 2), 0, 0, 360, 255, -1)
        return cv2.bitwise_and(image, cv2.merge([mask, mask, mask]))
    
    def Quit(self):
        self.running = False
        if cfg.Bettercam_capture and hasattr(self, 'bc') and self.bc.is_capturing:
            self.bc.stop()
        
        if cfg.Obs_capture and hasattr(self, 'obs_camera'):
            self.obs_camera.release()
        
        self.join()

capture = Capture()
capture.start()