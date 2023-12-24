from logic.config_watcher import *
from ultralytics import YOLO
import torch
import cv2
import time
import win32con, win32api
import threading
import queue

from logic.targets import *
from logic.keyboard import *
from logic.screen import *
from logic.frame import get_new_frame, speed, draw_helpers
from logic.mouse import MouseThread

if mouse_native == False:
    from logic.mouse import ghub_mouse_up, ghub_mouse_down
if mouse_shoot_by_arduino or mouse_move_by_arduino:
    from logic.mouse import Arduino

class work_queue(threading.Thread):
    def __init__(self):
        super(work_queue, self).__init__()
        self.queue = queue.Queue()
        self.daemon = True
        self.maxsize = 1
        self.name = 'work_queue'
        self.shooting_queue = []
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.target_w = 0
        self.target_h = 0
        self.distance = 0
        self.start()

    def run(self):
        while True:
            item = self.queue.get()
            if item == None:
                self.shooting_queue = []
                mouse_worker.queue.put(None)
            if item != None:
                if disable_headshot == False:
                    head_target = False
                    for box in item:
                        self.shooting_queue.append(Targets(x=box.xywh[0][0].item(), y=box.xywh[0][1].item(), w=box.xywh[0][2].item(), h=box.xywh[0][3].item(), cls=int(box.cls.item())))
                    for x in self.shooting_queue:
                        if len(self.shooting_queue) >= 3:
                            head_target = False
                            break
                        if x.cls == 7:
                            head_target = True
                        else:
                            head_target = False
                    if head_target:
                        self.shooting_queue.sort(key=lambda x: x.cls == 7, reverse=True)
                    else:
                        self.shooting_queue.sort(key=lambda x: x.distance, reverse=False)
                else:
                    for box in item:
                        if int(box.cls.item()) == 0 or int(box.cls.item()) == 1 or int(box.cls.item()) == 5 or int(box.cls.item()) == 6:
                            self.shooting_queue.append(Targets(x=box.xywh[0][0].item(), y=box.xywh[0][1].item(), w=box.xywh[0][2].item(), h=box.xywh[0][3].item(), cls=int(box.cls.item())))
                    self.shooting_queue.sort(key=lambda x: x.distance, reverse=False)
                try:
                    self.x = self.shooting_queue[0].mouse_x
                    self.y = self.shooting_queue[0].mouse_y
                    self.target_x = self.shooting_queue[0].x
                    self.target_y = self.shooting_queue[0].y
                    self.target_w = self.shooting_queue[0].w
                    self.target_h = self.shooting_queue[0].h
                    self.distance = self.shooting_queue[0].distance
                    self.shooting_queue = []
                except:
                    pass

                mouse_worker.queue.put((self.x, self.y, self.target_x, self.target_y, self.target_w, self.target_h, self.distance))

@torch.no_grad()
def init():
    if show_window and show_fps:
        prev_frame_time = 0
        new_frame_time = 0
    try:
        model = YOLO('models/{}'.format(AI_model_path), task='detect')
    except FileNotFoundError:
        print('Model file not found')
        quit(0)

    if '.pt' in AI_model_path:
        print('PT Model loaded.')
    if '.onnx' in AI_model_path:
        print('Onnx CPU loaded.')
    if '.engine' in AI_model_path:
        print('Engine loaded')

    print('\033[32mAimbot is started. Enjoy!\033[0m\n[\033[33m' + hotkey_targeting + '\033[0m] - Aiming at the target\n[\033[33m' + hotkey_exit + '\033[0m] - EXIT\n[\033[33m' + hotkey_pause + '\033[0m] - PAUSE AIM')
    
    if show_window:
        print('An open debug window can affect performance.')
        cv2.namedWindow(debug_window_name)

    clss = []
    if show_window:
        clss = range(9)
    if hideout_targets and show_window == False:
        clss = [0,1,5,6,7]
    if hideout_targets == False and show_window == False:
        clss = [0,1,7]

    first_frame_init = True
    while True:
        app_pause = win32api.GetKeyState(Keyboard.KeyCodes.get(hotkey_pause))

        if frame_ready.is_set() and first_frame_init == False:
            image = get_new_frame()
            frame_ready.clear()

        if first_frame_init:
            first_frame_init = False
            image = get_new_frame()

        result = model.predict(
            source=image,
            stream=True,
            cfg='logic/game.yaml',
            imgsz=AI_image_size,
            stream_buffer=False,
            agnostic_nms=False,
            save=False,
            conf=AI_conf,
            iou=AI_iou,
            device=AI_device,
            half=False,
            max_det=AI_max_det,
            vid_stride=False,
            classes=clss,
            verbose=False,
            show_boxes=False,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(detection_window_height * debug_window_scale_percent / 100)
            width = int(detection_window_width * debug_window_scale_percent / 100)
            dim = (width, height)
            
            annotated_frame = image

        for frame in result:
            if show_window and show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                if app_pause == 0:
                    queue_worker.queue.put(frame.boxes)
                else: pass

                if show_window and show_boxes:
                    annotated_frame = draw_helpers(annotated_frame=annotated_frame, boxes=frame.boxes)
            else:
                if app_pause == 0:
                    queue_worker.queue.put(None)

        if show_window and show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            
            if show_speed:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if win32api.GetAsyncKeyState(Keyboard.KeyCodes.get(hotkey_exit)) & 0xFF:
            if show_window:
                cv2.destroyWindow(debug_window_name)
            break

        if show_window:
            try:
                cv2.resizeWindow(debug_window_name, dim)
            except: exit(0)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    frame_ready = threading.Event()
    mouse_worker = MouseThread(frame_ready)
    queue_worker = work_queue()
    init()