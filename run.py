import math
from logic.config_watcher import Config
cfg = Config()

from ultralytics import YOLO
import torch
import cv2
import time
import win32api
import threading
import queue

from logic.keyboard import *
from logic.capture import *
from logic.mouse import MouseThread
if cfg.mouse_native == False:
    from logic.mouse import ghub_mouse_up, ghub_mouse_down
if cfg.mouse_shoot_by_arduino or cfg.mouse_move_by_arduino:
    from logic.mouse import Arduino

class Targets:
    def __init__(self, x, y, w, h, cls):
        self.mouse_x = x - frames.screen_x_center
        self.mouse_y = (y - frames.screen_y_center) if cls == 7 else (y - frames.screen_y_center - cfg.body_y_offset * h)
        self.distance = math.sqrt((x - frames.screen_x_center)**2 + (y - frames.screen_y_center)**2)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cls = cls

@torch.no_grad()
def init():
    if cfg.show_window and cfg.show_fps:
        prev_frame_time = 0
        new_frame_time = 0
    try:
        model = YOLO('models/{}'.format(cfg.AI_model_path), task='detect')
    except Exception as e:
        print(e)
        quit(0)

    if '.pt' in cfg.AI_model_path:
        print('PT Model loaded.')
    if '.onnx' in cfg.AI_model_path:
        print('Onnx CPU loaded.')
    if '.engine' in cfg.AI_model_path:
        print('Engine loaded')

    print('\033[32mAimbot is started. Enjoy!\033[0m\n[\033[33m' + cfg.hotkey_targeting + '\033[0m] - Aiming at the target\n[\033[33m' + cfg.hotkey_exit + '\033[0m] - EXIT\n[\033[33m' + cfg.hotkey_pause + '\033[0m] - PAUSE AIM\n[\033[33m' + cfg.hotkey_reload_config + '\033[0m] - Reload config')
    
    if cfg.show_window:
        print('An open debug window can affect performance.')
        cv2.namedWindow(cfg.debug_window_name)
        if cfg.debug_window_always_on_top:
            debug_window_hwnd = win32gui.FindWindow(None, cfg.debug_window_name)
            win32gui.SetWindowPos(debug_window_hwnd,win32con.HWND_TOPMOST,100,100,200,200,0)

    clss = []
    if cfg.hideout_targets:
        clss = [0,1,5,6,7]
    if cfg.hideout_targets == False:
        clss = [0,1,7]

    first_frame_init = True
    cfg_reload_prev_state = 0
    shooting_queue = []
    while True:
        app_pause = win32api.GetKeyState(Keyboard.KeyCodes.get(cfg.hotkey_pause))

        app_reload_cfg = win32api.GetKeyState(Keyboard.KeyCodes.get(cfg.hotkey_reload_config))
        if app_reload_cfg != cfg_reload_prev_state:
            if app_reload_cfg == 1 or app_reload_cfg == 0:
                cfg.Read(verbose=True)
                frames.reload_capture()
        cfg_reload_prev_state = app_reload_cfg

        if frame_ready.is_set() and first_frame_init == False:
            image = frames.get_new_frame()
            frame_ready.clear()

        if first_frame_init:
            first_frame_init = False
            image = frames.get_new_frame()

        result = model.predict(
            source=image,
            stream=True,
            cfg='logic/game.yaml',
            imgsz=cfg.AI_image_size,
            stream_buffer=False,
            visualize=False,
            augment=True,
            agnostic_nms=False,
            save=False,
            conf=cfg.AI_conf,
            iou=cfg.AI_iou,
            device=cfg.AI_device,
            half=False,
            max_det=cfg.AI_max_det,
            vid_stride=False,
            classes=clss,
            verbose=False,
            show_boxes=False,
            show_labels=False,
            show_conf=False,
            show=False)
        
        if cfg.show_window:
            height = int(cfg.detection_window_height * cfg.debug_window_scale_percent / 100)
            width = int(cfg.detection_window_width * cfg.debug_window_scale_percent / 100)
            dim = (width, height)
            
            annotated_frame = image

        for frame in result:
            if cfg.show_window and cfg.show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                if app_pause == 0:
                    for box in frame.boxes:
                        cls = int(box.cls.item())
                        if not cfg.disable_headshot:
                            shooting_queue.append(Targets(*box.xywh[0], cls))
                        elif cls in (0, 1, 5, 6):
                            shooting_queue.append(Targets(*box.xywh[0], cls))

                    if not cfg.disable_headshot:
                        shooting_queue.sort(key=lambda x: (x.cls != 7, x.distance))
                    else:
                        shooting_queue.sort(key=lambda x: x.distance, reverse=False)
                    try:
                        target = shooting_queue[0]
                        mouse_worker.queue.put((
                            target.mouse_x,
                            target.mouse_y,
                            target.x,
                            target.y,
                            target.w,
                            target.h,
                            target.distance))
                        if cfg.show_window and cfg.show_target_line:
                            draw_target_line(annotated_frame=annotated_frame, screen_x_center=cfg.detection_window_width / 2, screen_y_center=cfg.detection_window_height / 2, target_x=target.mouse_x + frames.screen_x_center, target_y=target.mouse_y + frames.screen_y_center + cfg.body_y_offset / target.h)
                    except IndexError:
                        mouse_worker.queue.put(None)
                        shooting_queue.clear()
                    shooting_queue.clear()
                else: pass

                if cfg.show_window and cfg.show_boxes:
                    draw_helpers(annotated_frame=annotated_frame, boxes=frame.boxes)
            else:
                mouse_worker.queue.put(None)

        if cfg.show_window and cfg.show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            
            if cfg.show_speed:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(cfg.hotkey_exit)) & 0xFF:
            if cfg.show_window:
                cv2.destroyWindow(cfg.debug_window_name)
            frames.Quit()
            break

        if cfg.show_window:
            try:
                cv2.resizeWindow(cfg.debug_window_name, dim)
            except: exit(0)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(cfg.debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    frame_ready = threading.Event()
    frames = Capture()
    mouse_worker = MouseThread(frame_ready)
    init()