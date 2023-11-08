from options import *
import win32gui, win32ui, win32con, win32api
import numpy as np

screen_x_center, screen_y_center = screen_width / 2, screen_height / 2

def Calculate_screen_offset():
    left = original_screen_width / 2 - screen_width / 2
    top = original_screen_height / 2 - screen_height / 2
    width = left + screen_width
    height = top + screen_height
    return (int(left), int(top), int(width), int(height))

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

def check_target_in_scope(distance): # TODO
    distance = distance * (head_y_offset + body_y_offset / 2)
    if distance < 45 and distance > -45:
        return True
    else:
        return False