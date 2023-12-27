import cv2
import bettercam
import numpy as np
import torch
from logic.config_watcher import *
from run import cfg
import win32gui, win32ui, win32con
from screeninfo import get_monitors

class Capture():
    def __init__(self):
        self.screen_x_center = cfg.detection_window_width / 2
        self.screen_y_center = cfg.detection_window_height / 2

        self.prev_detection_window_width = cfg.detection_window_width
        self.prev_detection_window_height = cfg.detection_window_height
        self.prev_bettercam_capture_fps = cfg.bettercam_capture_fps

        if cfg.Bettercam_capture:
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64)
            if self.bc.is_capturing == False:
                self.bc.start(self.Calculate_screen_offset(), target_fps=cfg.bettercam_capture_fps)
        
        if cfg.Obs_capture:
            self.obs_camera = cv2.VideoCapture(cfg.Obs_camera_id)
            self.obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.detection_window_width)
            self.obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.detection_window_height)
            self.obs_camera.set(cv2.CAP_PROP_FPS, cfg.Obs_capture_fps)
        
    def get_new_frame(self):
        if cfg.Bettercam_capture:
            return self.bc.get_latest_frame()
        
        if cfg.Obs_capture:
            self.ret_val, self.img = self.obs_camera.read()
            return self.img
        
        if cfg.native_Windows_capture:
            return self.windows_native_grab_screen(self.Calculate_screen_offset())
        
    def windows_native_grab_screen(self, region):
        hwin = win32gui.GetDesktopWindow()

        left,top,x2,y2 = region
        width = x2 - left
        height = y2 - top
        
        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
        
        signedIntsArray = bmp.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img
    
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
        
    def check_target_in_scope(self, target_x, target_y, target_w, target_h):
        x = cfg.detection_window_width / 2
        y = cfg.detection_window_height / 2
        x1 = (target_x - target_w)
        x2 = (target_x + target_w)
        y1 = (target_y - target_h)
        y2 = (target_y + target_h)

        if (x > x1 and x < x2 and y > y1 and y < y2) :
            return True
        else :
            return False
    
    def Quit(self):
        if cfg.Bettercam_capture:
            self.bc.stop()

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

    return annotated_frame