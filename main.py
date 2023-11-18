from ultralytics import YOLO
import torch
import cv2
import time
import win32con, win32api
import asyncio
from options import *
from targets import *
from screen import *
from frame import get_new_frame, speed
from mouse import win32_raw_mouse_move

def append_targets(boxes):
    shooting_queue = []
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
    
    if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) and mouse_auto_aim == False:
            try: asyncio.run(win32_raw_mouse_move(x=int(shooting_queue[0].mouse_x), y=int(shooting_queue[0].mouse_y), target_x=shooting_queue[0].x, target_y=shooting_queue[0].y, target_w=shooting_queue[0].w, target_h=shooting_queue[0].h))
            except: pass
            
    if mouse_auto_shoot == True and mouse_auto_aim == False:
        asyncio.run(win32_raw_mouse_move(x=None, y=None, target_x=shooting_queue[0].x, target_y=shooting_queue[0].y, target_w=shooting_queue[0].w, target_h=shooting_queue[0].h))
    if mouse_auto_aim:
        try:
            asyncio.run(win32_raw_mouse_move(x=int(shooting_queue[0].mouse_x), y=int(shooting_queue[0].mouse_y), target_x=shooting_queue[0].x, target_y=shooting_queue[0].y, target_w=shooting_queue[0].w, target_h=shooting_queue[0].h))
        except: pass

@torch.no_grad()
def init():
    global screen_height, screen_width

    if show_window and show_fps:
        prev_frame_time = 0
        new_frame_time = 0

    model = YOLO(AI_model_path, task='detect')

    if show_window:
        cv2.namedWindow(debug_window_name)

    while True:
        img = get_new_frame()
        
        result = model(
            img,
            stream=False,
            cfg='game.yaml',
            imgsz=AI_image_size,
            stream_buffer=True,
            agnostic_nms=False,
            save=False,
            conf=AI_conf,
            iou=AI_iou,
            device=AI_device,
            show=False,
            boxes=False,
            half=AI_half,
            max_det=AI_max_det,
            vid_stride=False,
            classes=range(9),
            verbose=AI_verbose,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(img.shape[0] * debug_window_scale_percent / 100)
            width = int(img.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)

            annotated_frame = result[0].plot()

        for frame in result:
            if show_window and show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                append_targets(frame.boxes)

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