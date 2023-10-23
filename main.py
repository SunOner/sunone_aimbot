from ultralytics import YOLO
import numpy as np
import torch
import cv2
import win32gui, win32ui, win32con, win32api
import ghub_mouse as ghub
from math import *
from options import *
import time
import dxcam

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
    aim_x_left = int(screen_x_center - screen_height / 2)
    aim_x_right = int(screen_x_center + screen_height / 2)
    aim_y_up = int(screen_y_center - screen_width / 2)
    aim_y_down = int(screen_y_center + screen_width / 2)

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
        clss = []
        if head_correction == True:
            clss = [0, 1, 7]
        else:
            clss = [0, 1]
        result = model(
            img,
            stream=False,
            cfg='coco8.yaml',
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
            max_det=1,
            vid_stride=False,
            classes=clss,
            verbose=False,
            show_labels=False,
            show_conf=False)
        
        if show_window:
            height = int(img.shape[0] * debug_window_scale_percent / 100)
            width = int(img.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)

        annotated_frame = result[0].plot()
        final_x = 0
        final_y = 0
        for frame in result:
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
                wrapped_array_body = []
                wrapped_array_head = []
                target_distance_list = []
                target_xywh_list = []

                result_xywh = frame.boxes.xywh

                min_index = 0
                head_min_index = 0

                if head_correction == True:
                    head_distance_list = []
                    head_xywh_list = []

                wrapper_i = 0
                for c in frame.boxes.cls:
                    cls = int(c.item())
                    if cls == 0 or cls == 1:
                        wrapped_array_body.append(result_xywh[wrapper_i])
                    if cls == 7:
                        wrapped_array_head.append(result_xywh[wrapper_i])
                    wrapper_i  = wrapper_i + 1
                if head_correction == True:
                    for head in wrapped_array_head:
                        head_xywh_list.append(head)
                        head_distance = abs(edge_x + head[0] - screen_x_center)
                        head_distance_list.append(head_distance)
                        head_min_index = head_distance_list.index(min(head_distance_list))

                for target in wrapped_array_body:
                    target_xywh_list.append(target)
                    
                    target_distance = abs(edge_x + target[0] - screen_x_center)
                    target_distance_list.append(target_distance)

                    min_index = target_distance_list.index(min(target_distance_list))
                    target_xywh = target_xywh_list[min_index]
                    if head_min_index and head_correction == True:
                        head_xywh = head_xywh_list[head_min_index]
                        target_xywh_x = int(target_xywh[0] + head_xywh[0] / 2) + edge_x
                        target_xywh_y = int(target_xywh[1] + head_xywh[1] / 2) + edge_y
                    else:
                        target_xywh_x = target_xywh[0] + edge_x
                        target_xywh_y = target_xywh[1] + edge_y

                    if aim_x_left < target_xywh_x < aim_x_right and aim_y_up < target_xywh_y < aim_y_down:
                        final_x = target_xywh_x - screen_x_center
                        final_y = target_xywh_y - screen_y_center - y_offset * target_xywh[3]
                        if show_window: cv2.line(annotated_frame, (int(screen_x_center), int(screen_y_center)), (int(screen_x_center) + int(final_x), int(screen_y_center) + int(final_y)), (255, 0, 0), 2)
        
        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON):
            try:
                ghub.mouse_xy(int(final_x / mouse_sensitivity), int(final_y / mouse_sensitivity))
                final_x, final_y = 0, 0
            except:
                pass
        if show_window and show_fps:
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            cv2.putText(annotated_frame, 'FPS: {0}'.format(str(int(fps))), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

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