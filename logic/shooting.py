import queue
import threading
import os
import win32con, win32api

from logic.ghub import gHub
from logic.config_watcher import cfg
from logic.logger import logger

if cfg.mouse_rzr:
    from logic.rzctl import RZCONTROL 
    from logic.rzctl import MOUSE_CLICK

if cfg.arduino_move or cfg.arduino_shoot:
    from logic.arduino import arduino
    
class Shooting(threading.Thread):
    def __init__(self):
        super(Shooting, self).__init__()
        self.queue = queue.Queue(maxsize=1)
        self.daemon = True
        self.name = 'Shooting'
        self.button_pressed = False
        self.ghub = gHub
        self.lock = threading.Lock()
        
        self.start()
        if cfg.mouse_rzr:
            dll_name = "rzctl.dll" 
            script_directory = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_directory, dll_name)
            self.rzr = RZCONTROL(dll_path)
            
            if not self.rzr.init():
                logger.error("[Shooting] Failed to initialize rzctl")
            
    def run(self):
        while True:
            try:
                bScope, shooting_state = self.queue.get()
                self.shoot(bScope, shooting_state)
            except Exception as e:
                logger.error("[Shooting] Shooting thread crashed: %s", e)
            
    def shoot(self, bScope, shooting_state):
        with self.lock:
            # By GetAsyncKeyState
            if cfg.auto_shoot and not cfg.triggerbot:
                if shooting_state and bScope or cfg.mouse_auto_aim and bScope:
                    if not self.button_pressed:
                        if cfg.mouse_rzr:  # Razer
                            self.rzr.mouse_click(MOUSE_CLICK.LEFT_DOWN)
                        elif cfg.mouse_ghub:  # ghub
                            self.ghub.mouse_down()
                        elif cfg.arduino_shoot:  # arduino
                            arduino.press()
                        else:  # native
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

                        self.button_pressed = True

            if not shooting_state and self.button_pressed or not bScope and self.button_pressed:
                if cfg.mouse_rzr:  # Razer
                    self.rzr.mouse_click(MOUSE_CLICK.LEFT_UP)
                elif cfg.mouse_ghub:  # ghub
                    self.ghub.mouse_up()
                elif cfg.arduino_shoot:  # arduino
                    arduino.release()
                else:  # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

                self.button_pressed = False

            if shooting_state == False and self.button_pressed == True or bScope == False and self.button_pressed == True:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_up()
                    
                if cfg.arduino_shoot: # arduino
                    arduino.release()
                
                self.button_pressed = False
        
        # By triggerbot
        if cfg.auto_shoot and cfg.triggerbot and bScope or cfg.mouse_auto_aim and bScope:
            if not self.button_pressed:
                if cfg.mouse_rzr:  # Razer
                    self.rzr.mouse_click(MOUSE_CLICK.LEFT_DOWN)
                elif cfg.mouse_ghub:  # ghub
                    self.ghub.mouse_down()
                elif cfg.arduino_shoot:  # arduino
                    arduino.press()
                else:  # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

                self.button_pressed = True

        if cfg.auto_shoot and cfg.triggerbot and not bScope:
            if self.button_pressed:
                if cfg.mouse_rzr:  # Razer
                    self.rzr.mouse_click(MOUSE_CLICK.LEFT_UP)
                elif cfg.mouse_ghub:  # ghub
                    self.ghub.mouse_up()
                elif cfg.arduino_shoot:  # arduino
                    arduino.release()
                else:  # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

                self.button_pressed = False
    
shooting = Shooting()