import cv2
import mss
from screeninfo import get_monitors
import threading
import queue
import time
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

        self.frame_queue = queue.Queue(maxsize=1)

        self._backend_lock = threading.RLock()
        self._capture_backend = self._selected_backend()
        self._settings_snapshot = self._capture_settings_snapshot()
        self._frame_interval = self._calculate_frame_interval()

        self.bc = None
        self.obs_camera = None
        self.monitor = None
        self.sct = None
        self._circle_mask = None
        self._circle_mask_shape = None

        self.running = True

        if self._capture_backend is None:
            raise SystemExit(1)
        self._setup_backend()

    def _selected_backend(self):
        enabled = []
        if cfg.Bettercam_capture:
            enabled.append("bettercam")
        if cfg.Obs_capture:
            enabled.append("obs")
        if cfg.mss_capture:
            enabled.append("mss")

        if len(enabled) != 1:
            logger.error("[Capture] Enable exactly one capture backend: BetterCam, OBS, or MSS.")
            return None
        return enabled[0]

    def _capture_settings_snapshot(self, backend=None):
        if backend is None:
            backend = self._capture_backend

        return (
            backend,
            cfg.detection_window_width,
            cfg.detection_window_height,
            cfg.capture_fps,
            cfg.bettercam_monitor_id,
            cfg.bettercam_gpu_id,
            cfg.Obs_camera_id,
        )

    def _calculate_frame_interval(self):
        return 1.0 / max(1, int(cfg.capture_fps))

    def _setup_backend(self):
        if self._capture_backend == "bettercam":
            self.setup_bettercam()
        elif self._capture_backend == "obs":
            self.setup_obs()
        elif self._capture_backend == "mss":
            self.setup_mss()

    def _release_backend(self):
        if self.bc is not None:
            try:
                if self.bc.is_capturing:
                    self.bc.stop()
            finally:
                self.bc = None

        if self.obs_camera is not None:
            self.obs_camera.release()
            self.obs_camera = None

        if self.sct is not None:
            self.sct.close()
            self.sct = None

    def setup_bettercam(self):
        import bettercam

        self.bc = bettercam.create(
            device_idx=cfg.bettercam_gpu_id,
            output_idx=cfg.bettercam_monitor_id,
            output_color="BGR",
            max_buffer_len=16,
            region=None
        )
        region = self.calculate_screen_offset(
            custom_region=(self.bc.width, self.bc.height) if len(self._custom_region) == 0 else self._custom_region,
            x_offset=self._offset_x if self._offset_x is not None else 0,
            y_offset=self._offset_y if self._offset_y is not None else 0
        )
        if not self.bc.is_capturing:
            self.bc.start(
                region=region,
                target_fps=cfg.capture_fps
            )

    def setup_obs(self):
        camera_id = self.find_obs_virtual_camera() if cfg.Obs_camera_id == 'auto' else int(cfg.Obs_camera_id) if cfg.Obs_camera_id.isdigit() else None
        if camera_id is None or camera_id < 0:
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
        next_frame_at = time.perf_counter()
        try:
            while self.running:
                frame = self.capture_frame()
                if frame is not None:
                    self._publish_frame(frame)

                if self._capture_backend != "bettercam":
                    next_frame_at = self._sleep_until_next_frame(next_frame_at)
        finally:
            self._release_backend()

    def capture_frame(self):
        with self._backend_lock:
            if self._capture_backend == "bettercam":
                bc = self.bc
            else:
                bc = None

            if self._capture_backend == "obs" and self.obs_camera is not None:
                ret_val, img = self.obs_camera.read()
                return img if ret_val else None

            if self._capture_backend == "mss" and self.monitor is not None:
                if self.sct is None:
                    self.sct = mss.mss()
                screenshot = self.sct.grab(self.monitor)
                img = np.frombuffer(screenshot.bgra, np.uint8).reshape((screenshot.height, screenshot.width, 4))
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if bc is not None:
            try:
                return bc.get_latest_frame()
            except Exception as e:
                if self.running:
                    logger.warning(f"[Capture] BetterCam frame read failed: {e}")

        return None

    def _publish_frame(self, frame):
        try:
            self.frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            self.frame_queue.put_nowait(frame)

    def _sleep_until_next_frame(self, next_frame_at):
        next_frame_at += self._frame_interval
        sleep_for = next_frame_at - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_frame_at = time.perf_counter()
        return next_frame_at

    def get_new_frame(self):
        try:
            return self.frame_queue.get(timeout=1)
        except queue.Empty:
            return None
    
    def restart(self):
        with self._backend_lock:
            new_backend = self._selected_backend()
            if new_backend is None:
                return
            new_snapshot = self._capture_settings_snapshot(new_backend)

            if new_snapshot == self._settings_snapshot:
                return

            self._release_backend()
            self._capture_backend = new_backend
            self._setup_backend()
            self._clear_frame_queue()

            self._settings_snapshot = new_snapshot
            self._frame_interval = self._calculate_frame_interval()
            self.screen_x_center = int(cfg.detection_window_width / 2)
            self.screen_y_center = int(cfg.detection_window_height / 2)

            logger.info('[Capture] Capture reloaded')

    def calculate_screen_offset(self, custom_region=None, x_offset=None, y_offset=None):
        if x_offset is None:
            x_offset = 0
        if y_offset is None:
            y_offset = 0

        if not custom_region:
            screen_width, screen_height = self.get_primary_display_resolution()
        else:
            screen_width, screen_height = custom_region

        width = cfg.detection_window_width
        height = cfg.detection_window_height
        left, top = self._center_region(screen_width, screen_height, width, height, x_offset, y_offset)

        return (left, top, left + width, top + height)

    def _clear_frame_queue(self):
        while True:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                return

    def calculate_mss_offset(self):
        monitor = self.get_primary_display()
        left, top = self._center_region(
            monitor.width,
            monitor.height,
            cfg.detection_window_width,
            cfg.detection_window_height,
            0,
            0,
        )
        left += monitor.x
        top += monitor.y
        return int(left), int(top), int(cfg.detection_window_width), int(cfg.detection_window_height)

    def _center_region(self, screen_width, screen_height, width, height, x_offset, y_offset):
        if width > screen_width or height > screen_height:
            raise ValueError(
                f"[Capture] Detection window {width}x{height} is larger than display {screen_width}x{screen_height}."
            )

        left = int((screen_width - width) / 2 + x_offset)
        top = int((screen_height - height) / 2 - y_offset)

        left = max(0, min(left, screen_width - width))
        top = max(0, min(top, screen_height - height))
        return left, top

    def get_primary_display(self):
        monitors = list(get_monitors())
        if not monitors:
            raise RuntimeError("[Capture] No displays found.")

        return next((m for m in monitors if m.is_primary), monitors[0])

    def get_primary_display_resolution(self):
        monitor = self.get_primary_display()
        return monitor.width, monitor.height
            
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
        shape = (height, width)
        if self._circle_mask is None or self._circle_mask_shape != shape:
            mask = np.zeros(shape, dtype=np.uint8)
            cv2.ellipse(mask, (width // 2, height // 2), (width // 2, height // 2), 0, 0, 360, 255, -1)
            self._circle_mask = mask
            self._circle_mask_shape = shape
        return cv2.bitwise_and(image, image, mask=self._circle_mask)
    
    def Quit(self):
        self.running = False
        with self._backend_lock:
            self._release_backend()
        self.join()


capture = Capture()
capture.start()
