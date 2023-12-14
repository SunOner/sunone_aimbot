import asyncio
from ultralytics import YOLO
import torch
import cv2
import time
import win32con, win32api
import threading
import queue
import time
from logic.targets import *

from logic.screen import *
from logic.frame import get_new_frame, speed, draw_helpers
from logic.mouse import win32_raw_mouse_move
from logic.config_watcher import *
if mouse_move_by_arduino or mouse_shoot_by_arduino:
    from logic.mouse import arduino


class work_queue(threading.Thread):
    def __init__(self):
        super(work_queue, self).__init__()
        self.queue = queue.Queue()
        self.daemon = True
        self.queue.maxsize = 100
        self.start()

    def run(self):
        while True:
            # https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
            shooting_key = win32api.GetAsyncKeyState(win32con.VK_RBUTTON)

            item = self.queue.get()

            x, y, target_x, target_y, target_w, target_h, distance = item

            # By key pressed
            if shooting_key == -32768 and mouse_auto_aim == False:
                asyncio.run(win32_raw_mouse_move(x=x, y=y, target_x=target_x, target_y=target_y, target_w=target_w, target_h=target_h, distance=distance))
                if mouse_shoot_by_arduino:
                    arduino.press()
            else:
                if mouse_shoot_by_arduino and shooting_key == 0:
                    arduino.release()
            # Auto shoot
            if mouse_auto_shoot == True and mouse_auto_aim == False:
                asyncio.run(win32_raw_mouse_move(x=None, y=None, target_x=target_x, target_y=target_y, target_w=target_w, target_h=target_h, distance=distance))

            # Auto AIM
            if mouse_auto_aim:
                try:
                    asyncio.run(win32_raw_mouse_move(x=x, y=y, target_x=target_x, target_y=target_y, target_w=target_w, target_h=target_h, distance=distance))
                except: pass

def append_queue(boxes, queue_worker):
    shooting_queue = []

    if disable_headshot == False:
        head_target = False
        for box in boxes:
            shooting_queue.append(Targets(x=box.xywh[0][0].item(), y=box.xywh[0][1].item(), w=box.xywh[0][2].item(), h=box.xywh[0][3].item(), cls=int(box.cls.item())))
        for x in shooting_queue:
            if len(shooting_queue) >= 3:
                head_target = False
                break
            if x.cls == 7:
                head_target = True
            else:
                head_target = False
        if head_target:
            shooting_queue.sort(key=lambda x: x.cls == 7, reverse=True)
        else:
            shooting_queue.sort(key=lambda x: x.distance, reverse=False)
    else:
        for box in boxes:
            if int(box.cls.item()) == 0 or int(box.cls.item()) == 1 or int(box.cls.item()) == 5 or int(box.cls.item()) == 6:
                shooting_queue.append(Targets(x=box.xywh[0][0].item(), y=box.xywh[0][1].item(), w=box.xywh[0][2].item(), h=box.xywh[0][3].item(), cls=int(box.cls.item())))
        shooting_queue.sort(key=lambda x: x.distance, reverse=False)

    try:
        queue_worker.queue.put((shooting_queue[0].mouse_x, shooting_queue[0].mouse_y, shooting_queue[0].x, shooting_queue[0].y, shooting_queue[0].w, shooting_queue[0].h, shooting_queue[0].distance))
    except:
        pass

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

    print('Aimbot is started. Enjoy!\n[Right mouse button] - Aiming at the target\n[F2] - EXIT\n[F3] - PAUSE AIM')
    
    if show_window:
        print('An open debug window can affect performance.')
        cv2.namedWindow(debug_window_name)
    
    queue_worker = work_queue()
    queue_worker.name = 'work_queue_thread'

    clss = []
    if show_window:
        clss = range(9)
    if hideout_targets and show_window == False:
        clss = [0,1,5,6,7]
    if hideout_targets == False and show_window == False:
        clss = [0,1,7]

    while True:
        frame = get_new_frame()

        app_pause = win32api.GetKeyState(win32con.VK_F3)
        
        result = model.predict(
            source=frame,
            stream=True,
            cfg='logic/game.yaml',
            imgsz=AI_image_size,
            stream_buffer=False,
            agnostic_nms=False,
            save=False,
            conf=AI_conf,
            iou=AI_iou,
            device=AI_device,
            half=True,
            max_det=AI_max_det,
            vid_stride=False,
            classes=clss,
            verbose=False,
            show_boxes=False,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(frame.shape[0] * debug_window_scale_percent / 100)
            width = int(frame.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)
            
            annotated_frame = frame

        for frame in result:
            if show_window and show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                if app_pause == 0:
                    append_queue(frame.boxes, queue_worker)
                else: pass

                if show_window and show_boxes:
                    annotated_frame = draw_helpers(annotated_frame=annotated_frame, boxes=frame.boxes)

        if show_window and show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            if show_speed:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if win32api.GetAsyncKeyState(win32con.VK_F2) & 0xFF:
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
    init()