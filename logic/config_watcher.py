import configparser
from pathlib import Path
from typing import Any, Callable, Dict, Union
import random

from logic.logger import logger

StrPath = Union[str, Path]

class Config:
    CONFIG_PATH: Path
    WINDOW_NAMES_PATH: Path

    def __init__(self, path: StrPath = "config.ini", window_names_path: StrPath = "window_names.txt"):
        self.CONFIG_PATH = Path(path)
        self.WINDOW_NAMES_PATH = Path(window_names_path)

        self.config = configparser.ConfigParser()
        self._dirty: bool = False
        self._last_mtime_ns: int = 0

        self.DEFAULTS: Dict[str, Dict[str, str]] = {
            "Detection window": {
                "detection_window_width": "320",
                "detection_window_height": "320",
                "circle_capture": "true",
            },
            "Capture Methods": {
                "capture_fps": "60",
                "Bettercam_capture": "false",
                "bettercam_monitor_id": "0",
                "bettercam_gpu_id": "0",
                "Obs_capture": "false",
                "Obs_camera_id": "0",
                "mss_capture": "true",
            },
            "Aim": {
                "body_y_offset": "0.0",
                "hideout_targets": "false",
                "disable_headshot": "false",
                "disable_prediction": "false",
                "prediction_interval": "0.05",
                "third_person": "false",
            },
            "Hotkeys": {
                "hotkey_targeting": "RightMouseButton",
                "hotkey_exit": "F2",
                "hotkey_pause": "F3",
                "hotkey_reload_config": "F4",
            },
            "Mouse": {
                "mouse_dpi": "800",
                "mouse_sensitivity": "1.0",
                "mouse_fov_width": "200",
                "mouse_fov_height": "200",
                "mouse_min_speed_multiplier": "0.1",
                "mouse_max_speed_multiplier": "1.0",
                "mouse_lock_target": "false",
                "mouse_auto_aim": "false",
                "mouse_ghub": "false",
                "mouse_rzr": "false",
            },
            "Shooting": {
                "auto_shoot": "false",
                "triggerbot": "false",
                "force_click": "false",
                "bScope_multiplier": "1.0",
            },
            "Arduino": {
                "arduino_move": "false",
                "arduino_shoot": "false",
                "arduino_port": "COM3",
                "arduino_baudrate": "115200",
                "arduino_16_bit_mouse": "false",
            },
            "AI": {
                "AI_model_name": "sunxds_0.8.0.pt",
                "ai_model_image_size": "640",
                "AI_conf": "0.2",
                "AI_device": "0",
                "AI_enable_AMD": "false",
                "disable_tracker": "false",
            },
            "overlay": {
                "show_overlay": "true",
                "overlay_show_borders": "false",
                "overlay_show_boxes": "true",
                "overlay_show_target_line": "false",
                "overlay_show_target_prediction_line": "false",
                "overlay_show_labels": "true",
                "overlay_show_conf": "false",
            },
            "Debug window": {
                "show_window": "false",
                "show_detection_speed": "false",
                "show_window_fps": "false",
                "show_boxes": "false",
                "show_labels": "false",
                "show_conf": "false",
                "show_target_line": "false",
                "show_target_prediction_line": "false",
                "show_bScope_box": "false",
                "show_history_points": "false",
                "debug_window_always_on_top": "false",
                "spawn_window_pos_x": "100",
                "spawn_window_pos_y": "100",
                "debug_window_scale_percent": "100",
                "debug_window_screenshot_key": "F12",
            },
        }

        self.window_name: str = self._get_random_window_name()

        self.read(verbose=False)

    def read(self, verbose: bool = False) -> None:
        """Load from disk, ensure defaults, expose typed attributes, and persist any missing keys."""
        self._dirty = False
        self.config = configparser.ConfigParser()

        if not self.CONFIG_PATH.exists():
            logger.warning("[Config] config.ini not found. Creating with defaults.")
            self._init_with_defaults()
            self._save()

        try:
            with self.CONFIG_PATH.open("r", encoding="utf-8") as f:
                self.config.read_file(f)
        except Exception as e:
            logger.error(f"[Config] Failed to read config.ini: {e}. Re-initializing with defaults.")
            self._init_with_defaults()

        self._ensure_defaults_present()

        self._bind_attributes()

        if self._dirty:
            self._save()
            self._dirty = False

        if verbose:
            logger.info("[Config] Config loaded")

        self._last_mtime_ns = self._get_mtime_ns()

    def Read(self, verbose: bool = False) -> None:
        self.read(verbose=verbose)

    def _init_with_defaults(self) -> None:
        self.config.clear()
        for section, kv in self.DEFAULTS.items():
            self.config[section] = dict(kv)
        self._dirty = True

    def _ensure_defaults_present(self) -> None:
        for section, options in self.DEFAULTS.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                self._dirty = True
            for opt, val in options.items():
                if not self.config.has_option(section, opt):
                    self.config.set(section, opt, val)
                    self._dirty = True

    def _save(self) -> None:
        try:
            if self.CONFIG_PATH.exists():
                bak = self.CONFIG_PATH.with_suffix(self.CONFIG_PATH.suffix + ".bak")
                if not bak.exists():
                    bak.write_bytes(self.CONFIG_PATH.read_bytes())
            with self.CONFIG_PATH.open("w", encoding="utf-8") as f:
                self.config.write(f)
            self._last_mtime_ns = self._get_mtime_ns()
            logger.info("[Config] Saved config.ini")
        except Exception as e:
            logger.error(f"[Config] Failed to save config.ini: {e}")

    def _get_mtime_ns(self) -> int:
        try:
            return self.CONFIG_PATH.stat().st_mtime_ns
        except OSError:
            return 0

    def reload_if_changed(self, verbose: bool = False) -> bool:
        current_mtime_ns = self._get_mtime_ns()
        if current_mtime_ns == 0 or current_mtime_ns == self._last_mtime_ns:
            return False
        self.read(verbose=verbose)
        return True

    def _ensure_and_get(
        self,
        section: str,
        option: str,
        fallback: Any,
        caster: Callable[[str], Any]) -> Any:
        if not self.config.has_section(section):
            self.config.add_section(section)
            self._dirty = True

        if not self.config.has_option(section, option):
            self.config.set(section, option, self._to_str(fallback))
            self._dirty = True

        raw = self.config.get(section, option, fallback=self._to_str(fallback))
        try:
            return caster(raw)
        except Exception:
            logger.warning(f"[Config] Invalid value for [{section}] {option!r}={raw!r}; resetting to default.")
            self.config.set(section, option, self._to_str(fallback))
            self._dirty = True
            return caster(self._to_str(fallback))

    @staticmethod
    def _to_str(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _bind_attributes(self) -> None:
        # Detection window
        s = "Detection window"
        self.detection_window_width = self._ensure_and_get(s, "detection_window_width", 320, int)
        self.detection_window_height = self._ensure_and_get(s, "detection_window_height", 320, int)
        self.circle_capture = self._ensure_and_get(s, "circle_capture", True, lambda v: self._to_bool(v))

        # Capture Methods
        s = "Capture Methods"
        self.capture_fps = self._ensure_and_get(s, "capture_fps", 60, int)

        self.Bettercam_capture = self._ensure_and_get(s, "Bettercam_capture", False, self._to_bool)
        self.bettercam_monitor_id = self._ensure_and_get(s, "bettercam_monitor_id", 0, int)
        self.bettercam_gpu_id = self._ensure_and_get(s, "bettercam_gpu_id", 0, int)

        self.Obs_capture = self._ensure_and_get(s, "Obs_capture", False, self._to_bool)
        self.Obs_camera_id = self._ensure_and_get(s, "Obs_camera_id", "0", str)

        self.mss_capture = self._ensure_and_get(s, "mss_capture", True, self._to_bool)

        # Aim
        s = "Aim"
        self.body_y_offset = self._ensure_and_get(s, "body_y_offset", 0.0, float)
        self.hideout_targets = self._ensure_and_get(s, "hideout_targets", False, self._to_bool)
        self.disable_headshot = self._ensure_and_get(s, "disable_headshot", False, self._to_bool)
        self.disable_prediction = self._ensure_and_get(s, "disable_prediction", False, self._to_bool)
        self.prediction_interval = self._ensure_and_get(s, "prediction_interval", 0.05, float)
        self.third_person = self._ensure_and_get(s, "third_person", False, self._to_bool)

        # Hotkeys
        s = "Hotkeys"
        self.hotkey_targeting = self._ensure_and_get(s, "hotkey_targeting", "RightMouseButton", str)
        self.hotkey_targeting_list = [t.strip() for t in self.hotkey_targeting.split(",") if t.strip()]
        self.hotkey_exit = self._ensure_and_get(s, "hotkey_exit", "F2", str)
        self.hotkey_pause = self._ensure_and_get(s, "hotkey_pause", "F3", str)
        self.hotkey_reload_config = self._ensure_and_get(s, "hotkey_reload_config", "F4", str)

        # Mouse
        s = "Mouse"
        self.mouse_dpi = self._ensure_and_get(s, "mouse_dpi", 800, int)
        self.mouse_sensitivity = self._ensure_and_get(s, "mouse_sensitivity", 1.0, float)
        self.mouse_fov_width = self._ensure_and_get(s, "mouse_fov_width", 200, int)
        self.mouse_fov_height = self._ensure_and_get(s, "mouse_fov_height", 200, int)
        self.mouse_min_speed_multiplier = self._ensure_and_get(s, "mouse_min_speed_multiplier", 0.1, float)
        self.mouse_max_speed_multiplier = self._ensure_and_get(s, "mouse_max_speed_multiplier", 1.0, float)
        self.mouse_lock_target = self._ensure_and_get(s, "mouse_lock_target", False, self._to_bool)
        self.mouse_auto_aim = self._ensure_and_get(s, "mouse_auto_aim", False, self._to_bool)
        self.mouse_ghub = self._ensure_and_get(s, "mouse_ghub", False, self._to_bool)
        self.mouse_rzr = self._ensure_and_get(s, "mouse_rzr", False, self._to_bool)

        # Shooting
        s = "Shooting"
        self.auto_shoot = self._ensure_and_get(s, "auto_shoot", False, self._to_bool)
        self.triggerbot = self._ensure_and_get(s, "triggerbot", False, self._to_bool)
        self.force_click = self._ensure_and_get(s, "force_click", False, self._to_bool)
        self.bScope_multiplier = self._ensure_and_get(s, "bScope_multiplier", 1.0, float)

        # Arduino
        s = "Arduino"
        self.arduino_move = self._ensure_and_get(s, "arduino_move", False, self._to_bool)
        self.arduino_shoot = self._ensure_and_get(s, "arduino_shoot", False, self._to_bool)
        self.arduino_port = self._ensure_and_get(s, "arduino_port", "COM3", str)
        self.arduino_baudrate = self._ensure_and_get(s, "arduino_baudrate", 115200, int)
        self.arduino_16_bit_mouse = self._ensure_and_get(s, "arduino_16_bit_mouse", False, self._to_bool)

        # AI
        s = "AI"
        self.AI_model_name = self._ensure_and_get(s, "AI_model_name", "sunxds_0.8.0.pt", str)
        self.ai_model_image_size = self._ensure_and_get(s, "ai_model_image_size", 640, int)
        self.AI_conf = self._ensure_and_get(s, "AI_conf", 0.2, float)
        self.AI_device = self._ensure_and_get(s, "AI_device", "0", str)
        self.AI_enable_AMD = self._ensure_and_get(s, "AI_enable_AMD", False, self._to_bool)
        self.disable_tracker = self._ensure_and_get(s, "disable_tracker", False, self._to_bool)

        # Overlay
        s = "overlay"
        self.show_overlay = self._ensure_and_get(s, "show_overlay", True, self._to_bool)
        self.overlay_show_borders = self._ensure_and_get(s, "overlay_show_borders", False, self._to_bool)
        self.overlay_show_boxes = self._ensure_and_get(s, "overlay_show_boxes", True, self._to_bool)
        self.overlay_show_target_line = self._ensure_and_get(s, "overlay_show_target_line", False, self._to_bool)
        self.overlay_show_target_prediction_line = self._ensure_and_get(s, "overlay_show_target_prediction_line", False, self._to_bool)
        self.overlay_show_labels = self._ensure_and_get(s, "overlay_show_labels", True, self._to_bool)
        self.overlay_show_conf = self._ensure_and_get(s, "overlay_show_conf", False, self._to_bool)

        # Debug window
        s = "Debug window"
        self.show_window = self._ensure_and_get(s, "show_window", False, self._to_bool)
        self.show_detection_speed = self._ensure_and_get(s, "show_detection_speed", False, self._to_bool)
        self.show_window_fps = self._ensure_and_get(s, "show_window_fps", False, self._to_bool)
        self.show_boxes = self._ensure_and_get(s, "show_boxes", False, self._to_bool)
        self.show_labels = self._ensure_and_get(s, "show_labels", False, self._to_bool)
        self.show_conf = self._ensure_and_get(s, "show_conf", False, self._to_bool)
        self.show_target_line = self._ensure_and_get(s, "show_target_line", False, self._to_bool)
        self.show_target_prediction_line = self._ensure_and_get(s, "show_target_prediction_line", False, self._to_bool)
        self.show_bScope_box = self._ensure_and_get(s, "show_bScope_box", False, self._to_bool)
        self.show_history_points = self._ensure_and_get(s, "show_history_points", False, self._to_bool)
        self.debug_window_always_on_top = self._ensure_and_get(s, "debug_window_always_on_top", False, self._to_bool)
        self.spawn_window_pos_x = self._ensure_and_get(s, "spawn_window_pos_x", 100, int)
        self.spawn_window_pos_y = self._ensure_and_get(s, "spawn_window_pos_y", 100, int)
        self.debug_window_scale_percent = self._ensure_and_get(s, "debug_window_scale_percent", 100, int)
        self.debug_window_screenshot_key = self._ensure_and_get(s, "debug_window_screenshot_key", "F12", str)

        self.debug_window_name = self.window_name

    @staticmethod
    def _to_bool(v: str) -> bool:
        return str(v).strip().lower() in {"1", "true", "yes", "on"}

    def _get_random_window_name(self) -> str:
        try:
            if self.WINDOW_NAMES_PATH.exists():
                lines = self.WINDOW_NAMES_PATH.read_text(encoding="utf-8").splitlines()
                return random.choice([ln for ln in lines if ln.strip()]) if lines else "Calculator"
            logger.warning("[Config] window_names.txt not found. Using default window name.")
            return "Calculator"
        except Exception as e:
            logger.error(f"[Config] Failed to read window_names.txt: {e}. Using default.")
            return "Calculator"


cfg = Config()
