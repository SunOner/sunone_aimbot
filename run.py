from ultralytics import YOLO
import torch

from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.frame_parser import frameParser
from logic.hotkeys_watcher import hotkeys_watcher
from logic.checks import run_checks

@torch.inference_mode()
def perform_detection(model, image):
    return model.predict(
        source=image,
        cfg="logic/game.yaml",
        imgsz=cfg.ai_model_image_size,
        stream=True,
        conf=cfg.AI_conf,
        iou=0.5,
        device=cfg.AI_device,
        half=False if "cpu" in cfg.AI_device else True,
        max_det=20,
        agnostic_nms=False,
        augment=False,
        vid_stride=False,
        visualize=False,
        verbose=False,
        show_boxes=False,
        show_labels=False,
        show_conf=False,
        save=False,
        show=False)
        
def init():
    run_checks()
    
    try:
        model = YOLO(f"models/{cfg.AI_model_name}", task="detect")
    except Exception as e:
        print("An error occurred when loading the AI model:\n", e)
        quit(0)
    
    while True:
        image = capture.get_new_frame()
        
        if image is not None:
            if cfg.circle_capture:
                image = capture.convert_to_circle(image)
            
            if cfg.show_window or cfg.show_overlay:
                visuals.queue.put(image)
                
            result = perform_detection(model, image)

            if hotkeys_watcher.app_pause == 0:
                frameParser.parse(result)

if __name__ == "__main__":
    init()