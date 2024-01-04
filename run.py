from logic.config_watcher import Config
cfg = Config()
from logic.keyboard import *
from logic.capture import *
from logic.mouse import MouseThread

from ultralytics import YOLO
import math
import torch
import cv2
import time
import win32api, win32con, win32gui
if cfg.show_overlay_detector:
    import tkinter as tk

class Target:
    def __init__(self, x, y, w, h, cls):
        self.mouse_x = x - frames.screen_x_center
        self.mouse_y = (y - frames.screen_y_center) if cls == 7 else (y - frames.screen_y_center - cfg.body_y_offset * h)
        self.distance = math.sqrt((x - frames.screen_x_center)**2 + (y - frames.screen_y_center)**2)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cls = cls
        
class OverlayWindow:
    def __init__(self):
        self.overlay_detector = tk.Tk()
        self.overlay_detector.geometry(f'{cfg.detection_window_width}x{cfg.detection_window_height}+{frames.Calculate_screen_offset()[0]}+{frames.Calculate_screen_offset()[1]}')
        self.overlay_detector.lift()
        self.overlay_detector.wm_attributes("-topmost", True)
        self.overlay_detector.wm_attributes("-disabled", True)
        self.overlay_detector.wm_attributes("-transparentcolor", "white")
        self.overlay_detector.title('new.txt')
        self.overlay_detector.overrideredirect(True)
        
        self.canvas = tk.Canvas(self.overlay_detector, bg='white', height=cfg.detection_window_height, width=cfg.detection_window_width)
        self.canvas.pack()
        
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
        half=False,
        max_det=cfg.AI_max_det,
        vid_stride=False,
        classes=clss,
        verbose=False,
        show_boxes=False,
        show_labels=False,
        show_conf=False,
        show=False)
    
def print_startup_messages():
    print('Aimbot is started. Enjoy!\n'
          f'[{cfg.hotkey_targeting}] - Aiming at the target\n'
          f'[{cfg.hotkey_exit}] - EXIT\n'
          f'[{cfg.hotkey_pause}] - PAUSE AIM\n'
          f'[{cfg.hotkey_reload_config}] - Reload config')
    
def process_hotkeys(cfg_reload_prev_state):
    global app_pause
    app_pause = win32api.GetKeyState(Keyboard.KEY_CODES[cfg.hotkey_pause])
    app_reload_cfg = win32api.GetKeyState(Keyboard.KEY_CODES[cfg.hotkey_reload_config])
    if app_reload_cfg != cfg_reload_prev_state:
        if app_reload_cfg in (1, 0):
            cfg.Read(verbose=True)
            frames.reload_capture()
            mouse_worker.Update_settings()
    cfg_reload_prev_state = app_reload_cfg
    return cfg_reload_prev_state

def update_overlay_window(overlay):
    if cfg.show_overlay_detector:
        overlay.overlay_detector.update()
        overlay.canvas.delete("all")
        
@torch.no_grad()
def init():
    overlay = OverlayWindow() if cfg.show_overlay_detector else None
    prev_frame_time, new_frame_time = 0, 0 if cfg.show_window and cfg.show_fps else None
        
    try:
        model = YOLO(f'models/{cfg.AI_model_path}', task='detect')
        print_startup_messages()
    except Exception as e:
        print(e)
        quit(0)
    
    if cfg.show_window:
        print('An open debug window can affect performance.')
        cv2.namedWindow(cfg.debug_window_name)
        if cfg.debug_window_always_on_top:
            debug_window_hwnd = win32gui.FindWindow(None, cfg.debug_window_name)
            win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)

    clss = [0, 1, 5, 6, 7] if cfg.hideout_targets else [0, 1, 7]
    cfg_reload_prev_state = 0
    shooting_queue = []

    while True:
        cfg_reload_prev_state = process_hotkeys(cfg_reload_prev_state)
        image = frames.get_new_frame()
        result = perform_detection(model, image, clss)
        update_overlay_window(overlay)
        
        if cfg.show_window and cfg.debug_window_scale_percent != 100:
            height = int(cfg.detection_window_height * cfg.debug_window_scale_percent / 100)
            width = int(cfg.detection_window_width * cfg.debug_window_scale_percent / 100)
            dim = (width, height)
            
        if cfg.show_window:
            annotated_frame = image

        for frame in result:
            if cfg.show_window and cfg.show_speed == True:
                annotated_frame = speed(annotated_frame, frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

            if len(frame.boxes):
                if app_pause == 0:
                    for box in frame.boxes:
                        cls = int(box.cls.item())
                        if not cfg.disable_headshot:
                            shooting_queue.append(Target(*box.xywh[0], cls))
                        elif cls in (0, 1, 5, 6):
                            shooting_queue.append(Target(*box.xywh[0], cls))

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
                            
                        if cfg.show_overlay_detector and cfg.show_overlay_boxes:
                            x1, y1 = target.x - target.w / 2, target.y - target.h / 2
                            x2, y2 = target.x + target.w / 2, target.y + target.h / 2
                            overlay.canvas.create_rectangle(x1.item(), y1.item(), x2.item(), y2.item(), width=2, outline='green')
                            
                        if cfg.show_overlay_detector and cfg.show_overlay_line:
                            overlay.canvas.create_line(cfg.detection_window_width / 2, cfg.detection_window_height / 2, target.mouse_x.item() + frames.screen_x_center, target.mouse_y.item() + frames.screen_y_center + cfg.body_y_offset / target.h.item(), width=2, fill='red')
                            
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
                cv2.putText(annotated_frame, f'FPS: {str(int(fps))}', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.putText(annotated_frame, f'FPS: {str(int(fps))}', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if win32api.GetAsyncKeyState(Keyboard.KEY_CODES.get(cfg.hotkey_exit)) & 0xFF:
            if cfg.show_window:
                cv2.destroyWindow(cfg.debug_window_name)
            frames.Quit()
            break

        if cfg.show_window:
            try:
                if cfg.debug_window_scale_percent != 100:
                    cv2.resizeWindow(cfg.debug_window_name, dim)
                    resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
                    cv2.imshow(cfg.debug_window_name, resised)
                else:
                    cv2.imshow(cfg.debug_window_name, annotated_frame)
            except: exit(0)
            if cfg.show_window and cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    frames = Capture()
    mouse_worker = MouseThread()
    init()