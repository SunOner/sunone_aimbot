import queue
import threading
import os

from logic.config_watcher import cfg
from logic.logger import logger
from logic.platform import input_backend

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
        self.ghub = None
        self.lock = threading.Lock()

        if cfg.mouse_ghub:
            from logic.ghub import gHub
            self.ghub = gHub

        if cfg.mouse_rzr:
            dll_name = "rzctl.dll"
            script_directory = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_directory, dll_name)
            self.rzr = RZCONTROL(dll_path)

            if not self.rzr.init():
                logger.error("[Shooting] Failed to initialize rzctl")

        self.start()

    def submit(self, bScope, shooting_state):
        try:
            self.queue.put_nowait((bScope, shooting_state))
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            self.queue.put_nowait((bScope, shooting_state))

    def run(self):
        while True:
            try:
                bScope, shooting_state = self.queue.get()
                self.shoot(bScope, shooting_state)
            except Exception as e:
                logger.error("[Shooting] Shooting thread crashed: %s", e)

    def shoot(self, bScope, shooting_state):
        with self.lock:
            self._ensure_hardware()
            should_press = False

            if cfg.mouse_auto_aim and bScope:
                should_press = True
            elif cfg.auto_shoot and cfg.triggerbot:
                should_press = bScope
            elif cfg.auto_shoot:
                should_press = shooting_state and bScope

            if should_press and not self.button_pressed:
                self._press()
                self.button_pressed = True
            elif not should_press and self.button_pressed:
                self._release()
                self.button_pressed = False

    def _ensure_hardware(self):
        global RZCONTROL, MOUSE_CLICK

        if cfg.mouse_ghub and self.ghub is None:
            from logic.ghub import gHub
            self.ghub = gHub

        if cfg.mouse_rzr and not hasattr(self, "rzr"):
            from logic.rzctl import RZCONTROL, MOUSE_CLICK
            dll_name = "rzctl.dll"
            script_directory = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.join(script_directory, dll_name)
            self.rzr = RZCONTROL(dll_path)
            if not self.rzr.init():
                logger.error("[Shooting] Failed to initialize rzctl")

    def _press(self):
        if cfg.mouse_rzr:
            self.rzr.mouse_click(MOUSE_CLICK.LEFT_DOWN)
        elif cfg.mouse_ghub:
            self.ghub.mouse_down()
        elif cfg.arduino_shoot:
            from logic.arduino import arduino
            arduino.press()
        else:
            if not input_backend.left_down():
                logger.warning("[Shooting] Native mouse click backend is unavailable on this platform.")

    def _release(self):
        if cfg.mouse_rzr:
            self.rzr.mouse_click(MOUSE_CLICK.LEFT_UP)
        elif cfg.mouse_ghub:
            self.ghub.mouse_up()
        elif cfg.arduino_shoot:
            from logic.arduino import arduino
            arduino.release()
        else:
            if not input_backend.left_up():
                logger.warning("[Shooting] Native mouse click backend is unavailable on this platform.")

shooting = Shooting()
