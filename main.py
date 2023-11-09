from ultralytics import YOLO
import numpy as np
import torch
import cv2
import win32gui, win32ui, win32con, win32api
import time
from options import *
from targets import *
from screen import *
from frame import get_new_frame, speed, debug_draw_distance_line
from mouse import win32_raw_mouse_move

# def
players = []
heads = []
bots= []
hideout_target_human = []
hideout_target_balls = []

def Aiming(): # TODO
        shooting_queue = []
        try:
            shooting_queue.append((players[0].x - screen_x_center, players[0].y - screen_y_center - body_y_offset * players[0].h, players[0].distance, players[0].x, players[0].y, players[0].w, players[0].h))
        except: pass
        try:
            shooting_queue.append((bots[0].x - screen_x_center, bots[0].y - screen_y_center - body_y_offset * bots[0].h, bots[0].distance, bots[0].x, bots[0].y, bots[0].w, bots[0].h))
        except: pass
        try:
            if hideout_targets: shooting_queue.append((hideout_target_human[0].x - screen_x_center, hideout_target_human[0].y - screen_y_center - body_y_offset * hideout_target_human[0].h, hideout_target_human[0].distance, hideout_target_human[0].x, hideout_target_human[0].y, hideout_target_human[0].w, hideout_target_human[0].h))
        except: pass
        try:
            if hideout_targets: shooting_queue.append((hideout_target_balls[0].x - screen_x_center, hideout_target_balls[0].y - screen_y_center - body_y_offset * hideout_target_balls[0].h, hideout_target_balls[0].distance, hideout_target_balls[0].x, hideout_target_balls[0].y, hideout_target_balls[0].w, hideout_target_balls[0].h))
        except: pass
        try:
            shooting_queue.append((heads[0].x - screen_x_center, heads[0].y - screen_y_center - head_y_offset * heads[0].h, heads[0].distance, heads[0].x, heads[0].y, heads[0].w, heads[0].h))
        except: pass

        shooting_queue.sort(key=lambda x: x[2], reverse=False)

        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) and mouse_auto_aim == False:
            try: win32_raw_mouse_move(x=int(shooting_queue[0][0]), y=int(shooting_queue[0][1]), target_x=shooting_queue[0][3], target_y=shooting_queue[0][4], target_w=shooting_queue[0][5], target_h=shooting_queue[0][6])
            except: pass
            
        if mouse_auto_aim:
            try:
                win32_raw_mouse_move(x=int(shooting_queue[0][0]), y=int(shooting_queue[0][1]), target_x=shooting_queue[0][3], target_y=shooting_queue[0][4], target_w=shooting_queue[0][5], target_h=shooting_queue[0][6])
            except: pass
        try:
            return (int(shooting_queue[0][0]), int(shooting_queue[0][1]), shooting_queue[0][2])
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

@torch.no_grad()
def init():
    global screen_height, screen_width, players, heads, bots, hideout_target_human, hideout_target_balls

    if show_window and show_fps:
        prev_frame_time = 0
        new_frame_time = 0

    model = YOLO(model_path, task='detect')

    if show_window:
        cv2.namedWindow(debug_window_name)

    while True:
        img = get_new_frame()
        
        result = model(
            img,
            stream=False,
            cfg='game.yaml',
            stream_buffer=True,
            agnostic_nms=False,
            save=False,
            imgsz=320,
            conf=0.35,
            iou=0.2,
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
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                append_targets(frame.boxes.cls, frame.boxes.xywh)
                debug_lines = Aiming()
                annotated_frame = debug_draw_distance_line(annotated_frame, debug_lines)

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
            quit(0)

        if show_window:
            cv2.resizeWindow(debug_window_name, dim)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    init()