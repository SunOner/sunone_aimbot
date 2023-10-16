import cv2
import numpy as np
import win32gui, win32ui, win32con, win32api, win32process
import psutil

def get_window_title(pid):
   def callback(hwnd, hwnd_list):
       if win32gui.IsWindowVisible(hwnd):
           if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
               hwnd_list.append(hwnd)
       return True

   hwnd_list = []
   win32gui.EnumWindows(callback, hwnd_list)

   if hwnd_list:
       return win32gui.GetWindowText(hwnd_list[0])
   return None

def grab_screen(hwnd):
  window_rect = win32gui.GetWindowRect(hwnd)
  window_x = window_rect[0]
  window_y = window_rect[1]
  window_w = window_rect[2] - window_x
  window_h = window_rect[3] - window_y
  
  hwindc = win32gui.GetWindowDC(hwnd)
  srcdc = win32ui.CreateDCFromHandle(hwindc)
  memdc = srcdc.CreateCompatibleDC()

  bmp = win32ui.CreateBitmap()
  bmp.CreateCompatibleBitmap(srcdc, window_w, window_h)
  memdc.SelectObject(bmp)
  memdc.BitBlt((0, 0), (window_w, window_h), srcdc, (window_x, window_y), win32con.SRCCOPY)

  signedIntsArray = bmp.GetBitmapBits(True)
  img = np.fromstring(signedIntsArray, dtype='uint8')
  img.shape = (window_h, window_w, 4)

  srcdc.DeleteDC()
  memdc.DeleteDC()
  win32gui.ReleaseDC(hwnd, hwindc)
  win32gui.DeleteObject(bmp.GetHandle())

  return img 

def init():
  cv2_window_scale = 50

  pid = next(item for item in psutil.process_iter() if item.name() == 'msedge.exe').pid
  window_title = get_window_title(pid)
  hwnd = win32gui.FindWindow(None, window_title)
  cv2.namedWindow('cv2')
  while True:
    img = grab_screen(hwnd)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    width, height = int(img.shape[1] * cv2_window_scale / 100), int(img.shape[0] * cv2_window_scale / 100)

    if win32api.GetAsyncKeyState(win32con.VK_F2):
        cv2.destroyWindow('cv2')
        quit(0)
    cv2.resizeWindow('cv2', (width, height))
    cv2.imshow('cv2', cv2.resize(img, (width, height), cv2.INTER_NEAREST))
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
    
if __name__ == '__main__' :
  init()