import asyncio
from ultralytics import YOLO
import torch
import cv2
import time
import win32con, win32api
import threading
import queue
import time
from options import *
from targets import *
from screen import *
from frame import get_new_frame, speed, draw_helpers
from mouse import win32_raw_mouse_move

class work_queue(threading.Thread):
    def __init__(self):
        super(work_queue, self).__init__()
        self.queue = queue.Queue()
        self.daemon = True
        self.queue.maxsize = AI_max_det
        self.start()

    def run(self):
        while True:
            item = self.queue.get()

            if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) and mouse_auto_aim == False:
                asyncio.run(win32_raw_mouse_move(x=item[0], y=item[1], target_x=item[2], target_y=item[3], target_w=item[4], target_h=item[5], distance=item[6]))

            if mouse_auto_shoot == True and mouse_auto_aim == False:
                asyncio.run(win32_raw_mouse_move(x=None, y=None, target_x=item[2], target_y=item[3], target_w=item[4], target_h=item[5], distance=item[6]))
    
            if mouse_auto_aim:
                try:
                    asyncio.run(win32_raw_mouse_move(x=item[0], y=item[1], target_x=item[2], target_y=item[3], target_w=item[4], target_h=item[5], distance=item[6]))
                except: pass
                
            self.queue.task_done()

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
        model = YOLO(AI_model_path, task='detect')
    except FileNotFoundError:
        print('Model file not found')
        quit(0)

    if '.engine' in AI_model_path:
        print('Engine loaded')
    if '.onnx' in AI_model_path:
        print('Onnx CPU loaded.')
    if '.pt' in AI_model_path:
        print('Model loaded.', model.info(detailed=False, verbose=False))

    print('Aimbot is started. Enjoy!\n[Right mouse button] - Aiming at the target\n[F2] - EXIT')
    
    if show_window:
        print('An open debug window can affect performance.')
        cv2.namedWindow(debug_window_name)
    
    queue_worker = work_queue()
    queue_worker.name = 'Work_queue_thread'

    while True:
        frame = get_new_frame()
        
        result = model.predict(
            source=frame,
            stream=True,
            cfg='game.yaml',
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
            classes=range(9),
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
                append_queue(frame.boxes, queue_worker)

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

        if win32api.GetAsyncKeyState(win32con.VK_F2):
            if show_window:
                cv2.destroyWindow(debug_window_name)
            quit(0)

        if show_window:
            cv2.resizeWindow(debug_window_name, dim)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    init()