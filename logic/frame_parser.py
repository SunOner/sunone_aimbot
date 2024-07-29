import torch

from logic.hotkeys_watcher import hotkeys_watcher
from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.mouse import mouse
from logic.shooting import shooting

class Target:
    def __init__(self, x, y, w, h, cls):
        self.x = x
        self.y = y if cls == 7 else (y - cfg.body_y_offset * h)
        self.w = w
        self.h = h
        self.cls = cls

class FrameParser:
    def __init__(self):
        self.arch = self.get_arch()
    
    def parse(self, result):
        for frame in result:
            if frame.boxes:
                target = self.sort_targets(frame)
                
                if target:
                    if hotkeys_watcher.clss is None:
                        hotkeys_watcher.active_classes()
                    if target.cls in hotkeys_watcher.clss:
                        mouse.process_data((target.x, target.y, target.w, target.h, target.cls))
                
                if cfg.show_window or cfg.show_overlay:
                    if cfg.show_boxes or cfg.overlay_show_boxes:
                        visuals.draw_helpers(frame.boxes)
            else:
                # no detections
                if cfg.auto_shoot or cfg.triggerbot:
                    shooting.shoot(False, False)
                if cfg.show_window or cfg.show_overlay:
                    visuals.clear()
            
            if cfg.show_window and cfg.show_detection_speed:
                visuals.draw_speed(frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])
               
    def sort_targets(self, frame):
        boxes_array = frame.boxes.xywh.to(self.arch)
        classes_tensor = frame.boxes.cls.to(self.arch)
        
        if not classes_tensor.numel():
            return None

        center = torch.tensor([capture.screen_x_center, capture.screen_y_center], device=self.arch)
        distances_sq = torch.sum((boxes_array[:, :2] - center) ** 2, dim=1)

        if not cfg.disable_headshot:
            head_mask = classes_tensor == 7
            if head_mask.any():
                head_distances_sq = distances_sq[head_mask]
                nearest_head_idx = torch.argmin(head_distances_sq)
                nearest_idx = torch.nonzero(head_mask)[nearest_head_idx].item()
            else:
                nearest_idx = torch.argmin(distances_sq)
        else:
            nearest_idx = torch.argmin(distances_sq)

        target_data = boxes_array[nearest_idx, :4].cpu().numpy()
        target_class = classes_tensor[nearest_idx].item()
        
        return Target(*target_data, target_class)
    
    def get_arch(self):
        if cfg.AI_enable_AMD:
            arch = f'hip:{cfg.AI_device}'
        else:
            arch = f'cuda:{cfg.AI_device}'
        if 'cpu' in cfg.AI_device:
            arch = 'cpu'
        return arch

frameParser = FrameParser()