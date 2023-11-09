import win32gui, win32ui, win32con, win32api
import asyncio
from screen import check_target_in_scope
from options import mouse_auto_shoot, mouse_auto_shoot_timer, mouse_auto_shoot_sleep_time, mouse_native
import ghub_mouse as ghub

def win32_raw_mouse_move(x, y, target_x=None, target_y=None, target_w=None, target_h=None):
    if mouse_native:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)
    else:
        ghub.mouse_xy(x, y)
    if target_x is not None and target_y is not None:
        bScope = check_target_in_scope(target_x, target_y, target_w, target_h)

    if mouse_auto_shoot and bScope:
        asyncio.run(win32_raw_mouse_click(x=x, y=y))
        
    if mouse_auto_shoot and bScope:
        asyncio.run(win32_raw_mouse_click(x=x, y=y))

async def win32_raw_mouse_click(x, y):
    if mouse_auto_shoot_timer:
        await asyncio.sleep(mouse_auto_shoot_sleep_time)
    if mouse_native:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    else:
        ghub.mouse_down(1)
        ghub.mouse_up(1)