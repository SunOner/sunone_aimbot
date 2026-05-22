import torch
import supervision as sv
import numpy as np

from logic.hotkeys_watcher import hotkeys_watcher
from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.mouse import mouse
from logic.shooting import shooting

class Target:
    def __init__(self, x, y, w, h, cls):
        self.cls = int(cls)
        self.x = x
        self.y = y if self.cls == 7 else (y - cfg.body_y_offset * h)
        self.w = w
        self.h = h

class FrameParser:
    def __init__(self):
        self.arch = self.get_arch()
        self._center = None
        self._center_cache_key = None

    def parse(self, result):
        if result is None:
            self._handle_no_detections()
            return

        if isinstance(result, sv.Detections):
            self._process_sv_detections(result)
        else:
            self._process_yolo_detections(result)

    def _process_sv_detections(self, detections):
        if len(detections) > 0:
            if cfg.show_window or cfg.show_overlay:
                visuals.draw_helpers(detections)
            target = self.sort_targets(detections)
            self._handle_target(target)
        else:
            self._handle_no_detections()

    def _process_yolo_detections(self, results):
        frames = (results,) if hasattr(results, "boxes") else results
        processed = False

        for frame in frames:
            processed = True
            boxes = getattr(frame, "boxes", None)
            if boxes is not None and len(boxes) > 0:
                target = self.sort_targets(frame)
                self._handle_target(target)
                self._visualize_frame(frame)
            else:
                self._handle_no_detections()

        if not processed:
            self._handle_no_detections()

    def _handle_target(self, target):
        if target:
            if hotkeys_watcher.clss is None:
                hotkeys_watcher.active_classes()

            if target.cls in hotkeys_watcher.clss:
                mouse.process_data((target.x, target.y, target.w, target.h, target.cls))

    def _visualize_frame(self, frame):
        if cfg.show_window or cfg.show_overlay:
            if cfg.show_boxes or cfg.overlay_show_boxes:
                visuals.draw_helpers(frame.boxes)

            if cfg.show_window and cfg.show_detection_speed:
                visuals.draw_speed(frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess'])

    def _handle_no_detections(self):
        if cfg.show_window or cfg.show_overlay:
            visuals.clear()
        if cfg.auto_shoot or cfg.triggerbot:
            shooting.shoot(False, False)

    def sort_targets(self, frame):
        if isinstance(frame, sv.Detections):
            boxes_array, classes_tensor = self._convert_sv_to_tensor(frame)
        else:
            if frame.boxes is None or len(frame.boxes) == 0:
                return None
            boxes_array = self._to_tensor(frame.boxes.xywh, dtype=torch.float32)
            classes_tensor = self._to_tensor(frame.boxes.cls, dtype=torch.long)

        if not classes_tensor.numel():
            return None

        return self._find_nearest_target(boxes_array, classes_tensor)

    def _convert_sv_to_tensor(self, frame):
        xyxy = np.asarray(frame.xyxy, dtype=np.float32)
        xywh = np.empty((xyxy.shape[0], 4), dtype=np.float32)
        xywh[:, 0] = (xyxy[:, 0] + xyxy[:, 2]) / 2
        xywh[:, 1] = (xyxy[:, 1] + xyxy[:, 3]) / 2
        xywh[:, 2] = xyxy[:, 2] - xyxy[:, 0]
        xywh[:, 3] = xyxy[:, 3] - xyxy[:, 1]

        boxes_tensor = torch.as_tensor(xywh, dtype=torch.float32, device=self.arch)
        class_ids = frame.class_id if frame.class_id is not None else np.zeros(xyxy.shape[0], dtype=np.int64)
        classes_tensor = torch.as_tensor(class_ids, dtype=torch.long, device=self.arch)
        return boxes_tensor, classes_tensor

    def _to_tensor(self, value, dtype):
        if hasattr(value, "to"):
            return value.to(device=self.arch, dtype=dtype)
        return torch.as_tensor(value, dtype=dtype, device=self.arch)

    def _find_nearest_target(self, boxes_array, classes_tensor):
        center = self._get_center(boxes_array.device)
        distances_sq = torch.sum((boxes_array[:, :2] - center) ** 2, dim=1)

        if cfg.disable_headshot:
            non_head_mask = classes_tensor != 7
            weights = torch.ones_like(distances_sq)
            weights[classes_tensor == 7] *= 0.5
            size_factor = (boxes_array[:, 2] * boxes_array[:, 3]).clamp_min(1.0)
            distances_sq = weights * (distances_sq / size_factor)

            if not non_head_mask.any():
                return None
            candidate_idxs = torch.nonzero(non_head_mask, as_tuple=False).flatten()
            nearest_idx = candidate_idxs[torch.argmin(distances_sq[candidate_idxs])].item()
        else:
            head_mask = classes_tensor == 7
            if head_mask.any():
                candidate_idxs = torch.nonzero(head_mask, as_tuple=False).flatten()
                nearest_idx = candidate_idxs[torch.argmin(distances_sq[candidate_idxs])].item()
            else:
                nearest_idx = torch.argmin(distances_sq)

        target_data = boxes_array[nearest_idx, :4].cpu().numpy()
        target_class = int(classes_tensor[nearest_idx].item())

        return Target(*target_data, target_class)

    def _get_center(self, device):
        key = (capture.screen_x_center, capture.screen_y_center, str(device))
        if self._center is None or self._center_cache_key != key:
            self._center = torch.tensor(
                [capture.screen_x_center, capture.screen_y_center],
                dtype=torch.float32,
                device=device
            )
            self._center_cache_key = key
        return self._center

    def update_settings(self):
        self.arch = self.get_arch()
        self._center = None
        self._center_cache_key = None

    def get_arch(self):
        if cfg.AI_enable_AMD:
            return f'hip:{cfg.AI_device}'
        ai_device = str(cfg.AI_device).lower()
        if 'cpu' in ai_device:
            return 'cpu'
        if ai_device == 'cuda':
            return 'cuda'
        if ai_device.startswith('cuda:'):
            return cfg.AI_device
        else:
            return f'cuda:{cfg.AI_device}'

frameParser = FrameParser()
