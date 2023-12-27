import cv2
import bettercam
from logic.screen import *
from logic.config_watcher import *
from run import cfg
import time

class Capture():
    def __init__(self):
        self.prev_detection_window_width = cfg.detection_window_width
        self.prev_detection_window_height = cfg.detection_window_height

        if cfg.Bettercam_capture:
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64)
            if self.bc.is_capturing == False:
                self.bc.start(Calculate_screen_offset(), target_fps=cfg.bettercam_capture_fps)
        
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
            return windows_grab_screen(Calculate_screen_offset())
        
    def reload_capture(self):
        if cfg.Bettercam_capture and self.prev_detection_window_height != cfg.detection_window_height or cfg.Bettercam_capture and self.prev_detection_window_width != cfg.detection_window_width:
            self.bc.stop()
            del self.bc
            self.bc = bettercam.create(device_idx=cfg.bettercam_monitor_id, output_idx=cfg.bettercam_gpu_id, output_color="BGR", max_buffer_len=64)
            self.bc.start(Calculate_screen_offset(), target_fps=cfg.bettercam_capture_fps)
            print('Capture reloaded')
            self.prev_detection_window_width = cfg.detection_window_width
            self.prev_detection_window_height = cfg.detection_window_height

def speed(annotated_frame, speed_preprocess, speed_inference, speed_postprocess):
    cv2.putText(annotated_frame, 'preprocess: {:.2f}'.format(speed_preprocess), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'inference: {:.2f}'.format(speed_inference), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'postprocess: {:.2f}'.format(speed_postprocess), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    return annotated_frame

def draw_helpers(annotated_frame, boxes):
    for item in boxes:
        if item is not None:
            for xyxy in item.xyxy:
                if cfg.show_boxes:
                    cv2.rectangle(annotated_frame, (int(xyxy[0].item()), int(xyxy[1].item())), (int(xyxy[2].item()), int(xyxy[3].item())), (0, 200, 0), 2)
                    if cfg.show_labels:
                        str_cls = ''
                        for cls in item.cls:
                            match cls:
                                case 0:
                                    str_cls = 'player'
                                case 1:
                                    str_cls = 'bot'
                                case 2:
                                    str_cls = 'weapon'
                                case 3:
                                    str_cls = 'outline'
                                case 4:
                                    str_cls = 'dead_body'
                                case 5:
                                    str_cls = 'hideout_target_human'
                                case 6:
                                    str_cls = 'hideout_target_balls'
                                case 7:
                                    str_cls = 'head'
                                case 8:
                                    str_cls = 'smoke'
                                case 9:
                                    str_cls = 'fire'
                            if cfg.show_conf == False:
                                cv2.putText(annotated_frame, str_cls, (int(xyxy[0].item()), int(xyxy[1].item() - 5)), cv2.FONT_HERSHEY_SIMPLEX , 1, (0, 200, 0), 1, cv2.LINE_AA)
                    if cfg.show_conf:
                        for conf in item.conf:
                            cv2.putText(annotated_frame, str('{} {:.2f}'.format(str_cls,conf.item())), (int(xyxy[0].item()), int(xyxy[1].item() - 5)), cv2.FONT_HERSHEY_SIMPLEX , 1, (0, 200, 0), 1, cv2.LINE_AA)
    return annotated_frame