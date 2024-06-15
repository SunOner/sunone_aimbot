import queue
import threading
import time
import cv2
import torch
import win32gui, win32con

from logic.config_watcher import cfg
from logic.capture import capture

class Visuals(threading.Thread):
    def __init__(self):
        if cfg.show_window:
            super(Visuals, self).__init__()
            self.queue = queue.Queue(maxsize=1)
            self.daemon = True
            self.name = 'Visuals'
            
            self.image = None
            self.interpolation = cv2.INTER_NEAREST
            
            self.draw_line_data = None
            self.draw_predicted_position_data = None
            self.draw_boxes_data = None
            self.draw_speed_data = None
            self.draw_bScope_data = None
            
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
        self.spawn_debug_window()
        prev_frame_time, new_frame_time = 0, 0 if cfg.show_window_fps else None
        while True:
            self.image = self.queue.get()
            
            if self.image is None:
                self.destroy()
                break
            
            # simple line
            if self.draw_line_data is not None and len(self.draw_line_data):
                cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(self.draw_line_data[0]), int(self.draw_line_data[1])), (0, 255, 255), 2)
            
            # boxes
            if self.draw_boxes_data is not None and len(self.draw_boxes_data): 
                if cfg.show_boxes: 
                    for item in self.draw_boxes_data:
                        if item is None:
                            continue
                        for xyxy, cls, conf in zip(item.xyxy, item.cls, item.conf):
                            x0, y0, x1, y1 = map(int, map(torch.Tensor.item, xyxy))
                            cv2.rectangle(self.image, (x0, y0), (x1, y1), (0, 200, 0), 2)
                            str_cls = self.cls_model_data.get(cls.item(), '')
                            if cfg.show_labels and not cfg.show_conf:
                                cv2.putText(self.image, str_cls, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
                            if cfg.show_conf:
                                text = '{} {:.2f}'.format(str_cls, conf.item())
                                cv2.putText(self.image, text, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1, cv2.LINE_AA)
            
            # speed
            if self.draw_speed_data is not None and len(self.draw_speed_data):
                cv2.putText(self.image, 'preprocess: {:.2f}'.format(self.draw_speed_data[0]), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(self.image, 'inference: {:.2f}'.format(self.draw_speed_data[1]), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(self.image, 'postprocess: {:.2f}'.format(self.draw_speed_data[2]), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            
            # fps
            if cfg.show_window_fps:
                new_frame_time = time.time()
                fps = 1/(new_frame_time-prev_frame_time)
                prev_frame_time = new_frame_time
                cv2.putText(self.image, f'FPS: {str(int(fps))}', (10, 80) if cfg.show_detection_speed else (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

            # bScope
            if self.draw_bScope_data is not None and len(self.draw_bScope_data):
                b_x1, b_x2, b_y1, b_y2, bScope = self.draw_bScope_data
                
                if bScope:
                    cv2.putText(self.image, 'True', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                else:
                    cv2.putText(self.image, 'False', (int(b_x1), int(b_y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 0), 2, cv2.LINE_AA)
                
                cv2.rectangle(self.image, (int(b_x1), int(b_y1)), (int(b_x2), int(b_y2)), (200, 0, 0), 2)

            # prediction line
            if self.draw_predicted_position_data is not None and len(self.draw_predicted_position_data):
                cv2.line(self.image, (capture.screen_x_center, capture.screen_y_center), (int(self.draw_predicted_position_data[0]), int(self.draw_predicted_position_data[1])), (255, 0, 255), 2)
            
            # debug window: resize
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
        
    def clear(self):
        self.draw_boxes_data = None
        self.draw_line_data = None
        self.draw_speed_data = None
        self.draw_predicted_position_data = None
        self.draw_bScope_data = None
        
    def destroy(self):
        cv2.destroyAllWindows()

visuals = Visuals()