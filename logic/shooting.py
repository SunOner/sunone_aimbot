_B=True
_A=False
import queue,threading,os,win32con,win32api
from logic.ghub import gHub
from logic.config_watcher import cfg
if cfg.mouse_rzr:from logic.rzctl import RZCONTROL,MOUSE_CLICK
if cfg.arduino_move or cfg.arduino_shoot:from logic.arduino import arduino
class Shooting(threading.Thread):
        def __init__(A):
                super(Shooting,A).__init__();A.queue=queue.Queue(maxsize=1);A.daemon=_B;A.name='Shooting';A.button_pressed=_A;A.ghub=gHub;A.start()
                if cfg.mouse_rzr:
                        B='rzctl.dll';C=os.path.dirname(os.path.abspath(__file__));D=os.path.join(C,B);A.rzr=RZCONTROL(D)
                        if not A.rzr.init():print('Failed to initialize rzctl')
        def run(A):
                while _B:B,C=A.queue.get();A.shoot(B,C)
        def shoot(A,bScope,shooting_state):
                C=shooting_state;B=bScope
                if cfg.auto_shoot and not cfg.triggerbot:
                        if C and B or cfg.mouse_auto_aim and B:
                                if not A.button_pressed:
                                        if cfg.mouse_rzr:A.rzr.mouse_click(MOUSE_CLICK.LEFT_DOWN)
                                        elif cfg.mouse_ghub:A.ghub.mouse_down()
                                        elif cfg.arduino_shoot:arduino.press()
                                        else:win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
                                        A.button_pressed=_B
                        if not C and A.button_pressed or not B and A.button_pressed:
                                if cfg.mouse_rzr:A.rzr.mouse_click(MOUSE_CLICK.LEFT_UP)
                                elif cfg.mouse_ghub:A.ghub.mouse_up()
                                elif cfg.arduino_shoot:arduino.release()
                                else:win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
                                A.button_pressed=_A
                        if C==_A and A.button_pressed==_B or B==_A and A.button_pressed==_B:
                                if cfg.mouse_ghub==_A and cfg.arduino_shoot==_A:win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
                                if cfg.mouse_ghub and cfg.arduino_shoot==_A:A.ghub.mouse_up()
                                if cfg.arduino_shoot:arduino.release()
                                A.button_pressed=_A
                if cfg.auto_shoot and cfg.triggerbot and B or cfg.mouse_auto_aim and B:
                        if not A.button_pressed:
                                if cfg.mouse_rzr:A.rzr.mouse_click(MOUSE_CLICK.LEFT_DOWN)
                                elif cfg.mouse_ghub:A.ghub.mouse_down()
                                elif cfg.arduino_shoot:arduino.press()
                                else:win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
                                A.button_pressed=_B
                if cfg.auto_shoot and cfg.triggerbot and not B:
                        if A.button_pressed:
                                if cfg.mouse_rzr:A.rzr.mouse_click(MOUSE_CLICK.LEFT_UP)
                                elif cfg.mouse_ghub:A.ghub.mouse_up()
                                elif cfg.arduino_shoot:arduino.release()
                                else:win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
                                A.button_pressed=_A
shooting=Shooting()