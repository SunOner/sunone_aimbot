from ultralytics import YOLO
import numpy as np
import torch
import cv2
import win32gui, win32ui, win32con, win32api
from options import *
from targets import *
import time
import dxcam
import asyncio
import tensorrt as trt
from cuda import cuda, cudart

def check_target_in_scope(distance): # TODO
    distance = distance * (head_y_offset + body_y_offset / 2)

    if distance <= 25:
        return True
    else:
        return False

def win32_raw_mouse_move(x, y, dst=None):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

    bDst = check_target_in_scope(dst)

    if mouse_auto_shoot and bDst:
        asyncio.run(win32_raw_mouse_click(x=x, y=y))
        
    if mouse_auto_shoot and bDst:
        asyncio.run(win32_raw_mouse_click(x=x, y=y))

async def win32_raw_mouse_click(x, y):
    if mouse_auto_shoot_timer:
        await asyncio.sleep(mouse_auto_shoot_sleep_time)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

def Aiming(): # TODO
        shooting_queue = []
        try:
            shooting_queue.append((players[0].x - screen_x_center, players[0].y - screen_y_center - body_y_offset * players[0].h, players[0].distance))
        except: pass
        try:
            shooting_queue.append((bots[0].x - screen_x_center, bots[0].y - screen_y_center - body_y_offset * bots[0].h, bots[0].distance))
        except: pass
        try:
            if hideout_targets: shooting_queue.append((hideout_target_human[0].x - screen_x_center, hideout_target_human[0].y - screen_y_center - body_y_offset * hideout_target_human[0].h, hideout_target_human[0].distance))
        except: pass
        try:
            if hideout_targets: shooting_queue.append((hideout_target_balls[0].x - screen_x_center, hideout_target_balls[0].y - screen_y_center - body_y_offset * hideout_target_balls[0].h, hideout_target_balls[0].distance))
        except: pass
        try:
            shooting_queue.append((heads[0].x - screen_x_center, heads[0].y - screen_y_center - body_y_offset * heads[0].h, heads[0].distance))
        except: pass

        shooting_queue.sort(key=lambda x: x[2], reverse=False)

        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) and mouse_auto_aim == False:
            try: win32_raw_mouse_move(x=int(shooting_queue[0][0]), y=int(shooting_queue[0][1]), dst=shooting_queue[0][2])
            except: pass
            
        if mouse_auto_aim:
            win32_raw_mouse_move(x=int(shooting_queue[0][0]), y=int(shooting_queue[0][1]), dst=shooting_queue[0][2])
        try:
            if show_window: return (shooting_queue[0][0], shooting_queue[0][1])
        except: pass

def append_targets(clss, xywhs):
    player_i = 0
    head_i = 0
    bot_i = 0
    hideout_target_human_i = 0
    hideout_target_balls_i = 0

    for cls_num in clss:
        cls = int(cls_num.item())
        match cls:
            case 0:
                players.append(Player(x=xywhs[player_i][0].item(), y=xywhs[player_i][1].item(), w=xywhs[player_i][2].item(), h=xywhs[player_i][3].item()))
                player_i = player_i + 1
            case 1:
                bots.append(Bot(x=xywhs[bot_i][0].item(), y=xywhs[bot_i][1].item(), w=xywhs[bot_i][2].item(), h=xywhs[bot_i][3].item()))
                bot_i = bot_i + 1
            case 5:
                if hideout_targets: hideout_target_human.append(Hideout_target_human(x=xywhs[hideout_target_human_i][0].item(), y=xywhs[hideout_target_human_i][1].item(), w=xywhs[hideout_target_human_i][2].item(), h=xywhs[hideout_target_human_i][3].item()))
                if hideout_targets: hideout_target_human_i = hideout_target_human_i + 1
            case 6:
                if hideout_targets: hideout_target_balls.append(Hideout_target_balls(x=xywhs[hideout_target_balls_i][0].item(), y=xywhs[hideout_target_balls_i][1].item(), w=xywhs[hideout_target_balls_i][2].item(), h=xywhs[hideout_target_balls_i][3].item()))
                if hideout_targets: hideout_target_balls_i = hideout_target_balls_i + 1
            case 7:
                heads.append(Hideout_target_balls(x=xywhs[head_i][0].item(), y=xywhs[head_i][1].item(), w=xywhs[head_i][2].item(), h=xywhs[head_i][3].item()))
                head_i = head_i + 1

    players.sort(key=lambda x: x.distance, reverse=False)
    bots.sort(key=lambda x: x.distance, reverse=False)
    if hideout_targets: hideout_target_human.sort(key=lambda x: x.distance, reverse=False)
    if hideout_targets: hideout_target_balls.sort(key=lambda x: x.distance, reverse=False)
    heads.sort(key=lambda x: x.distance, reverse=False)

