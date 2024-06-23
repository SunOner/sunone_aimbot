import queue
import threading
import time
import cv2
import torch
import win32gui, win32con

from logic.config_watcher import cfg
from logic.capture import capture
from logic.overlay import overlay

class Visuals(threading.Thread):
    def __init__(self):
        overlay.show(cfg.detection_window_width, cfg.detection_window_height)
        
        if cfg.show_window or cfg.show_overlay:
            super(Visuals, self).__init__()
            self.queue = queue.Queue(maxsize=1)
            self.daemon = True
            self.name = 'Visuals'
            self.image = None
            
            if cfg.show_window:
                self.interpolation = cv2.INTER_NEAREST
            
            self.draw_line_data = None
            self.draw_predicted_position_data = None
            self.draw_boxes_data = None
            self.draw_speed_data = None
            self.draw_bScope_data = None
            self.draw_history_point_data = []
            self.cls_model_data = {
                0:'player',
                1:'bot',
                2:'weapon',
                3:'outline',
                4:'dead_body',
                5:'hideout_target_human',
                6:'hideout_target_balls',
                7:'head',
                8:'smoke',
                9:'fire'
                }
            
            self.start()
    
    def run(self):
        if cfg.show_window:
            self.spawn_debug_window()
            prev_frame_time, new_frame_time = 0, 0 if cfg.show_window_fps else None
            
        while True:
            self.image = self.queue.get()
            
            if self.image is None:
                self.destroy()
                break
            
            # simple line
            if self.draw_line_data is not None and len(self.draw_line_data):
                if cfg.show_window and cfg.show_target_line:
                    cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(self.draw_line_data[0]), int(self.draw_line_data[1])), (0, 255, 255), 2)
                
                if cfg.show_overlay and cfg.overlay_show_target_line:
                    overlay.draw_line(capture.screen_x_center, capture.screen_y_center, int(self.draw_line_data[0]), int(self.draw_line_data[1]), 'green', 2)

            # boxes
            if self.draw_boxes_data is not None and len(self.draw_boxes_data): 
                for item in self.draw_boxes_data:
                    if item is not None:
                        for xyxy, cls, conf in zip(item.xyxy, item.cls, item.conf):
                            x0, y0, x1, y1 = map(int, map(torch.Tensor.item, xyxy))
                            
                            if cfg.show_window and cfg.show_boxes:
                                cv2.rectangle(self.image, (x0, y0), (x1, y1), (0, 200, 0), 2)
                                
                            if cfg.show_overlay and cfg.overlay_show_boxes:
                                overlay.draw_square(x0, y0, x1, y1, 'green', 2)
                                
                            # cv2 and overlay labels and conf
                            str_cls = self.cls_model_data.get(cls.item(), '')
                            
                            # cv2 labels
                            if cfg.show_window and cfg.show_labels and not cfg.show_conf:
                                cv2.putText(self.image, str_cls, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
                            
                            # overlay labels
                            if cfg.show_overlay and cfg.overlay_show_labels and not cfg.overlay_show_conf:
                                overlay.draw_text(x0 + 30, y0 + 7, str_cls)
                            
                            # cv2 conf
                            conf_text = '{} {:.2f}'.format(str_cls, conf.item())
                            
                            if cfg.show_window and cfg.show_conf:
                                cv2.putText(self.image, conf_text, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)

                            # overlay conf
                            if cfg.show_overlay and cfg.overlay_show_conf:
                                overlay.draw_text(x0 + 45, y0 + 7, conf_text)
            # speed
            if self.draw_speed_data is not None and len(self.draw_speed_data):
                if cfg.show_window:
                    cv2.putText(self.image, 'preprocess: {:.2f}'.format(self.draw_speed_data[0]), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(self.image, 'inference: {:.2f}'.format(self.draw_speed_data[1]), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(self.image, 'postprocess: {:.2f}'.format(self.draw_speed_data[2]), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            
            # fps
            if cfg.show_window_fps:
                new_frame_time = time.time()
                fps = 1/(new_frame_time-prev_frame_time)
                prev_frame_time = new_frame_time
                if cfg.show_window:
                    cv2.putText(self.image, f'FPS: {str(int(fps))}', (10, 80) if cfg.show_detection_speed else (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

            # bScope
            if self.draw_bScope_data is not None and len(self.draw_bScope_data):
                b_x1, b_x2, b_y1, b_y2, bScope = self.draw_bScope_data
                
                if bScope:
                    if cfg.show_window:
                        cv2.putText(self.image, 'True', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                else:
                    if cfg.show_window:
                        cv2.putText(self.image, 'False', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                
                if cfg.show_window:
                    cv2.rectangle(self.image, (int(b_x1), int(b_y1)), (int(b_x2), int(b_y2)), (200, 0, 0), 2)

            # prediction line
            if self.draw_predicted_position_data is not None and len(self.draw_predicted_position_data):
                if cfg.show_window and cfg.show_target_prediction_line:
                    cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(self.draw_predicted_position_data[0]), int(self.draw_predicted_position_data[1])), (255, 0, 255), 2)
                
                if cfg.show_overlay and cfg.overlay_show_target_prediction_line:
                    overlay.draw_line(capture.screen_x_center, capture.screen_y_center, int(self.draw_predicted_position_data[0]), int(self.draw_predicted_position_data[1]), 'green', 2)  
            
            # history points
            if self.draw_history_point_data is not None and len(self.draw_history_point_data):
                if len(self.draw_history_point_data) >= 30:
                    self.draw_history_point_data.pop(0)
                for x, y in self.draw_history_point_data:
                    if cfg.show_window:
                        cv2.circle(self.image, (x + capture.screen_x_center, y + capture.screen_y_center), radius=1, color=(0, 0, 255), thickness=2)
                    
            # debug window: resize
            if cfg.show_window:
                try:
                    if cfg.debug_window_scale_percent != 100:
                        height = int(cfg.detection_window_height * cfg.debug_window_scale_percent / 100)
                        width = int(cfg.detection_window_width * cfg.debug_window_scale_percent / 100)
                        dim = (width, height)
                        cv2.resizeWindow(cfg.debug_window_name, dim)
                        resised = cv2.resize(self.image, dim, self.interpolation)
                        cv2.imshow(cfg.debug_window_name, resised)
                        self.clear()
                    else:
                        cv2.imshow(cfg.debug_window_name, self.image)
                        self.clear()
                except: exit(0)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
            if cfg.show_overlay:
                self.clear()
                
    def spawn_debug_window(self):
        cv2.namedWindow(cfg.debug_window_name)
        if cfg.debug_window_always_on_top:
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
                print(f'Error with on top window, skipping this option `debug_window_always_on_top`:{e}')
                
    def draw_target_line(self, target_x, target_y):
        self.draw_line_data = (target_x, target_y)

    def draw_predicted_position(self, target_x, target_y):
        self.draw_predicted_position_data = (target_x, target_y)
        
    def draw_speed(self, speed_preprocess, speed_inference, speed_postprocess):
        self.draw_speed_data = (speed_preprocess, speed_inference, speed_postprocess)

    def draw_helpers(self, boxes):
        self.draw_boxes_data = boxes
        
    def draw_bScope(self, x1, x2, y1, y2, bScope):
        self.draw_bScope_data = (x1, x2, y1, y2, bScope)
        
    def draw_history_point_add_point(self, x, y):
        self.draw_history_point_data.append([int(x), int(y)])
        
    def clear(self):
        self.draw_boxes_data = None
        self.draw_line_data = None
        self.draw_speed_data = None
        self.draw_predicted_position_data = None
        self.draw_bScope_data = None
        
    def destroy(self):
        cv2.destroyAllWindows()

visuals = Visuals()