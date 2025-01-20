from ultralytics import YOLO
import torch
from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.frame_parser import frameParser
from logic.hotkeys_watcher import hotkeys_watcher
from logic.checks import run_checks
import supervision as sv  # Import this for ByteTrack

@torch.inference_mode()
def perform_detection(model, image):
    if cfg.disable_tracker == False:
        # Initialize ByteTrack
        byte_tracker = sv.ByteTrack()
        
        results = model.predict(
            source=image,
            cfg="logic/tracker.yaml",
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
        
        for result in results:
            # Convert each result to detections
            detections = sv.Detections.from_ultralytics(result)
            tracked_detections = byte_tracker.update_with_detections(detections)
            return tracked_detections  # Assuming you want to return the first frame's detection for simplicity
        
    else:
        # If not using tracker, return the first result from the generator
        result = next(model.predict(
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
            show=False))
        
        return result

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