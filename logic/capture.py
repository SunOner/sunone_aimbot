import cv2
import bettercam
import numpy as np
import torch
import win32gui, win32ui, win32con
from logic.config_watcher import *
from run import cfg
from screeninfo import get_monitors

class Capture():
    def __init__(self):
        self.Warnings()
        self.screen_x_center = cfg.detection_window_width / 2
        self.screen_y_center = cfg.detection_window_height / 2

        self.prev_detection_window_width = cfg.detection_window_width
        self.prev_detection_window_height = cfg.detection_window_height
        self.prev_bettercam_capture_fps = cfg.bettercam_capture_fps

        if cfg.Bettercam_capture:
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64, region=self.Calculate_screen_offset())
            if self.bc.is_capturing == False:
                self.bc.start(self.Calculate_screen_offset(), target_fps=cfg.bettercam_capture_fps)
        
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
    
    def reload_capture(self):
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
            
    def Calculate_screen_offset(self):
        left, top = self.get_primary_display_resolution()
        left = left / 2 - cfg.detection_window_width / 2
        top = top / 2 - cfg.detection_window_height / 2
        width = left + cfg.detection_window_width
        height = top + cfg.detection_window_height
        return (int(left), int(top), int(width), int(height))
    
    def get_primary_display_resolution(self):
        _ = get_monitors()
        for m in _:
            if m.is_primary:
                return m.width, m.height
            
    def find_obs_virtual_camera(self):
        max_tested = 10
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
    
    def Warnings(self):
        # FATAL ERRORS
        if torch.cuda.is_available == False:
            print('`Torch` is installed without CUDA support.')
            exit(0)
        if cfg.AI_device.lower == 'cpu':
            print('CPU is not supported, please select Nvidia GPU device.\nExample: AI_device=0')
            exit(0)
        if cfg.Bettercam_capture == False and cfg.Obs_capture == False:
            print('Use at least one image capture method.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
            exit(0)
        if cfg.Bettercam_capture and cfg.Obs_capture:
            print('Only one capture method is possible.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
            exit(0)
        # WARNINGS
        if '.pt' in cfg.AI_model_path:
            print('WARNING: Export the model to `.engine` for better performance.')
        if cfg.mouse_native and cfg.mouse_move_by_arduino == False and cfg.mouse_shoot_by_arduino == False:
            print('WARNING: win32api is detected in some games.')
        if cfg.mouse_native == False and cfg.mouse_move_by_arduino == False and cfg.mouse_shoot_by_arduino == False:
            print('WARNING: ghub_mouse.dll is detected in some games.')
        if cfg.show_window:
            print('WARNING: An open debug window can affect performance.')
        if cfg.debug_window_name == 'Calculator' and cfg.show_window:
            print('WARNING: For more security, change the name of the debug window. `debug_window_name` option.')
        if cfg.show_overlay_detector:
            print('WARNING: An activated overlay may affect performance, not work properly in some games, and may also be visible as an anti-cheat in some games.')
        if cfg.bettercam_capture_fps >= 90:
            print('WARNING: A large number of frames per second can affect the behavior of automatic aiming. (Shaking).')
        if cfg.detection_window_width >= 700:
            print('WARNING: The object detector window is more than 700 pixels wide, and a large object detector window can have a bad effect on performance.')
        if cfg.detection_window_height >= 700:
            print('WARNING: The object detector window is more than 700 pixels in height, a large object detector window can have a bad effect on performance.')
        if cfg.mouse_move_by_arduino == False:
            print('WARNING: Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.mouse_shoot_by_arduino == False and cfg.mouse_auto_shoot:
            print('WARNING: Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.AI_conf <= 0.15:
            print('WARNING: A small value of `AI_conf ` can lead to a large number of false positives.')
            
    def Quit(self):
        if cfg.Bettercam_capture and self.bc.is_capturing:
            self.bc.stop()

def draw_target_line(annotated_frame, screen_x_center, screen_y_center, target_x, target_y):
    cv2.line(annotated_frame, (int(screen_x_center), int(screen_y_center)), (int(target_x), int(target_y)), (0, 255, 255), 2)

def speed(annotated_frame, speed_preprocess, speed_inference, speed_postprocess):
    cv2.putText(annotated_frame, 'preprocess: {:.2f}'.format(speed_preprocess), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'inference: {:.2f}'.format(speed_inference), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'postprocess: {:.2f}'.format(speed_postprocess), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    return annotated_frame

def draw_helpers(annotated_frame, boxes):
    class_labels = {
        0: 'player',
        1: 'bot',
        2: 'weapon',
        3: 'outline',
        4: 'dead_body',
        5: 'hideout_target_human',
        6: 'hideout_target_balls',
        7: 'head',
        8: 'smoke',
        9: 'fire'
    }

    if cfg.show_boxes: 
        for item in boxes:
            if item is None:
                continue
            for xyxy, cls, conf in zip(item.xyxy, item.cls, item.conf):
                x0, y0, x1, y1 = map(int, map(torch.Tensor.item, xyxy))
                cv2.rectangle(annotated_frame, (x0, y0), (x1, y1), (0, 200, 0), 2)
                str_cls = class_labels.get(cls.item(), '')
                if cfg.show_labels and not cfg.show_conf:
                    cv2.putText(annotated_frame, str_cls, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
                if cfg.show_conf:
                    text = '{} {:.2f}'.format(str_cls, conf.item())
                    cv2.putText(annotated_frame, text, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)