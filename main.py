from ultralytics import YOLO
import numpy as np
import torch
import cv2
import win32gui, win32ui, win32con, win32api
import ghub_mouse as ghub
from math import *
from options import *
from ext_tools.mouse_calc import mouse_calc

def screen_grab(region=None):
    hwin = win32gui.FindWindow("aboba", None)
    if region:
            left, top, x2, y2 = region
            width = x2 - left
            height = y2 - top
    else:
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
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

screen_x, screen_y, window_x, window_y = screen_height / 2 / 2, screen_width / 2 / 2, screen_height / 2, screen_width / 2
screen_x_center, screen_y_center = screen_x / 2, screen_y / 2
pid = mouse_calc(0.000000000000000001, 10000000, -10000000, 0.45, 0.0000000001, 0)
window_region = (int(screen_x), int(screen_y), int(screen_height - screen_x), int(screen_width - screen_y))
edge_x = screen_x_center - window_x / 2
edge_y = screen_y_center - window_y / 2

@torch.no_grad()
def init():
    np.bool = np.bool_
    aim_x = screen_height / 4
    aim_y = screen_width / 4
    aim_x_left = int(screen_x_center - aim_x / 2)
    aim_x_right = int(screen_x_center + aim_x / 2)
    aim_y_up = int(screen_y_center - aim_y / 2)
    aim_y_down = int(screen_y_center + aim_y / 2)
    avg_postprocess_speed, avg_count, avg_last = 0, 0, 0
    
    model = YOLO("models/all_1.engine")
    if show_window:
        cv2.namedWindow(debug_window_name)

    while True:
        img = screen_grab(window_region)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        clss = []
        if head_correction == True:
            clss = [0, 1, 7]
        else:
            clss = [0, 1]
        result = model.predict(
            img,
            stream=False,
            stream_buffer=False,
            agnostic_nms=False,
            save=False,
            imgsz=640,
            conf=0.35,
            iou=0.7,
            device=0,
            show=False,
            boxes=False,
            half=False,
            max_det=20,
            vid_stride=False,
            classes=clss,
            verbose=False,
            show_labels=False,
            show_conf=False,
            task='detect')
        if(show_window):
            height = int(img.shape[0] * debug_window_scale_percent / 100)
            width = int(img.shape[1] * debug_window_scale_percent / 100)
            dim = (width, height)
            

        annotated_frame = result[0].plot()
        
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
                        pid_x = int(pid.calculate_mouse(final_x, 0))
                        pid_y = int(pid.calculate_mouse(final_y, 0))
                        if show_window: cv2.line(annotated_frame, (int(screen_x_center * 2), int(screen_y_center * 2)), (int(screen_x_center * 2) + int(pid_x * 2), int(screen_y_center * 2) + int(pid_y * 2)), (255, 0, 0), 2)

                    if auto_aim == False:
                        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON):
                            try:
                                ghub.mouse_xy(pid_x, pid_y)
                                if auto_shot == True:
                                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,pid_x, pid_y, 0, 0)
                                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,pid_x, pid_y, 0, 0)
                            except:
                                pass
                    else:
                        try:
                            ghub.mouse_xy(pid_x, pid_y)
                            if auto_shot == True:
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,pid_x, pid_y, 0, 0)
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,pid_x, pid_y, 0, 0)
                        except:
                                pass

        if win32api.GetAsyncKeyState(win32con.VK_F2):
            if show_window:
                cv2.destroyWindow(debug_window_name)
            quit(0)

        if show_window:
            cv2.resizeWindow(debug_window_name, dim)
            resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
            cv2.imshow(debug_window_name, resised)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    init()