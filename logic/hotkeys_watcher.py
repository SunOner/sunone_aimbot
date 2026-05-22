import threading
import time
from typing import List
import cv2
import os

from logic.config_watcher import cfg
from logic.capture import capture
from logic.mouse import mouse
from logic.visual import visuals
from logic.platform import input_backend

class HotkeysWatcher(threading.Thread):
    def __init__(self):
        super(HotkeysWatcher, self).__init__()
        self.daemon = True
        self.name = 'HotkeysWatcher'
        
        self.app_pause = 0
        self.clss = self.active_classes()
        self._next_config_poll_at = 0.0

        self.start()
        
    def run(self):
        cfg_reload_prev_state = False
        while True:
            cfg_reload_prev_state = self.process_hotkeys(cfg_reload_prev_state)
            self.reload_config_if_changed()
                
            # terminate
            if input_backend.is_pressed(cfg.hotkey_exit):
                capture.Quit()
                if cfg.show_window:
                    visuals.stop()
                os._exit(0)
            time.sleep(0.01)
            
    def process_hotkeys(self, cfg_reload_prev_state):
        self.app_pause = -1 if input_backend.is_pressed(cfg.hotkey_pause) else 0
        app_reload_cfg = input_backend.is_pressed(cfg.hotkey_reload_config)
        
        if app_reload_cfg and not cfg_reload_prev_state:
            cfg.Read(verbose=True)
            self.apply_config_changes()
                    
        return app_reload_cfg

    def reload_config_if_changed(self):
        now = time.monotonic()
        if now < self._next_config_poll_at:
            return
        self._next_config_poll_at = now + 0.25
        if cfg.reload_if_changed(verbose=True):
            self.apply_config_changes()

    def apply_config_changes(self):
        capture.restart()
        mouse.update_settings()
        try:
            from logic.frame_parser import frameParser
            frameParser.update_settings()
        except ImportError:
            pass
        self.clss = self.active_classes()
        if cfg.show_window == False:
            cv2.destroyAllWindows()

    def active_classes(self) -> List[int]:
        clss = [0, 1]
        
        if cfg.hideout_targets:
            clss.extend([5, 6])

        if not cfg.disable_headshot:
            clss.append(7)
            
        if cfg.third_person:
            clss.append(10)
        
        self.clss = clss
        return clss
    
hotkeys_watcher = HotkeysWatcher()
