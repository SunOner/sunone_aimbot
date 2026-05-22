import queue
import threading
import time
import cv2
import os

from logic.config_watcher import cfg
from logic.capture import capture
from logic.overlay import overlay
from logic.buttons import Buttons
from logic.logger import logger
from logic.platform import IS_WINDOWS, input_backend

if IS_WINDOWS:
    import win32gui
    import win32con

class Visuals(threading.Thread):
    def __init__(self):
        super(Visuals, self).__init__()
        overlay.show(cfg.detection_window_width, cfg.detection_window_height)
        self.queue = queue.Queue(maxsize=1)
        self.daemon = True
        self.name = 'Visuals'
        self.image = None
        self.screenshot_taken = False
        self.interpolation = cv2.INTER_NEAREST
        self.debug_window_open = False
        self.last_debug_window_dim = None
        self.data_lock = threading.Lock()

        self.draw_line_data = None
        self.draw_predicted_position_data = None
        self.draw_boxes_data = None
        self.draw_speed_data = None
        self.draw_bScope_data = None
        self.draw_history_point_data = []
        self.cls_model_data = {
            0: 'player',
            1: 'bot',
            2: 'weapon',
            3: 'outline',
            4: 'dead_body',
            5: 'hideout_target_human',
            6: 'hideout_target_balls',
            7: 'head',
            8: 'smoke',
            9: 'fire',
            10: 'third_person'
        }

        self.disabled_line_classes = [2, 3, 4, 8, 9, 10]
        self.start()

    def submit_frame(self, image):
        if not (cfg.show_window or cfg.show_overlay):
            return

        frame = image.copy()
        self._put_latest(frame)

    def stop(self):
        self._put_latest(None)

    def _put_latest(self, item):
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            self.queue.put_nowait(item)
    
    def run(self):
        prev_frame_time = time.perf_counter()
            
        while True:
            self.image = self.queue.get()
            
            if self.image is None:
                self.destroy()
                break

            if cfg.show_overlay:
                overlay.show(cfg.detection_window_width, cfg.detection_window_height)

            if cfg.show_window and not self.debug_window_open:
                self.spawn_debug_window()
            
            # screenshot
            screenshot_key = Buttons.KEY_CODES.get(cfg.debug_window_screenshot_key)
            if screenshot_key is not None and input_backend.is_pressed(cfg.debug_window_screenshot_key):
                if not self.screenshot_taken:
                    cv2.imwrite(f"./screenshots/{time.time()}.jpg", self.image)
                    self.screenshot_taken = True
            else:
                self.screenshot_taken = False

            with self.data_lock:
                draw_line_data = self.draw_line_data
                draw_predicted_position_data = self.draw_predicted_position_data
                draw_boxes_data = self.draw_boxes_data
                draw_speed_data = self.draw_speed_data
                draw_bScope_data = self.draw_bScope_data
                draw_history_point_data = list(self.draw_history_point_data)
            
            # simple line
            if draw_line_data:
                if cfg.show_window and cfg.show_target_line:
                    cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(draw_line_data[0]), int(draw_line_data[1])), (0, 255, 255), 2)
                
                if cfg.show_overlay and cfg.overlay_show_target_line:
                    overlay.draw_line(capture.screen_x_center, capture.screen_y_center, int(draw_line_data[0]), int(draw_line_data[1]), 'green', 2)

            # boxes
            if draw_boxes_data is not None:
                boxes = draw_boxes_data

                
                if hasattr(boxes, "cls"): # Ultralytics Boxes
                    xyxy_iter = boxes.xyxy
                    cls_iter  = boxes.cls
                    conf_iter = boxes.conf
                else:
                    xyxy_iter = boxes.xyxy # supervision.Detections
                    cls_iter  = boxes.class_id
                    conf_iter = boxes.confidence

                if conf_iter is None:
                    conf_iter = [None] * len(xyxy_iter)

                for xyxy, cls, conf in zip(xyxy_iter, cls_iter, conf_iter):
                    x0, y0, x1, y1 = map(int, map(float, xyxy))
                            
                    if cfg.show_window and cfg.show_boxes:
                        cv2.rectangle(self.image, (x0, y0), (x1, y1), (0, 200, 0), 2)
                        
                    if cfg.show_overlay and cfg.overlay_show_boxes:
                        overlay.draw_square(x0, y0, x1, y1, 'green', 2)
                        
                    # cv2 and overlay labels and conf
                    cls_id = self._scalar(cls)
                    str_cls = self.cls_model_data.get(int(cls_id), '')
                    
                    # cv2 labels
                    if cfg.show_window and cfg.show_labels and not cfg.show_conf:
                        cv2.putText(self.image, str_cls, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
                    
                    # format conf text for cv2 and overlay
                    if cfg.show_window or cfg.show_overlay:
                        conf_text = str_cls if conf is None else '{} {:.2f}'.format(str_cls, float(self._scalar(conf)))
                    
                    # cv2 conf
                    if cfg.show_window and cfg.show_conf:
                        cv2.putText(self.image, conf_text, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
                    
                    if cfg.show_overlay and (cfg.overlay_show_conf or cfg.overlay_show_labels):
                        # out of overlay
                        x_out = 0
                        y_out = 0
                        
                        if y0 <= 15:
                            x_out = x0 - 45
                            y_out = y0 + 15
                        else:
                            x_out = x0 + 45
                            y_out = y0 - 15
                        
                        if x0 <= 40:
                            x_out = x0 + 40
                        
                        if x0 >= cfg.detection_window_width - 80:
                            x_out = x0 - 40

                        # overlay conf
                        if cfg.overlay_show_conf:
                            overlay.draw_text(x_out, y_out, conf_text)

                        # overlay labels
                        if cfg.overlay_show_labels and not cfg.overlay_show_conf:
                            overlay.draw_text(x_out, y_out, str_cls)
                                
            # speed
            if draw_speed_data:
                if cfg.show_window:
                    cv2.putText(self.image, 'preprocess: {:.2f}'.format(draw_speed_data[0]), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(self.image, 'inference: {:.2f}'.format(draw_speed_data[1]), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(self.image, 'postprocess: {:.2f}'.format(draw_speed_data[2]), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            
            # fps
            if cfg.show_window_fps:
                new_frame_time = time.perf_counter()
                fps = 1 / max(new_frame_time - prev_frame_time, 1e-6)
                prev_frame_time = new_frame_time
                if cfg.show_window:
                    cv2.putText(self.image, f'FPS: {str(int(fps))}', (10, 80) if cfg.show_detection_speed else (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

            # bScope
            if draw_bScope_data:
                b_x1, b_x2, b_y1, b_y2, bScope = draw_bScope_data
                
                if bScope:
                    if cfg.show_window:
                        cv2.putText(self.image, 'True', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                else:
                    if cfg.show_window:
                        cv2.putText(self.image, 'False', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                
                if cfg.show_window:
                    cv2.rectangle(self.image, (int(b_x1), int(b_y1)), (int(b_x2), int(b_y2)), (200, 0, 0), 2)

            # prediction line
            if draw_predicted_position_data:
                if cfg.show_window and cfg.show_target_prediction_line:
                    cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(draw_predicted_position_data[0]), int(draw_predicted_position_data[1])), (255, 0, 255), 2)
                
                if cfg.show_overlay and cfg.overlay_show_target_prediction_line:
                    overlay.draw_line(capture.screen_x_center, capture.screen_y_center, int(draw_predicted_position_data[0]), int(draw_predicted_position_data[1]), 'green', 2)
            
            # history points
            if draw_history_point_data:
                for x, y in draw_history_point_data:
                    if cfg.show_window:
                        cv2.circle(self.image, (x + capture.screen_x_center, y + capture.screen_y_center), radius=1, color=(0, 0, 255), thickness=2)
                    
            # debug window: resize
            if cfg.show_window:
                try:
                    if cfg.debug_window_scale_percent != 100:
                        height = int(cfg.detection_window_height * cfg.debug_window_scale_percent / 100)
                        width = int(cfg.detection_window_width * cfg.debug_window_scale_percent / 100)
                        dim = (width, height)
                        if self.last_debug_window_dim != dim:
                            cv2.resizeWindow(cfg.debug_window_name, dim)
                            self.last_debug_window_dim = dim
                        resised = cv2.resize(self.image, dim, self.interpolation)
                        cv2.imshow(cfg.debug_window_name, resised)
                    else:
                        cv2.imshow(cfg.debug_window_name, self.image)
                except Exception as e:
                    logger.error(f'[Visuals] Debug window error: {e}')
                    self.destroy()
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
    def spawn_debug_window(self):
        cv2.namedWindow(cfg.debug_window_name)
        self.debug_window_open = True
        
        if cfg.debug_window_always_on_top and IS_WINDOWS:
            try:
                x = cfg.spawn_window_pos_x
                y = cfg.spawn_window_pos_y
                
                if x <= -1:
                    x = 0
                if y <= -1:
                    y = 0
                
                debug_window_hwnd = win32gui.FindWindow(None, cfg.debug_window_name)
                win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, x, y, cfg.detection_window_width, cfg.detection_window_height, 0)
            except Exception as e:
                logger.error(f'[Visuals] Error with on top window, skipping this option `debug_window_always_on_top`: {e}')
                
    def draw_target_line(self, target_x, target_y, target_cls):
        if target_cls not in self.disabled_line_classes:
            with self.data_lock:
                self.draw_line_data = (target_x, target_y)

    def draw_predicted_position(self, target_x, target_y, target_cls):
        if target_cls not in self.disabled_line_classes:
            with self.data_lock:
                self.draw_predicted_position_data = (target_x, target_y)
        
    def draw_speed(self, speed_preprocess, speed_inference, speed_postprocess):
        with self.data_lock:
            self.draw_speed_data = (speed_preprocess, speed_inference, speed_postprocess)

    def draw_helpers(self, boxes):
        with self.data_lock:
            self.draw_boxes_data = boxes
        
    def draw_bScope(self, x1, x2, y1, y2, bScope):
        with self.data_lock:
            self.draw_bScope_data = (x1, x2, y1, y2, bScope)
        
    def draw_history_point_add_point(self, x, y):
        with self.data_lock:
            self.draw_history_point_data.append([int(x), int(y)])
            if len(self.draw_history_point_data) > 30:
                self.draw_history_point_data.pop(0)
        
    def clear(self):
        with self.data_lock:
            self.draw_boxes_data = None
            self.draw_line_data = None
            self.draw_speed_data = None
            self.draw_predicted_position_data = None
            self.draw_bScope_data = None
        
    def destroy(self):
        cv2.destroyAllWindows()
        self.debug_window_open = False
        self.last_debug_window_dim = None

    @staticmethod
    def _scalar(value):
        return value.item() if hasattr(value, "item") else value

visuals = Visuals()
