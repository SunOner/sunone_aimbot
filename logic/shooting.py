import queue
import threading
import win32con, win32api

from logic.config_watcher import cfg

if cfg.arduino_move or cfg.arduino_shoot:
    from logic.arduino import arduino
    
class Shooting(threading.Thread):
    def __init__(self):
        super(Shooting, self).__init__()
        self.queue = queue.Queue(maxsize=1)
        self.daemon = True
        self.name = 'Shooting'
        
        self.button_pressed = False
        
        self.start()
        
    def run(self):
        while True:
            bScope, shooting_state = self.queue.get()
            self.shoot(bScope, shooting_state)
            
    def shoot(self, bScope, shooting_state):
        # By GetAsyncKeyState
        if cfg.auto_shoot == True and cfg.triggerbot == False:
            if shooting_state and bScope or cfg.mouse_auto_aim and bScope:
                if  self.button_pressed == False:
                    if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        
                    if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                        self.ghub.mouse_down()
                        
                    if cfg.arduino_shoot: # arduino
                        arduino.press()
                    
                    self.button_pressed = True

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
            if self.button_pressed == False:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_down()
                    
                if cfg.arduino_shoot: # arduino
                    arduino.press()
                
                self.button_pressed = True

        if cfg.auto_shoot and cfg.triggerbot and bScope == False:
            if self.button_pressed == True:
                if cfg.mouse_ghub == False and cfg.arduino_shoot == False: # native
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                if cfg.mouse_ghub and cfg.arduino_shoot == False: #ghub
                    self.ghub.mouse_up()
                    
                if cfg.arduino_shoot: # arduino
                    arduino.release() 
                
                self.button_pressed = False
    
shooting = Shooting()