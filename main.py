from ultralytics import YOLO
import numpy as np
import torch
import cv2
import win32gui, win32ui, win32con, win32api
from options import *
import time
import dxcam
import math

class Target:
    def __init__(self, cls, x, y, w, h):
        self.cls = cls
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.distance = math.sqrt((self.x - screen_x_center)**2 + (self.y - screen_y_center)**2)
        
region = Calculate_screen_offset()
if Dxcam_capture:
    dx = dxcam.create(device_idx=dxcam_monitor_id, output_idx=dxcam_gpu_id, output_color="BGR", max_buffer_len=dxcam_max_buffer_len)

screen_x_center, screen_y_center = screen_width / 2, screen_height / 2
edge_x = screen_x_center - screen_width / 2
edge_y = screen_y_center - screen_height / 2

if Windows_capture:
    def windows_grab_screen(region):
        hwin = win32gui.FindWindow("aboba", None)
        left, top, x2, y2 = region
        width = x2 - left
        height = y2 - top

        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
        
        signedIntsArray = bmp.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img

@torch.no_grad()
def init():
    global screen_height
    global screen_width
    
    if Dxcam_capture:
        dx.start(region, target_fps=dxcam_capture_fps)
    if Obs_capture:
        obs_camera = cv2.VideoCapture(Obs_camera_id)
        screen_width  = obs_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        screen_height = obs_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

    np.bool = np.bool_

    avg_postprocess_speed, avg_count, avg_last = 0, 0, 0

    if show_window and show_fps:
        prev_frame_time = 0
        new_frame_time = 0

    model = YOLO(model_path)

    if show_window:
        cv2.namedWindow(debug_window_name)

    while True:
        if Dxcam_capture:
            img = dx.get_latest_frame()
        if Obs_capture:
            ret_val, img = obs_camera.read()
        if Windows_capture:
            img = windows_grab_screen(region)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        result = model(
            img,
            stream=False,
            cfg='game.yaml',
            stream_buffer=True,
            agnostic_nms=True,
            save=False,
            imgsz=640,
            conf=0.40,
            iou=0.2,
            device=0,
            show=False,
            boxes=False,
            half=True,
            max_det=10,
            vid_stride=False,
            classes=range(9),
            verbose=False,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(img.shape[0] * debug_window_scale_percent / 100)
            width = int(img.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)

        annotated_frame = result[0].plot()
        
        for frame in result: # current frame
            if show_window and show_speed == True:
                speed_preprocess, speed_inference, speed_postprocess = frame.speed['preprocess'], frame.speed['inference'], frame.speed['postprocess']
                cv2.putText(annotated_frame, 'preprocess:', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_preprocess), (150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'inference:', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_inference), (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'postprocess:', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(speed_postprocess), (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.putText(annotated_frame, 'avg_postprocess_speed:', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(avg_last), (240, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

                if avg_count <= 60:
                    avg_postprocess_speed = avg_postprocess_speed + speed_postprocess
                    avg_count = avg_count + 1
                if avg_count >= 60:
                    avg_postprocess_speed = avg_postprocess_speed / 60
                    avg_last = avg_postprocess_speed
                    avg_count = 0
                    avg_postprocess_speed = 0

            if len(frame.boxes):
                final_x = 0
                final_y = 0
                targets = []
                
                for cls_num in frame.boxes.cls:
                    cls = int(cls_num.item())
                    if cls == 0:
                        targets.append(Target(cls=cls,x=frame.boxes.xywh[cls][0].item(), y=frame.boxes.xywh[cls][1].item(), w=frame.boxes.xywh[cls][2].item(), h=frame.boxes.xywh[cls][3].item()))

                for s in targets:
                    final_x = int((s.x - screen_x_center) / mouse_sensitivity)
                    final_y = int((s.y - screen_y_center- y_offset * s.h) / mouse_sensitivity)
                    if show_window: cv2.line(annotated_frame, (int(screen_x_center), int(screen_y_center)), (int(screen_x_center) + int(final_x), int(screen_y_center) + int(final_y)), (255, 0, 0), 2)
                    if win32api.GetAsyncKeyState(win32con.VK_RBUTTON):
                        try:
                            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, final_x, final_y, 0, 0)
                            final_x = 0
                            final_y = 0
                        except:
                            pass

        if show_window and show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            if show_speed:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            else:
                cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

        if win32api.GetAsyncKeyState(win32con.VK_F2):
            if show_window:
                cv2.destroyWindow(debug_window_name)
                if Dxcam_capture:
                    dx.stop()
            quit(0)

        if show_window:
            cv2.resizeWindow(debug_window_name, dim)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    init()