region = Calculate_screen_offset()

if Dxcam_capture:
    dx = dxcam.create(device_idx=dxcam_monitor_id, output_idx=dxcam_gpu_id, output_color="BGR", max_buffer_len=dxcam_max_buffer_len)

screen_x_center, screen_y_center = screen_width / 2, screen_height / 2

if Windows_capture:
    def windows_grab_screen(region):
        hwin = win32gui.FindWindow("aboba", None)
        left, top, x2, y2 = region
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
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img

@torch.no_grad()
def init():
    global screen_height
    global screen_width
    global players
    global heads
    global bots
    global hideout_target_human
    global hideout_target_balls
    
    if Dxcam_capture:
        dx.start(region, target_fps=dxcam_capture_fps)
    if Obs_capture:
        obs_camera = cv2.VideoCapture(Obs_camera_id)
        obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
        obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)

    avg_postprocess_speed, avg_count, avg_last = 0, 0, 0

    if show_window and show_fps:
        prev_frame_time = 0
        new_frame_time = 0

    model = YOLO(model_path, task='detect')

    if show_window:
        cv2.namedWindow(debug_window_name)

    while True:
        if Dxcam_capture:
            img = dx.get_latest_frame()
        if Obs_capture:
            ret_val, img = obs_camera.read()
        if Windows_capture:
            img = windows_grab_screen(region)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        result = model(
            img,
            stream=False,
            cfg='game.yaml',
            stream_buffer=True,
            agnostic_nms=False,
            save=False,
            imgsz=640,
            conf=0.35,
            iou=0.001,
            device=0,
            show=False,
            boxes=False,
            half=True,
            max_det=20,
            vid_stride=False,
            classes=range(9),
            verbose=False,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(img.shape[0] * debug_window_scale_percent / 100)
            width = int(img.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)
            annotated_frame = result[0].plot()
        
        for frame in result: # current frame
            if show_window and show_speed == True:
                speed_preprocess, speed_inference, speed_postprocess = frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess']
                cv2.putText(annotated_frame, 'preprocess:', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_preprocess), (150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'inference:', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_inference), (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'postprocess:', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_postprocess), (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'avg_postprocess_speed:', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(avg_last), (240, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                if avg_count <= 60:
                    avg_postprocess_speed = avg_postprocess_speed + speed_postprocess
                    avg_count = avg_count + 1
                if avg_count >= 60:
                    avg_postprocess_speed = avg_postprocess_speed / 60
                    avg_last = avg_postprocess_speed
                    avg_count = 0
                    avg_postprocess_speed = 0

            if len(frame.boxes):
                append_targets(frame.boxes.cls, frame.boxes.xywh)
                debug_lines = Aiming()

                try:
                    if show_window: cv2.line(annotated_frame, (int(screen_x_center), int(screen_y_center)), (int(screen_x_center) + int(debug_lines[0]), int(screen_y_center) + int(debug_lines[1])), (255, 0, 0), 2)
                except:
                    pass

                players = []
                heads = []
                bots= []
                hideout_target_human = []
                hideout_target_balls = []
                
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
                if Dxcam_capture:
                    dx.stop()
            quit(0)

        if show_window:
            cv2.resizeWindow(debug_window_name, dim)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    init()