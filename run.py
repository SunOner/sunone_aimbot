
from logic.config_watcher import Config
cfg = Config()
from logic.buttons import *
from logic.capture import *
from logic.mouse import MouseThread

from ultralytics import YOLO
from threading import Thread
import math
import torch
import cv2
import time
from typing import List
import win32api, win32con, win32gui
if cfg.show_overlay_detector:
    import tkinter as tk

class Target:
    def __init__(self, x, y, w, h, cls):
        self.x = x
        self.y = y if cls == 7 else (y - cfg.body_y_offset * h)
        self.w = w
        self.h = h
        self.distance = math.sqrt((x - frames.screen_x_center)**2 + (y - frames.screen_y_center)**2)
        self.cls = cls
      
class OverlayWindow:
    def __init__(self):
        self.overlay_detector = tk.Tk()
        self.overlay_detector.geometry(f'{cfg.detection_window_width}x{cfg.detection_window_height}+{frames.Calculate_screen_offset()[0]}+{frames.Calculate_screen_offset()[1]}')
        self.overlay_detector.lift()
        self.overlay_detector.wm_attributes("-topmost", True)
        self.overlay_detector.wm_attributes("-disabled", True)
        self.overlay_detector.wm_attributes("-transparentcolor", "white")
        self.overlay_detector.title('new1.txt')
        self.overlay_detector.overrideredirect(True)
        
        self.canvas = tk.Canvas(self.overlay_detector, bg='white', height=cfg.detection_window_height, width=cfg.detection_window_width)
        self.canvas.pack()

@torch.no_grad()
def perform_detection(model, image, clss):
    return model.predict(
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
        half=True,
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
            version = lines[0].replace('app=', '')
    except:
        print('version file is not found')
        
    print('Aimbot is started. Enjoy!\n',
          f'Version {version}\n',
          f'[{cfg.hotkey_targeting}] - Aiming at the target\n',
          f'[{cfg.hotkey_exit}] - EXIT\n',
          f'[{cfg.hotkey_pause}] - PAUSE AIM\n',
          f'[{cfg.hotkey_reload_config}] - Reload config')
    
def process_hotkeys(cfg_reload_prev_state):
    global app_pause
    global clss
    app_pause = win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_pause])
    app_reload_cfg = win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_reload_config])
    if app_reload_cfg != cfg_reload_prev_state:
        if app_reload_cfg in (1, 0):
            cfg.Read(verbose=True)
            frames.reload_capture()
            mouse_worker.Update_settings()
            clss = active_classes()
            
            if cfg.show_window == False:
                cv2.destroyAllWindows()
    cfg_reload_prev_state = app_reload_cfg
    return cfg_reload_prev_state

def update_overlay_window(overlay):
    if cfg.show_overlay_detector:
        overlay.overlay_detector.update()
        overlay.canvas.delete("all")
        
def spawn_debug_window():
    if cfg.show_window:
        cv2.namedWindow(cfg.debug_window_name)
        if cfg.debug_window_always_on_top:
            debug_window_hwnd = win32gui.FindWindow(None, cfg.debug_window_name)
            win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)
            
def sort_targets(frame, cfg) -> List[Target]:
    boxes_array = frame.boxes.xywh.to(f'cuda:{cfg.AI_device}')
    distances_sq = torch.sum((boxes_array[:, :2] - torch.tensor([frames.screen_x_center, frames.screen_y_center], device=f'cuda:{cfg.AI_device}')) ** 2, dim=1)
    classes_tensor = frame.boxes.cls.to(f'cuda:{cfg.AI_device}')

    if not cfg.disable_headshot:
        score = distances_sq + 10000 * (classes_tensor != 7).float()
        sort_indices = torch.argsort(score).cpu().numpy()
    else:
        class7_indices = torch.nonzero(classes_tensor == 7, as_tuple=False).squeeze(1)
        other_indices = torch.nonzero(classes_tensor != 7, as_tuple=False).squeeze(1)

        if len(class7_indices) > 0:
            class7_distances_sq = distances_sq[class7_indices]
            sort_indices_class7 = torch.argsort(class7_distances_sq)
            class7_indices = class7_indices[sort_indices_class7]
        else:
            sort_indices_class7 = torch.tensor([], dtype=torch.int64, device=f'cuda:{cfg.AI_device}')

        other_distances_sq = distances_sq[other_indices]
        sort_indices_other = torch.argsort(other_distances_sq)

        sort_indices = torch.cat((class7_indices, other_indices[sort_indices_other])).cpu().numpy()

    return [Target(*boxes_array[i, :4].cpu().numpy(), classes_tensor[i].item()) for i in sort_indices]

