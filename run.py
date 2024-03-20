from ultralytics import YOLO
import torch
import win32api

from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.frame_parser import frameParser
from logic.hotkeys_watcher import hotkeys_watcher
    
mask_points = []
annotated_frame = None

@torch.no_grad()
def perform_detection(model, image, clss):
    return model.predict(
        source=image,
        stream=True,
        cfg='logic/game.yaml',
        imgsz=480,
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

def init():    
    try:
        model = YOLO(f'models/{cfg.AI_model_name}', task='detect')
        print_startup_messages()
    except Exception as e:
        print('An error occurred when loading the AI model:\n', e)
        quit(0)
        
    while True:
        image = capture.get_new_frame()
        
        if cfg.show_window:
            visuals.queue.put(image)
        
        result = perform_detection(model, image, hotkeys_watcher.clss)
        
        if hotkeys_watcher.app_pause == 0:
            frameParser.parse(result)

if __name__ == "__main__":
    init()