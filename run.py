from ultralytics import YOLO
import torch
from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.frame_parser import frameParser
from logic.hotkeys_watcher import hotkeys_watcher
from logic.checks import run_checks
@torch.inference_mode()
def perform_detection(model,image):A=False;return model.predict(source=image,cfg='logic/game.yaml',imgsz=cfg.ai_model_image_size,stream=True,conf=cfg.AI_conf,iou=.5,device=cfg.AI_device,half=A if'cpu'in cfg.AI_device else True,max_det=20,agnostic_nms=A,augment=A,vid_stride=A,visualize=A,verbose=A,show_boxes=A,show_labels=A,show_conf=A,save=A,show=A)
def init():
        run_checks()
        try:B=YOLO(f"models/{cfg.AI_model_name}",task='detect')
        except Exception as C:print('An error occurred when loading the AI model:\n',C);quit(0)
        while True:
                A=capture.get_new_frame()
                if A is not None:
                        if cfg.circle_capture:A=capture.convert_to_circle(A)
                        if cfg.show_window or cfg.show_overlay:visuals.queue.put(A)
                        D=perform_detection(B,A)
                        if hotkeys_watcher.app_pause==0:frameParser.parse(D)
if __name__=='__main__':init()