def active_classes():
    clss = [0, 1]
    if cfg.hideout_targets:
        clss += 5, 6
    if cfg.disable_headshot == False:
        clss.append(7)
    return clss

def init():
    overlay = OverlayWindow() if cfg.show_overlay_detector else None
    prev_frame_time, new_frame_time = 0, 0 if cfg.show_window and cfg.show_fps else None
    try:
        model = YOLO(f'models/{cfg.AI_model_path}', task='detect')
        print_startup_messages()
    except Exception as e:
        print(e)
        quit(0)
    
    spawn_debug_window()
    cfg_reload_prev_state = 0
    shooting_queue = []
    
    while True:
        cfg_reload_prev_state = process_hotkeys(cfg_reload_prev_state)
        image = frames.get_new_frame()
        result = perform_detection(model, image, clss)
        update_overlay_window(overlay)
            
        if cfg.show_window:
            annotated_frame = image

        for frame in result:
            if cfg.show_window and cfg.show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                if app_pause == 0:
                    shooting_queue = sort_targets(frame, cfg)

                    if shooting_queue:
                        target = shooting_queue[0]
                        shooting_queue.clear()
                        
                        mouse_worker.queue.put((target.x, target.y, target.w, target.h))

                        if cfg.show_window or cfg.show_overlay_detector:
                            screen_x_center = cfg.detection_window_width / 2
                            screen_y_center = cfg.detection_window_height / 2
                            
                            if cfg.show_target_line and cfg.show_window:
                                draw_target_line(annotated_frame, screen_x_center, screen_y_center, target.x, target.y + cfg.body_y_offset / target.h)
                            
                        if cfg.show_overlay_detector:
                            x1 = target.x - target.w / 2
                            y1 = target.y - target.h / 2
                            x2 = target.x + target.w / 2
                            y2 = target.y + target.h / 2
                            
                            if cfg.disable_headshot:
                                y1 += cfg.body_y_offset * target.h
                                y2 += cfg.body_y_offset * target.h
                            
                            if cfg.show_overlay_boxes:
                                overlay.canvas.create_rectangle(x1.item(), y1.item(), x2.item(), y2.item(), width=2, outline='green')
                            
                            if cfg.show_overlay_line:
                                overlay.canvas.create_line(screen_x_center, screen_y_center, target.x, target.y + cfg.body_y_offset / target.h, width=2, fill='red')
                            
                else: pass

                if cfg.show_window and cfg.show_boxes:
                    draw_helpers(annotated_frame=annotated_frame, boxes=frame.boxes)
            else:
                mouse_worker.queue.put(None)

        if cfg.show_window and cfg.show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            
            cv2.putText(annotated_frame, f'FPS: {str(int(fps))}', (10, 80) if cfg.show_speed else (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if cfg.show_window:
            try:
                if cfg.debug_window_scale_percent != 100:
                    height = int(cfg.detection_window_height * cfg.debug_window_scale_percent / 100)
                    width = int(cfg.detection_window_width * cfg.debug_window_scale_percent / 100)
                    dim = (width, height)
                    cv2.resizeWindow(cfg.debug_window_name, dim)
                    resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
                    cv2.imshow(cfg.debug_window_name, resised)
                else:
                    cv2.imshow(cfg.debug_window_name, annotated_frame)
            except: exit(0)
            if cfg.show_window and cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
        if win32api.GetAsyncKeyState(Buttons.KEY_CODES.get(cfg.hotkey_exit)) & 0xFF:
            if cfg.show_window:
                cv2.destroyWindow(cfg.debug_window_name)
            frames.Quit()
            break

if __name__ == "__main__":
    frames = Capture()
    mouse_worker = MouseThread()
    clss = active_classes()
    init()
    