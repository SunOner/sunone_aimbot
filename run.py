from ultralytics import YOLO
import math
import torch
import cv2
from typing import List
import win32api

from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.mouse import mouse
from logic.buttons import Buttons
    
mask_points = []
annotated_frame = None

class Target():
    def __init__(self, x, y, w, h, cls):
        self.x = x
        self.y = y if cls == 7 else (y - cfg.body_y_offset * h)
        self.w = w
        self.h = h
        self.distance = math.sqrt((x - capture.screen_x_center)**2 + (y - capture.screen_y_center)**2)
        self.cls = cls

@torch.no_grad()
def perform_detection(model, image, clss):
    return model.predict(
        source=image,
        stream=True,
        cfg='logic/game.yaml',
        imgsz=cfg.AI_image_size,
        stream_buffer=False,
        visualize=False,
        augment=False,
        agnostic_nms=False,
        save=False,
        conf=cfg.AI_conf,
        iou=0.3,
        device=cfg.AI_device,
        half=False if 'cpu' in cfg.AI_device else True,
        max_det=25,
        vid_stride=False,
        classes=clss,
        verbose=False,
        show_boxes=False,
        show_labels=False,
        show_conf=False,
        show=False)

def print_startup_messages():
    version = 0
    try:
        with open('./version', 'r') as f:
            lines = f.read().split('\n')
            version = lines[0].split('=')[1]
    except:
        print('(version file is not found)')

    print(f'Yolov8 Aimbot is started! (Version {version})\n\n',
            'Hotkeys:\n',
            f'[{cfg.hotkey_targeting}] - Aiming at the target\n',
            f'[{cfg.hotkey_exit}] - EXIT\n',
            f'[{cfg.hotkey_pause}] - PAUSE AIM\n',
            f'[{cfg.hotkey_reload_config}] - Reload config\n')
    
def process_hotkeys(cfg_reload_prev_state):
    global app_pause
    global clss
    app_pause = win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_pause])
    app_reload_cfg = win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_reload_config])
    
    if app_reload_cfg != cfg_reload_prev_state:
        if app_reload_cfg in (1, 0):
            cfg.Read(verbose=True)
            capture.reload_capture()
            mouse.Update_settings()
            clss = active_classes()
            if cfg.show_window == False:
                cv2.destroyAllWindows()
                
    cfg_reload_prev_state = app_reload_cfg
    return cfg_reload_prev_state

def sort_targets(frame, cfg, arch) -> List[Target]:
    boxes_array = frame.boxes.xywh.to(arch)
    distances_sq = torch.sum((boxes_array[:, :2] - torch.tensor([capture.screen_x_center, capture.screen_y_center], device=arch)) ** 2, dim=1)
    classes_tensor = frame.boxes.cls.to(arch)

    if not cfg.disable_headshot:
        score = distances_sq + 10000 * (classes_tensor != 7).float()
        sort_indices = torch.argsort(score).cpu().numpy()
    else:
        heads = torch.nonzero(classes_tensor == 7, as_tuple=False).squeeze(1)
        other = torch.nonzero(classes_tensor != 7, as_tuple=False).squeeze(1)

        if len(heads) > 0:
            heads_distances_sq = distances_sq[heads]
            sort_heads = torch.argsort(heads_distances_sq)
            heads = heads[sort_heads]
        else:
            sort_heads = torch.tensor([], dtype=torch.int64, device=arch)

        other_distances_sq = distances_sq[other]
        sort_indices_other = torch.argsort(other_distances_sq)

        sort_indices = torch.cat((heads, other[sort_indices_other])).cpu().numpy()
        
    return [Target(*boxes_array[i, :4].cpu().numpy(), classes_tensor[i].item()) for i in sort_indices]

def active_classes() -> List[int]:
    clss = [0, 1]
    
    if cfg.hideout_targets:
        clss.extend([5, 6])

    if not cfg.disable_headshot:
        clss.append(7)
    
    return clss

def init():
    cfg_reload_prev_state = 0
    shooting_queue = []
    
    if cfg.AI_enable_AMD:
        arch = f'hip:{cfg.AI_device}'
    else:
        arch = f'cuda:{cfg.AI_device}'
    if 'cpu' in cfg.AI_device:
        arch = 'cpu'
    
    try:
        model = YOLO(f'models/{cfg.AI_model_name}', task='detect')
        print_startup_messages()
    except Exception as e:
        print('An error occurred when loading the AI model:\n', e)
        quit(0)
        
    while True:
        cfg_reload_prev_state = process_hotkeys(cfg_reload_prev_state)
        
        image = capture.get_new_frame()
        if cfg.show_window:
            visuals.queue.put(image)

        result = perform_detection(model, image, clss)

        for frame in result:
                
            if len(frame.boxes):
                if app_pause == 0:
                    shooting_queue = sort_targets(frame, cfg, arch)

                    if shooting_queue:
                        target = shooting_queue[0]
                        shooting_queue.clear()
                        
                        mouse.queue.put((target.x, target.y, target.w, target.h)) 
                else: pass

                if cfg.show_window:
                    if cfg.show_boxes:
                        visuals.draw_helpers(frame.boxes)
                    if cfg.show_target_line:
                        visuals.draw_target_line(target.x, target.y)
            else:
                mouse.queue.put(None)
            
            if cfg.show_window and cfg.show_detection_speed == True:
                visuals.draw_speed(frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])
                
        if win32api.GetAsyncKeyState(Buttons.KEY_CODES.get(cfg.hotkey_exit)) & 0xFF:
            capture.Quit()
            if cfg.show_window:
                visuals.queue.put(None)
            break

if __name__ == "__main__":
    clss = active_classes()
    init()
    