import cv2
import win32gui, win32ui, win32con
import numpy as np
from screeninfo import get_monitors
from logic.config_watcher import detection_window_width, detection_window_height

screen_x_center, screen_y_center = detection_window_width / 2, detection_window_height / 2

def Calculate_screen_offset():
    left, top = get_primary_display_resolution()
    left = left / 2 - detection_window_width / 2
    top = top / 2 - detection_window_height / 2
    width = left + detection_window_width
    height = top + detection_window_height
    return (int(left), int(top), int(width), int(height))

def windows_grab_screen(region):
    hwin = win32gui.GetDesktopWindow()

    left,top,x2,y2 = region
    width = x2 - left + 1
    height = y2 - top + 1
    
    hwindc = win32gui.GetWindowDC(hwin)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
    
    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height,width,4)

    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

def check_target_in_scope(target_x, target_y, target_w, target_h):
    x = detection_window_width / 2
    y = detection_window_height / 2
    x1 = target_x - target_w
    x2 = target_x + target_w
    y1 = target_y - target_h
    y2 = target_y + target_h
    if (x > x1 and x < x2 and y > y1 and y < y2) :
        return True
    else :
        return False

def get_primary_display_resolution():
    _ = get_monitors()
    for m in _:
        if m.is_primary:
            return m.width, m.height
    