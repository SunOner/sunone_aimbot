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
        
class WorkQueue(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue(maxsize=1)
        self.name = 'WorkQueue'
        self.daemon = True
        self.shooting_queue = []
        self.start()

    def run(self):
        while True:
            item = self.queue.get()
            if item is None:
                self.shooting_queue.clear()
                mouse_worker.queue.put(None)
            else:
                self.process_items(item)
                try:
                    target = self.shooting_queue[0]
                    mouse_worker.queue.put((
                        target.mouse_x,
                        target.mouse_y,
                        target.x,
                        target.y,
                        target.w,
                        target.h,
                        target.distance
                    ))
                except IndexError:
                    pass

    def process_items(self, item):
        self.shooting_queue.clear()
        for box in item:
            cls = int(box.cls.item())
            if not cfg.disable_headshot:
                self.shooting_queue.append(Targets(*box.xywh[0], cls))
            elif cls in (0, 1, 5, 6):
                self.shooting_queue.append(Targets(*box.xywh[0], cls))

        if not cfg.disable_headshot:
            self.shooting_queue.sort(key=lambda x: (x.cls != 7, x.distance))
        else:
            self.shooting_queue.sort(key=lambda x: x.distance, reverse=False)

@torch.no_grad()
def init():
    if cfg.show_window and cfg.show_fps:
        prev_frame_time = 0
        new_frame_time = 0
    try:
        model = YOLO('models/{}'.format(cfg.AI_model_path), task='detect')
    except FileNotFoundError:
        print('Model file not found')
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

    clss = []
    if cfg.show_window:
        clss = range(9)
    if cfg.hideout_targets and cfg.show_window == False:
        clss = [0,1,5,6,7]
    if cfg.hideout_targets == False and cfg.show_window == False:
        clss = [0,1,7]

    first_frame_init = True
    cfg_reload_prev_state = 0

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
                    queue_worker.queue.put(frame.boxes)
                else: pass

                if cfg.show_window and cfg.show_boxes:
                    annotated_frame = draw_helpers(annotated_frame=annotated_frame, boxes=frame.boxes)
            else:
                if app_pause == 0:
                    queue_worker.queue.put(None)

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
    queue_worker = WorkQueue()

    init()