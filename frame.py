from options import *
from screen import *
import cv2
import dxcam

dx = None
obs_camera = None

def get_new_frame():
    global dx
    global obs_camera
    if Dxcam_capture and dx is None:
        dx = dxcam.create(device_idx=dxcam_monitor_id, output_idx=dxcam_gpu_id, output_color="BGR", max_buffer_len=dxcam_max_buffer_len)
        if dx.is_capturing == False:
            dx.start(Calculate_screen_offset(), target_fps=dxcam_capture_fps)
    if Dxcam_capture and dx is not None:
        img = dx.get_latest_frame()

    if Obs_capture and obs_camera is None:
        obs_camera = cv2.VideoCapture(Obs_camera_id)
        obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
        obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)
    if Obs_capture and obs_camera is not None:
        ret_val, img = obs_camera.read()
    if native_Windows_capture:
        img = windows_grab_screen(Calculate_screen_offset())
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    
    return img

def debug_draw_distance_line(annotated_frame, debug_lines):
    try:
        if show_window: cv2.line(annotated_frame, (int(screen_x_center), int(screen_y_center)), (int(screen_x_center) + int(debug_lines[0]), int(screen_y_center) + int(debug_lines[1])), (0, 200, 200), 2)
        cv2.putText(annotated_frame, str(round(debug_lines[2], 2)), (int(screen_x_center), int(screen_y_center)), cv2.FONT_HERSHEY_SIMPLEX,  0.6, (0, 200, 200) , 2, cv2.LINE_AA)
    except:
        pass
    return annotated_frame

def speed(annotated_frame, speed_preprocess, speed_inference, speed_postprocess):
    cv2.putText(annotated_frame, 'preprocess:', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(annotated_frame, str(speed_preprocess), (150, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'inference:', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(annotated_frame, str(speed_inference), (150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.putText(annotated_frame, 'postprocess:', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(annotated_frame, str(speed_postprocess), (150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    return annotated_frame