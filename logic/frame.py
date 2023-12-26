import threading
import cv2
import dxcam
from logic.screen import *
from logic.config_watcher import *
import time
from run import cfg

dx = None
obs_camera = None

def thread_hook(args):
    if 'DXCamera' in str(args.thread) and 'cannot join current thread' in str(args.exc_value):
        raise 'It looks like the game is currently in fullscreen mode, please switch the game to windowed mode or windowless mode.'

def get_new_frame():
    global dx
    global obs_camera

    threading.excepthook = thread_hook

    if cfg.Dxcam_capture and dx is None:
        if cfg.native_Windows_capture or cfg.Obs_capture:
            print('Use only one capture method!')
            exit(0)
        if dx is None:
            dx = dxcam.create(device_idx=cfg.dxcam_monitor_id, output_idx=cfg.dxcam_gpu_id, output_color="BGR", max_buffer_len=cfg.dxcam_max_buffer_len)
        if dx.is_capturing == False:
            dx.start(Calculate_screen_offset(), target_fps=cfg.dxcam_capture_fps)
    if cfg.Dxcam_capture and dx is not None:
        img = dx.get_latest_frame()

    if cfg.Obs_capture and obs_camera is None:
        if cfg.Dxcam_capture or cfg.native_Windows_capture:
            print('Use only one capture method!')
            exit(0)
        obs_camera = cv2.VideoCapture(cfg.Obs_camera_id)
        obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, detection_window_width)
        obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, detection_window_height)
        obs_camera.set(cv2.CAP_PROP_FPS, cfg.Obs_capture_fps)
    if cfg.Obs_capture and obs_camera is not None:
        ret_val, img = obs_camera.read()
        
    if cfg.native_Windows_capture:
        if cfg.Obs_capture or cfg.Dxcam_capture:
            print('Use only one capture method!')
            exit(0)
        img = windows_grab_screen(Calculate_screen_offset())

    return img

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