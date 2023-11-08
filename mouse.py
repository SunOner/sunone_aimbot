import win32gui, win32ui, win32con, win32api
import asyncio
from screen import check_target_in_scope
from options import mouse_auto_shoot, mouse_auto_shoot_timer, mouse_auto_shoot_sleep_time, mouse_native
import ghub_mouse as ghub

def win32_raw_mouse_move(x, y, dst=None):
    if mouse_native:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)
    else:
        ghub.mouse_xy(x, y)

    bDst = check_target_in_scope(dst)

    if mouse_auto_shoot and bDst:
        asyncio.run(win32_raw_mouse_click(x=x, y=y))
        
    if mouse_auto_shoot and bDst:
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