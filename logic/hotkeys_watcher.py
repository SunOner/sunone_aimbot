import threading
from typing import List
import cv2,win32api,os
from logic.config_watcher import cfg
from logic.buttons import Buttons
from logic.capture import capture
from logic.mouse import mouse
from logic.visual import visuals
from logic.shooting import shooting
class HotkeysWatcher(threading.Thread):
        def __init__(A):super(HotkeysWatcher,A).__init__();A.daemon=True;A.name='HotkeysWatcher';A.app_pause=0;A.clss=A.active_classes();A.start()
        def run(B):
                A=0
                while True:
                        A=B.process_hotkeys(A)
                        if win32api.GetAsyncKeyState(Buttons.KEY_CODES.get(cfg.hotkey_exit))&255:
                                capture.Quit()
                                if cfg.show_window:visuals.queue.put(None)
                                os._exit(0)
        def process_hotkeys(A,cfg_reload_prev_state):
                B=cfg_reload_prev_state;A.app_pause=win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_pause]);C=win32api.GetKeyState(Buttons.KEY_CODES[cfg.hotkey_reload_config])
                if C!=B:
                        if C in(1,0):
                                cfg.Read(verbose=True);capture.restart();mouse.update_settings();A.clss=A.active_classes()
                                if cfg.show_window==False:cv2.destroyAllWindows()
                B=C;return B
        def active_classes(B):
                A=[.0,1.]
                if cfg.hideout_targets:A.extend([5.,6.])
                if not cfg.disable_headshot:A.append(7.)
                if cfg.third_person:A.append(1e1)
                B.clss=A
hotkeys_watcher=HotkeysWatcher()