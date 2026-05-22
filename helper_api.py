from __future__ import annotations

import configparser
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from helper_modules.common import DEVICE_OPTIONS, list_last_checkpoints, list_models, list_pt_models
from logic.buttons import Buttons


PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "config.ini"
VERSION_PATH = PROJECT_DIR / "version"
MODELS_DIR = PROJECT_DIR / "models"
UI_DIST_DIR = PROJECT_DIR / "helper_ui" / "dist"
CUDA_FILE_NAME = "cuda_12.8.0_571.96_windows.exe"
CUDA_URL = f"https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/{CUDA_FILE_NAME}"
CONFIG_LOCK = threading.RLock()
STREAM_STATUS_PREFIX = "__SUNONE_HELPER_STREAM_STATUS__"
HELPER_TOKEN_COOKIE = "sunone_helper_token"
HELPER_TOKEN_HEADER = "x-sunone-helper-token"
HELPER_API_TOKEN = os.environ.get("SUNONE_HELPER_TOKEN") or secrets.token_urlsafe(32)
ALLOWED_ORIGINS = ["http://127.0.0.1:8501", "http://localhost:8501"]
SYSTEM_META_CACHE_PATH = PROJECT_DIR / ".helper_system_meta_cache.json"
SYSTEM_META_CACHE_TTL_SECONDS = 3600
SYSTEM_META_CACHE_LOCK = threading.RLock()
SYSTEM_STATUS_CACHE: dict[str, Any] | None = None
SYSTEM_STATUS_CACHE_EXPIRES_AT = 0.0

FIELD_MAP: dict[str, tuple[str, str, str, Any]] = {
    "detection_window_width": ("Detection window", "detection_window_width", "int", 640),
    "detection_window_height": ("Detection window", "detection_window_height", "int", 640),
    "circle_capture": ("Detection window", "circle_capture", "bool", False),
    "capture_fps": ("Capture Methods", "capture_fps", "int", 60),
    "bettercam_monitor_id": ("Capture Methods", "bettercam_monitor_id", "int", 0),
    "bettercam_gpu_id": ("Capture Methods", "bettercam_gpu_id", "int", 0),
    "obs_camera_id": ("Capture Methods", "obs_camera_id", "str", "auto"),
    "body_y_offset": ("Aim", "body_y_offset", "float", 0.1),
    "hideout_targets": ("Aim", "hideout_targets", "bool", True),
    "disable_headshot": ("Aim", "disable_headshot", "bool", False),
    "disable_prediction": ("Aim", "disable_prediction", "bool", False),
    "prediction_interval": ("Aim", "prediction_interval", "float", 0.3),
    "third_person": ("Aim", "third_person", "bool", False),
    "hotkey_exit": ("Hotkeys", "hotkey_exit", "str", "F2"),
    "hotkey_pause": ("Hotkeys", "hotkey_pause", "str", "F3"),
    "hotkey_reload_config": ("Hotkeys", "hotkey_reload_config", "str", "F4"),
    "mouse_dpi": ("Mouse", "mouse_dpi", "int", 800),
    "mouse_sensitivity": ("Mouse", "mouse_sensitivity", "float", 2.0),
    "mouse_fov_width": ("Mouse", "mouse_fov_width", "int", 40),
    "mouse_fov_height": ("Mouse", "mouse_fov_height", "int", 40),
    "mouse_min_speed_multiplier": ("Mouse", "mouse_min_speed_multiplier", "float", 1.0),
    "mouse_max_speed_multiplier": ("Mouse", "mouse_max_speed_multiplier", "float", 1.5),
    "mouse_lock_target": ("Mouse", "mouse_lock_target", "bool", False),
    "mouse_auto_aim": ("Mouse", "mouse_auto_aim", "bool", False),
    "mouse_ghub": ("Mouse", "mouse_ghub", "bool", False),
    "mouse_rzr": ("Mouse", "mouse_rzr", "bool", False),
    "auto_shoot": ("Shooting", "auto_shoot", "bool", False),
    "triggerbot": ("Shooting", "triggerbot", "bool", False),
    "force_click": ("Shooting", "force_click", "bool", False),
    "bscope_multiplier": ("Shooting", "bscope_multiplier", "float", 1.0),
    "arduino_move": ("Arduino", "arduino_move", "bool", False),
    "arduino_shoot": ("Arduino", "arduino_shoot", "bool", False),
    "arduino_port": ("Arduino", "arduino_port", "str", "COM3"),
    "arduino_baudrate": ("Arduino", "arduino_baudrate", "int", 115200),
    "arduino_16_bit_mouse": ("Arduino", "arduino_16_bit_mouse", "bool", False),
    "ai_model_name": ("AI", "ai_model_name", "str", ""),
    "ai_model_image_size": ("AI", "ai_model_image_size", "int", 640),
    "ai_conf": ("AI", "ai_conf", "float", 0.1),
    "ai_device": ("AI", "ai_device", "str", "0"),
    "ai_enable_amd": ("AI", "ai_enable_amd", "bool", False),
    "disable_tracker": ("AI", "disable_tracker", "bool", False),
    "show_overlay": ("overlay", "show_overlay", "bool", False),
    "overlay_show_borders": ("overlay", "overlay_show_borders", "bool", True),
    "overlay_show_boxes": ("overlay", "overlay_show_boxes", "bool", False),
    "overlay_show_target_line": ("overlay", "overlay_show_target_line", "bool", False),
    "overlay_show_target_prediction_line": ("overlay", "overlay_show_target_prediction_line", "bool", False),
    "overlay_show_labels": ("overlay", "overlay_show_labels", "bool", False),
    "overlay_show_conf": ("overlay", "overlay_show_conf", "bool", False),
    "show_window": ("Debug window", "show_window", "bool", True),
    "show_detection_speed": ("Debug window", "show_detection_speed", "bool", False),
    "show_window_fps": ("Debug window", "show_window_fps", "bool", False),
    "show_boxes": ("Debug window", "show_boxes", "bool", True),
    "show_labels": ("Debug window", "show_labels", "bool", False),
    "show_conf": ("Debug window", "show_conf", "bool", True),
    "show_target_line": ("Debug window", "show_target_line", "bool", False),
    "show_target_prediction_line": ("Debug window", "show_target_prediction_line", "bool", False),
    "show_bscope_box": ("Debug window", "show_bscope_box", "bool", False),
    "show_history_points": ("Debug window", "show_history_points", "bool", False),
    "debug_window_always_on_top": ("Debug window", "debug_window_always_on_top", "bool", True),
    "spawn_window_pos_x": ("Debug window", "spawn_window_pos_x", "int", 100),
    "spawn_window_pos_y": ("Debug window", "spawn_window_pos_y", "int", 100),
    "debug_window_scale_percent": ("Debug window", "debug_window_scale_percent", "int", 100),
    "debug_window_screenshot_key": ("Debug window", "debug_window_screenshot_key", "str", "F12"),
}


class ConfigUpdateRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)


class ConfigFieldUpdateRequest(BaseModel):
    key: str
    value: Any = None


class ExportRequest(BaseModel):
    model_name: str
    image_size: int = 640
    precision: str = "half"
    data_yaml_path: str = "logic/game.yaml"
    add_nms: bool = True


class TrainRequest(BaseModel):
    selected_model_path: str
    resume: bool = False
    data_yaml: str = "logic/game.yaml"
    epochs: int = 80
    img_size: int = 640
    use_cache: bool = False
    augment: bool = True
    augment_degrees: int = 5
    augment_flipud: float = 0.2
    train_device: str | int = "0"
    batch_size: int | float = -1
    profile: bool = False
    disable_wandb: bool = True


def _parser() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    with CONFIG_LOCK:
        parser.read(CONFIG_PATH, encoding="utf-8")
    return parser


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_version(lines: list[str]) -> dict[str, str | int]:
    result: dict[str, str | int] = {"app_version": 0, "config_version": 0}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.strip().split("=", 1)
        if key == "app":
            result["app_version"] = value
        elif key == "config":
            result["config_version"] = value
    return result


def _offline_version() -> dict[str, str | int]:
    if not VERSION_PATH.exists():
        return {"app_version": 0, "config_version": 0}
    return _parse_version(VERSION_PATH.read_text(encoding="utf-8").splitlines())


def _online_version() -> dict[str, str | int]:
    try:
        response = requests.get("https://raw.githubusercontent.com/SunOner/sunone_aimbot/main/version", timeout=30)
        response.raise_for_status()
        return _parse_version(response.text.splitlines())
    except requests.RequestException:
        return {"app_version": 0, "config_version": 0}


def _find_cuda_paths(version: str = "12.8") -> list[str]:
    return [item for item in os.environ.get("PATH", "").split(";") if "cuda" in item.lower() and version in item]


def _python_probe(script: str, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": str(exc)}

    if result.returncode != 0:
        return {"available": False, "error": (result.stderr or result.stdout).strip()}

    output_lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not output_lines:
        return {"available": False, "error": "Probe returned no output."}

    try:
        return json.loads(output_lines[-1])
    except json.JSONDecodeError:
        return {"available": False, "error": result.stdout.strip()}


def _torch_info() -> dict[str, Any]:
    info = _python_probe(
        "import json\n"
        "import sys\n"
        "try:\n"
        "    import torch\n"
        "    devices = []\n"
        "    if torch.cuda.is_available():\n"
        "        devices = [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())]\n"
        "    print(json.dumps({\n"
        "        'available': True,\n"
        "        'cuda': bool(torch.cuda.is_available()),\n"
        "        'version': str(torch.__version__),\n"
        "        'torch_cuda': str(getattr(torch.version, 'cuda', '') or ''),\n"
        "        'device_count': int(torch.cuda.device_count()),\n"
        "        'devices': devices,\n"
        "        'executable': sys.executable,\n"
        "        'torch_file': getattr(torch, '__file__', ''),\n"
        "    }))\n"
        "except ModuleNotFoundError as exc:\n"
        "    print(json.dumps({'available': False, 'cuda': False, 'error': str(exc), 'executable': sys.executable}))\n"
        "except Exception as exc:\n"
        "    print(json.dumps({'available': False, 'cuda': False, 'error': str(exc), 'executable': sys.executable}))\n"
    )
    if not info.get("available"):
        return {
            "available": False,
            "cuda": False,
            "version": None,
            "torch_cuda": None,
            "device_count": 0,
            "devices": [],
            "executable": info.get("executable") or sys.executable,
            "torch_file": None,
            "error": info.get("error"),
        }
    return {
        "available": True,
        "cuda": bool(info.get("cuda")),
        "version": str(info.get("version") or ""),
        "torch_cuda": str(info.get("torch_cuda") or ""),
        "device_count": int(info.get("device_count") or 0),
        "devices": info.get("devices") if isinstance(info.get("devices"), list) else [],
        "executable": str(info.get("executable") or sys.executable),
        "torch_file": str(info.get("torch_file") or ""),
        "error": info.get("error"),
    }


def _torch_gpu_support() -> bool | None:
    info = _torch_info()
    if not info.get("available"):
        return None
    return bool(info.get("cuda"))


def _tensorrt_info() -> dict[str, Any]:
    info = _python_probe(
        "import json\n"
        "try:\n"
        "    import tensorrt\n"
        "    print(json.dumps({'available': True, 'version': str(tensorrt.__version__)}))\n"
        "except ModuleNotFoundError:\n"
        "    print(json.dumps({'available': False, 'version': None}))\n"
    )
    if not info.get("available"):
        return {"available": False, "version": None}
    return {"available": True, "version": str(info.get("version"))}


def _ultralytics_version() -> str | None:
    info = _python_probe(
        "import json\n"
        "try:\n"
        "    import ultralytics\n"
        "    print(json.dumps({'available': True, 'version': str(ultralytics.__version__)}))\n"
        "except ModuleNotFoundError:\n"
        "    print(json.dumps({'available': False, 'version': None}))\n"
    )
    if not info.get("available"):
        return None
    return str(info.get("version"))


def _read_value(parser: configparser.ConfigParser, section: str, option: str, value_type: str, default: Any) -> Any:
    if value_type == "bool":
        return parser.getboolean(section, option, fallback=default)
    if value_type == "int":
        return parser.getint(section, option, fallback=default)
    if value_type == "float":
        return parser.getfloat(section, option, fallback=default)
    return parser.get(section, option, fallback=default)


def _coerce_value(value: Any, value_type: str) -> Any:
    if value_type == "bool":
        return _as_bool(value)
    if value_type == "int":
        return int(value)
    if value_type == "float":
        return float(value)
    return str(value)


def _set_value(parser: configparser.ConfigParser, section: str, option: str, value: Any) -> None:
    if not parser.has_section(section):
        parser.add_section(section)
    if isinstance(value, bool):
        parser.set(section, option, "True" if value else "False")
    else:
        parser.set(section, option, str(value))


def _write_config(parser: configparser.ConfigParser) -> None:
    temp_path: Path | None = None
    with CONFIG_LOCK:
        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                dir=PROJECT_DIR,
                encoding="utf-8",
                mode="w",
                suffix=".ini",
            ) as file:
                parser.write(file)
                temp_path = Path(file.name)
            os.replace(temp_path, CONFIG_PATH)
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass


def _config_file_version() -> dict[str, int]:
    try:
        stat = CONFIG_PATH.stat()
    except FileNotFoundError:
        return {"mtime_ns": 0, "size": 0}
    return {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}


def _set_capture_method(parser: configparser.ConfigParser, value: Any) -> None:
    capture = str(value).lower()
    if capture not in {"bettercam", "obs", "mss"}:
        raise ValueError(f"Unknown capture method: {value}")
    _set_value(parser, "Capture Methods", "bettercam_capture", capture == "bettercam")
    _set_value(parser, "Capture Methods", "obs_capture", capture == "obs")
    _set_value(parser, "Capture Methods", "mss_capture", capture == "mss")


def _set_hotkey_targeting(parser: configparser.ConfigParser, value: Any) -> None:
    if isinstance(value, list):
        _set_value(parser, "Hotkeys", "hotkey_targeting", ",".join(str(item) for item in value))
    else:
        _set_value(parser, "Hotkeys", "hotkey_targeting", str(value))


def _snapshot_config() -> dict[str, Any]:
    parser = _parser()
    config: dict[str, Any] = {}
    for key, (section, option, value_type, default) in FIELD_MAP.items():
        config[key] = _read_value(parser, section, option, value_type, default)

    if parser.getboolean("Capture Methods", "obs_capture", fallback=False):
        config["capture_method"] = "obs"
    elif parser.getboolean("Capture Methods", "mss_capture", fallback=True):
        config["capture_method"] = "mss"
    else:
        config["capture_method"] = "bettercam"

    raw_targeting = parser.get("Hotkeys", "hotkey_targeting", fallback="")
    config["hotkey_targeting"] = [item.strip() for item in raw_targeting.split(",") if item.strip()]
    return config


def _save_config(values: dict[str, Any]) -> None:
    with CONFIG_LOCK:
        parser = _parser()
        for key, (section, option, value_type, _) in FIELD_MAP.items():
            if key in values:
                _set_value(parser, section, option, _coerce_value(values[key], value_type))

        if "capture_method" in values:
            _set_capture_method(parser, values["capture_method"])

        if "hotkey_targeting" in values:
            _set_hotkey_targeting(parser, values["hotkey_targeting"])

        _write_config(parser)


def _save_config_field(key: str, value: Any) -> None:
    with CONFIG_LOCK:
        parser = _parser()
        if key == "capture_method":
            _set_capture_method(parser, value)
        elif key == "hotkey_targeting":
            _set_hotkey_targeting(parser, value)
        elif key in FIELD_MAP:
            section, option, value_type, _ = FIELD_MAP[key]
            _set_value(parser, section, option, _coerce_value(value, value_type))
        else:
            raise KeyError(key)

        _write_config(parser)


def _run_command(command: list[str]) -> tuple[bool, str]:
    result = subprocess.run(command, cwd=PROJECT_DIR, capture_output=True, text=True)
    output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    return result.returncode == 0, output


def _format_command(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def _stream_status(ok: bool, message: str, **extra: Any) -> str:
    payload = json.dumps({"ok": ok, "message": message, **extra}, separators=(",", ":"))
    return f"\n{STREAM_STATUS_PREFIX}{payload}\n"


def _split_stream_result(raw_output: str) -> tuple[str, dict[str, Any] | None]:
    marker_index = raw_output.rfind(STREAM_STATUS_PREFIX)
    if marker_index < 0:
        return raw_output, None
    output = raw_output[:marker_index].strip()
    status_line = raw_output[marker_index + len(STREAM_STATUS_PREFIX) :].strip().splitlines()[0]
    try:
        status = json.loads(status_line)
    except json.JSONDecodeError:
        status = None
    return output, status if isinstance(status, dict) else None


def _stream_commands(commands: list[list[str]], success_message: str, failure_message: str):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    for command in commands:
        yield f"$ {_format_command(command)}\n"
        try:
            process = subprocess.Popen(
                command,
                cwd=PROJECT_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            yield f"Failed to start command: {exc}\n"
            yield _stream_status(False, failure_message)
            return

        if process.stdout is not None:
            for line in process.stdout:
                yield line

        returncode = process.wait()
        if returncode != 0:
            yield f"\nCommand exited with code {returncode}.\n"
            yield _stream_status(False, failure_message)
            return

        yield "\n"

    yield _stream_status(True, success_message)


def _stream_python_script(
    script: str,
    success_message: str,
    failure_message: str,
    *,
    env_overrides: dict[str, str] | None = None,
    cleanup_paths: list[Path] | None = None,
):
    cleanup_paths = cleanup_paths or []
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", dir=PROJECT_DIR, encoding="utf-8", mode="w") as temp_script:
            temp_script.write(script)
            temp_path = Path(temp_script.name)

        command = [sys.executable, str(temp_path)]
        yield f"$ {_format_command(command)}\n"

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if env_overrides:
            env.update(env_overrides)

        try:
            process = subprocess.Popen(
                command,
                cwd=PROJECT_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            yield f"Failed to start process: {exc}\n"
            yield _stream_status(False, failure_message)
            return

        if process.stdout is not None:
            for line in process.stdout:
                yield line

        returncode = process.wait()
        if returncode != 0:
            yield f"\nProcess exited with code {returncode}.\n"
            yield _stream_status(False, failure_message)
            return

        yield _stream_status(True, success_message)
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        for cleanup_path in cleanup_paths:
            try:
                cleanup_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def _stream_download_cuda():
    destination = PROJECT_DIR / CUDA_FILE_NAME
    bytes_downloaded = 0
    last_report = 0.0
    try:
        yield f"Downloading {CUDA_FILE_NAME}...\n"
        with requests.get(CUDA_URL, stream=True, timeout=60) as response:
            response.raise_for_status()
            total_bytes = int(response.headers.get("content-length", 0) or 0)
            with destination.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file.write(chunk)
                    bytes_downloaded += len(chunk)
                    now = time.monotonic()
                    if now - last_report >= 0.8:
                        last_report = now
                        if total_bytes:
                            percent = bytes_downloaded * 100 / total_bytes
                            yield f"Downloaded {bytes_downloaded / 1024 / 1024:.1f} MB / {total_bytes / 1024 / 1024:.1f} MB ({percent:.1f}%)\n"
                        else:
                            yield f"Downloaded {bytes_downloaded / 1024 / 1024:.1f} MB\n"
        yield f"Downloaded to {destination}\n"
        try:
            subprocess.Popen([str(destination)], cwd=PROJECT_DIR)
        except OSError as exc:
            yield f"CUDA downloaded but failed to launch: {exc}\n"
            yield _cuda_manual_launch_hint(destination)
            yield _stream_status(False, "CUDA downloaded, but the installer requires manual launch.")
            return
        _invalidate_system_meta_cache()
        yield _stream_status(True, "CUDA installer downloaded and launched.")
    except (requests.RequestException, OSError) as exc:
        yield f"Download failed: {exc}\n"
        yield _stream_status(False, "CUDA download failed.")


def _format_torch_info(info: dict[str, Any]) -> str:
    devices = ", ".join(str(device) for device in info.get("devices") or []) or "none"
    lines = [
        f"Python executable: {info.get('executable') or sys.executable}",
        f"Torch installed: {bool(info.get('available'))}",
        f"Torch version: {info.get('version') or 'not installed'}",
        f"Torch CUDA build: {info.get('torch_cuda') or 'none'}",
        f"torch.cuda.is_available(): {bool(info.get('cuda'))}",
        f"CUDA device count: {info.get('device_count') or 0}",
        f"CUDA devices: {devices}",
    ]
    if info.get("torch_file"):
        lines.append(f"Torch file: {info['torch_file']}")
    if info.get("error"):
        lines.append(f"Probe error: {info['error']}")
    return "\n".join(lines)


def _ensure_torch_cuda_for_aimbot() -> None:
    config = _snapshot_config()
    if str(config.get("ai_device", "")).strip().lower() == "cpu":
        return

    info = _torch_info()
    if info.get("cuda") is True:
        return

    raise HTTPException(
        status_code=400,
        detail={
            "message": "PyTorch CUDA is not available for the selected AI device.",
            "output": (
                "Aimbot is configured to use GPU, but PyTorch does not see CUDA in this Python environment.\n"
                f"{_format_torch_info(info)}\n\n"
                "Use Reinstall Torch in Helper, or run:\n"
                "pip uninstall torch torchvision torchaudio -y\n"
                "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"
            ),
        },
    )


def _cuda_manual_launch_hint(destination: Path) -> str:
    return (
        "Manual launch required:\n"
        f"1. Run this installer as Administrator: {destination}\n"
        f'2. Or run in PowerShell: Start-Process -FilePath "{destination}" -Verb RunAs\n'
    )


def _torch_reinstall_commands() -> list[list[str]]:
    return [
        [sys.executable, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"],
        [sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu128"],
    ]


def _tensorrt_reinstall_commands() -> list[list[str]]:
    return [
        [sys.executable, "-m", "pip", "uninstall", "tensorrt", "tensorrt-bindings", "tensorrt-cu12", "tensorrt-cu12_bindings", "tensorrt-cu12_libs", "tensorrt-libs", "-y"],
        [sys.executable, "-m", "pip", "install", "tensorrt"],
    ]


def _download_file(url: str, destination: Path) -> tuple[bool, str]:
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with destination.open("wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
        return True, "Downloaded"
    except (requests.RequestException, OSError) as exc:
        return False, str(exc)


def _reinstall_aimbot() -> tuple[bool, str]:
    archive = PROJECT_DIR / "main.zip"
    extract_dir = PROJECT_DIR / "temp_extract"
    repo_root = extract_dir / "sunone_aimbot-main"

    ok, message = _download_file(
        "https://github.com/SunOner/sunone_aimbot/archive/refs/heads/main.zip",
        archive,
    )
    if not ok:
        return False, message

    try:
        with zipfile.ZipFile(archive, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as exc:
        return False, f"Unpack failed: {exc}"

    online_cfg = int(_online_version().get("config_version", 0) or 0)
    offline_cfg = int(_offline_version().get("config_version", 0) or 0)
    replace_config = online_cfg != offline_cfg

    try:
        for source_file in repo_root.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(repo_root)
            if relative.as_posix() == "config.ini" and not replace_config:
                continue
            destination = PROJECT_DIR / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                destination.unlink()
            source_file.replace(destination)
    except Exception as exc:
        return False, f"Move files failed: {exc}"
    finally:
        if archive.exists():
            archive.unlink()
        if extract_dir.exists():
            for item in extract_dir.rglob("*"):
                try:
                    if item.is_file():
                        item.unlink()
                except OSError:
                    pass
            try:
                for item in sorted(extract_dir.rglob("*"), reverse=True):
                    if item.is_dir():
                        item.rmdir()
                extract_dir.rmdir()
            except OSError:
                pass

    return True, "Aimbot files were updated from GitHub."


def _status() -> dict[str, Any]:
    torch_info = _torch_info()
    return {
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "ultralytics": _ultralytics_version(),
        "aimbot_versions": {"offline": _offline_version(), "online": _online_version()},
        "cuda": {"available": len(_find_cuda_paths()) > 0, "paths": _find_cuda_paths()},
        "torch": torch_info,
        "torch_gpu_support": None if not torch_info.get("available") else bool(torch_info.get("cuda")),
        "tensorrt": _tensorrt_info(),
    }


def _invalidate_system_meta_cache() -> None:
    global SYSTEM_STATUS_CACHE, SYSTEM_STATUS_CACHE_EXPIRES_AT
    with SYSTEM_META_CACHE_LOCK:
        SYSTEM_STATUS_CACHE = None
        SYSTEM_STATUS_CACHE_EXPIRES_AT = 0.0
    try:
        SYSTEM_META_CACHE_PATH.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _read_system_status_cache(now: float) -> dict[str, Any] | None:
    try:
        cached = json.loads(SYSTEM_META_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    expires_at = float(cached.get("expires_at", 0) or 0)
    status = cached.get("status")
    if not isinstance(status, dict):
        legacy_meta = cached.get("meta")
        status = legacy_meta.get("status") if isinstance(legacy_meta, dict) else None
    if expires_at <= now or not isinstance(status, dict):
        return None

    return status


def _write_system_status_cache(status: dict[str, Any], expires_at: float) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=PROJECT_DIR,
            encoding="utf-8",
            mode="w",
            suffix=".meta-cache.json",
        ) as file:
            json.dump({"expires_at": expires_at, "status": status}, file)
            temp_path = Path(file.name)
        os.replace(temp_path, SYSTEM_META_CACHE_PATH)
    except OSError:
        pass
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _cached_status(force: bool = False) -> dict[str, Any]:
    global SYSTEM_STATUS_CACHE, SYSTEM_STATUS_CACHE_EXPIRES_AT
    now_monotonic = time.monotonic()
    now_epoch = time.time()
    with SYSTEM_META_CACHE_LOCK:
        if not force and SYSTEM_STATUS_CACHE is not None and now_monotonic < SYSTEM_STATUS_CACHE_EXPIRES_AT:
            return dict(SYSTEM_STATUS_CACHE)
        if not force:
            cached_status = _read_system_status_cache(now_epoch)
            if cached_status is not None:
                SYSTEM_STATUS_CACHE = dict(cached_status)
                SYSTEM_STATUS_CACHE_EXPIRES_AT = now_monotonic + SYSTEM_META_CACHE_TTL_SECONDS
                return dict(cached_status)

    status = _status()
    expires_at_epoch = time.time() + SYSTEM_META_CACHE_TTL_SECONDS
    with SYSTEM_META_CACHE_LOCK:
        SYSTEM_STATUS_CACHE = dict(status)
        SYSTEM_STATUS_CACHE_EXPIRES_AT = time.monotonic() + SYSTEM_META_CACHE_TTL_SECONDS
        _write_system_status_cache(status, expires_at_epoch)

    return status


def _system_meta(force: bool = False) -> dict[str, Any]:
    models = list_models(MODELS_DIR)
    pt_models = list_pt_models(MODELS_DIR)
    return {
        "ok": True,
        "status": _cached_status(force=force),
        "device_options": DEVICE_OPTIONS,
        "hotkey_options": list(Buttons.KEY_CODES.keys()),
        "models": models,
        "pt_models": pt_models,
        "last_checkpoints": list_last_checkpoints(r"runs\detect"),
        "pretrained_models": pt_models,
        "obs_camera_options": ["auto"] + [str(i) for i in range(11)],
    }


def _resolve_train_model_path(model_path: str) -> str:
    requested = Path(model_path)
    if requested.name == model_path and (MODELS_DIR / requested.name).is_file():
        return str(Path("models") / requested.name)

    candidate = requested if requested.is_absolute() else PROJECT_DIR / requested
    if not candidate.is_file():
        raise HTTPException(status_code=400, detail=f"Model not found: {model_path}")

    try:
        return str(candidate.relative_to(PROJECT_DIR))
    except ValueError:
        return str(candidate)


def _build_train_script(payload: TrainRequest, train_device: str | int, selected_model_path: str) -> str:
    lines = [
        "from ultralytics import YOLO",
        "",
        "if __name__ == '__main__':",
        f"    print('Loading model:', {selected_model_path!r}, flush=True)",
        f"    m = YOLO({selected_model_path!r})",
        "    print('Starting training...', flush=True)",
        "    m.train(",
        f"        device={train_device!r},",
        f"        batch={payload.batch_size},",
        f"        resume={payload.resume},",
    ]
    if not payload.resume:
        lines.extend(
            [
                f"        data={payload.data_yaml!r},",
                f"        epochs={payload.epochs},",
                f"        imgsz={payload.img_size},",
                f"        profile={payload.profile},",
                f"        cache={payload.use_cache},",
                f"        augment={payload.augment},",
            ]
        )
        if payload.augment:
            lines.extend([f"        degrees={payload.augment_degrees},", f"        flipud={payload.augment_flipud},"])
    lines.append("    )")
    lines.append("    print('Training completed.', flush=True)")
    return "\n".join(lines)


def _train_script_and_env(payload: TrainRequest) -> tuple[str, dict[str, str]]:
    train_device: str | int = payload.train_device
    if isinstance(train_device, str) and train_device != "cpu":
        try:
            train_device = int(train_device)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid train device: {payload.train_device}") from exc
    selected_model_path = _resolve_train_model_path(payload.selected_model_path)
    return _build_train_script(payload, train_device, selected_model_path), {
        "WANDB_DISABLED": "true" if payload.disable_wandb else "false"
    }


def _stream_train(payload: TrainRequest):
    script, env_overrides = _train_script_and_env(payload)
    yield from _stream_python_script(
        script,
        "Training completed.",
        "Training failed.",
        env_overrides=env_overrides,
    )
    _invalidate_system_meta_cache()


def _export_params(payload: ExportRequest) -> dict[str, Any]:
    params: dict[str, Any] = {
        "format": "engine",
        "imgsz": payload.image_size,
        "half": payload.precision == "half",
        "int8": payload.precision == "int8",
        "device": 0,
        "nms": payload.add_nms and payload.precision != "int8",
    }
    if payload.precision == "int8":
        params["data"] = payload.data_yaml_path or "logic/game.yaml"
    return params


def _export_model_path(model_name: str) -> Path:
    model_path = MODELS_DIR / model_name
    if not model_path.exists():
        raise HTTPException(status_code=400, detail=f"Model not found: {model_name}")
    return model_path


def _build_export_script(model_path: Path, params: dict[str, Any]) -> str:
    return "\n".join(
        [
            "from ultralytics import YOLO",
            "",
            "if __name__ == '__main__':",
            f"    exported = YOLO({str(model_path)!r}).export(**{params!r})",
            "    print(f'Exported path: {exported}', flush=True)",
        ]
    )


def _stream_export(payload: ExportRequest, model_path: Path):
    yield from _stream_python_script(
        _build_export_script(model_path, _export_params(payload)),
        "Model exported successfully.",
        "Export failed.",
    )
    _invalidate_system_meta_cache()


def _build_tests_script(params: dict[str, Any]) -> str:
    return "\n".join(
        [
            "import cv2",
            "import win32con",
            "import win32gui",
            "from ultralytics import YOLO",
            "",
            f"model_path = {params['model_path']!r}",
            f"video_source = {params['video_source']!r}",
            f"topmost = {bool(params['topmost'])!r}",
            f"model_image_size = {int(params['model_image_size'])!r}",
            f"device = {params['device']!r}",
            f"input_delay = {int(params['input_delay'])!r}",
            f"resize_factor = {int(params['resize_factor'])!r}",
            f"ai_conf = {float(params['ai_conf'])!r}",
            "",
            "print('Loading model:', model_path, flush=True)",
            "model = YOLO(model_path, task='detect')",
            "print('Opening video source:', video_source, flush=True)",
            "cap = cv2.VideoCapture(video_source)",
            "if not cap.isOpened():",
            "    raise RuntimeError('Could not open video source.')",
            "window_name = 'Detections test'",
            "cv2.namedWindow(window_name)",
            "if topmost:",
            "    hwnd = win32gui.FindWindow(None, window_name)",
            "    if hwnd:",
            "        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)",
            "frames = 0",
            "try:",
            "    while cap.isOpened():",
            "        ok, frame = cap.read()",
            "        if not ok:",
            "            break",
            "        result = model(frame, stream=False, show=False, imgsz=model_image_size, device=device, verbose=False, conf=ai_conf)",
            "        annotated = result[0].plot()",
            "        frame_height, frame_width = frame.shape[:2]",
            "        dim = (int(frame_width * resize_factor / 100), int(frame_height * resize_factor / 100))",
            "        cv2.resizeWindow(window_name, dim)",
            "        cv2.imshow(window_name, cv2.resize(annotated, dim, cv2.INTER_NEAREST))",
            "        frames += 1",
            "        if frames == 1 or frames % 50 == 0:",
            "            print(f'Processed {frames} frames', flush=True)",
            "        if cv2.waitKey(input_delay) & 0xFF == ord('q'):",
            "            break",
            "finally:",
            "    cap.release()",
            "    cv2.destroyAllWindows()",
            "    del model",
            "print(f'Test window closed after {frames} frames.', flush=True)",
        ]
    )


async def _save_uploaded_video(video_file: UploadFile) -> Path:
    temp_video_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=PROJECT_DIR, mode="wb") as temp_video:
            temp_video_path = Path(temp_video.name)
            while True:
                chunk = await video_file.read(1024 * 1024)
                if not chunk:
                    break
                temp_video.write(chunk)
    except OSError as exc:
        if temp_video_path and temp_video_path.exists():
            try:
                temp_video_path.unlink()
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Could not save uploaded video: {exc}") from exc
    return temp_video_path


async def _tests_script_and_cleanup(
    input_model: str,
    source_method: str,
    topmost: bool,
    model_image_size: int,
    input_device: str,
    input_delay: int,
    resize_factor: int,
    ai_conf: float,
    video_file: UploadFile | None,
) -> tuple[str, list[Path]]:
    model_path = MODELS_DIR / input_model
    if not model_path.exists():
        raise HTTPException(status_code=400, detail=f"Model not found: {input_model}")
    if input_device != "cpu" and not _torch_gpu_support():
        raise HTTPException(status_code=400, detail="CUDA is not available for GPU test execution.")

    cleanup_paths: list[Path] = []
    if source_method == "Default":
        video_source = PROJECT_DIR / "media" / "tests" / "test_det.mp4"
        if not video_source.exists():
            raise HTTPException(status_code=400, detail="Default test video not found.")
    else:
        if video_file is None:
            raise HTTPException(status_code=400, detail="Video file is required.")
        video_source = await _save_uploaded_video(video_file)
        cleanup_paths.append(video_source)

    if input_device == "cpu":
        device: str | int = "cpu"
    else:
        try:
            device = int(input_device)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid test device: {input_device}") from exc
    script = _build_tests_script(
        {
            "model_path": str(model_path),
            "video_source": str(video_source),
            "topmost": topmost,
            "model_image_size": model_image_size,
            "device": device,
            "input_delay": input_delay,
            "resize_factor": resize_factor,
            "ai_conf": ai_conf,
        }
    )
    return script, cleanup_paths


def _stream_tests(script: str, cleanup_paths: list[Path]):
    yield from _stream_python_script(
        script,
        "Detection test completed.",
        "Detection test failed.",
        cleanup_paths=cleanup_paths,
    )


def _set_helper_cookie(response: Response) -> Response:
    response.set_cookie(
        HELPER_TOKEN_COOKIE,
        HELPER_API_TOKEN,
        path="/",
        httponly=False,
        samesite="strict",
    )
    return response


def _is_valid_helper_token(request: Request) -> bool:
    header_token = request.headers.get(HELPER_TOKEN_HEADER, "")
    cookie_token = request.cookies.get(HELPER_TOKEN_COOKIE, "")
    return (
        secrets.compare_digest(header_token, HELPER_API_TOKEN)
        and secrets.compare_digest(cookie_token, HELPER_API_TOKEN)
    )


app = FastAPI(title="Sunone Helper API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Sunone-Helper-Token"],
)


@app.middleware("http")
async def require_helper_token(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not _is_valid_helper_token(request):
            return JSONResponse({"ok": False, "message": "Invalid helper session token."}, status_code=403)
    return await call_next(request)


@app.get("/api/system/meta")
def api_meta(force: bool = False) -> dict[str, Any]:
    return _system_meta(force=force)


@app.get("/api/config")
def api_get_config() -> dict[str, Any]:
    return {"ok": True, "config": _snapshot_config(), "version": _config_file_version()}


@app.get("/api/config/version")
def api_get_config_version() -> dict[str, Any]:
    return {"ok": True, "version": _config_file_version()}


@app.post("/api/config")
def api_save_config(payload: ConfigUpdateRequest) -> dict[str, Any]:
    try:
        _save_config(payload.config)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid config value: {exc}") from exc
    return {"ok": True, "message": "Config saved successfully.", "config": _snapshot_config(), "version": _config_file_version()}


@app.patch("/api/config")
def api_save_config_field(payload: ConfigFieldUpdateRequest) -> dict[str, Any]:
    try:
        _save_config_field(payload.key, payload.value)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown config key: {payload.key}") from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid config value for {payload.key}: {exc}") from exc
    return {"ok": True, "message": "Config updated.", "config": _snapshot_config(), "version": _config_file_version()}


@app.post("/api/actions/run-aimbot")
def api_run_aimbot() -> dict[str, Any]:
    _ensure_torch_cuda_for_aimbot()
    subprocess.Popen([sys.executable, "run.py"], cwd=PROJECT_DIR)
    return {"ok": True, "message": "Aimbot started in a new process."}


@app.post("/api/actions/reinstall-torch")
def api_reinstall_torch() -> dict[str, Any]:
    if not _find_cuda_paths():
        raise HTTPException(status_code=400, detail="CUDA 12.8 not found in PATH.")
    commands = _torch_reinstall_commands()
    output: list[str] = []
    for command in commands:
        ok, cmd_output = _run_command(command)
        if cmd_output:
            output.append(cmd_output)
        if not ok:
            raise HTTPException(status_code=500, detail={"message": "Torch reinstall failed.", "output": "\n\n".join(output)})
    _invalidate_system_meta_cache()
    return {"ok": True, "message": "Torch reinstalled successfully.", "output": "\n\n".join(output)}


@app.post("/api/actions/reinstall-torch/stream")
def api_reinstall_torch_stream():
    if not _find_cuda_paths():
        raise HTTPException(status_code=400, detail="CUDA 12.8 not found in PATH.")
    _invalidate_system_meta_cache()
    return StreamingResponse(
        _stream_commands(_torch_reinstall_commands(), "Torch reinstalled successfully.", "Torch reinstall failed."),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/api/actions/reinstall-tensorrt")
def api_reinstall_tensorrt() -> dict[str, Any]:
    if not _find_cuda_paths():
        raise HTTPException(status_code=400, detail="CUDA 12.8 not found in PATH.")
    commands = _tensorrt_reinstall_commands()
    output: list[str] = []
    for command in commands:
        ok, cmd_output = _run_command(command)
        if cmd_output:
            output.append(cmd_output)
        if not ok:
            raise HTTPException(status_code=500, detail={"message": "TensorRT reinstall failed.", "output": "\n\n".join(output)})
    _invalidate_system_meta_cache()
    return {"ok": True, "message": "TensorRT reinstalled successfully.", "output": "\n\n".join(output)}


@app.post("/api/actions/reinstall-tensorrt/stream")
def api_reinstall_tensorrt_stream():
    if not _find_cuda_paths():
        raise HTTPException(status_code=400, detail="CUDA 12.8 not found in PATH.")
    _invalidate_system_meta_cache()
    return StreamingResponse(
        _stream_commands(_tensorrt_reinstall_commands(), "TensorRT reinstalled successfully.", "TensorRT reinstall failed."),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/api/actions/download-cuda")
def api_download_cuda() -> dict[str, Any]:
    destination = PROJECT_DIR / CUDA_FILE_NAME
    ok, message = _download_file(CUDA_URL, destination)
    if not ok:
        raise HTTPException(status_code=500, detail=message)
    try:
        subprocess.Popen([str(destination)], cwd=PROJECT_DIR)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "CUDA downloaded, but the installer requires manual launch.",
                "output": f"CUDA downloaded but failed to launch: {exc}\n{_cuda_manual_launch_hint(destination)}",
            },
        ) from exc
    _invalidate_system_meta_cache()
    return {"ok": True, "message": "CUDA installer downloaded and launched."}


@app.post("/api/actions/download-cuda/stream")
def api_download_cuda_stream():
    return StreamingResponse(
        _stream_download_cuda(),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/api/actions/reinstall-aimbot")
def api_reinstall_aimbot() -> dict[str, Any]:
    ok, message = _reinstall_aimbot()
    if not ok:
        raise HTTPException(status_code=500, detail=message)
    _invalidate_system_meta_cache()
    return {"ok": True, "message": message}


@app.post("/api/export")
def api_export(payload: ExportRequest) -> dict[str, Any]:
    from ultralytics import YOLO
    model_path = _export_model_path(payload.model_name)
    params = _export_params(payload)
    try:
        exported = YOLO(str(model_path)).export(**params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}") from exc
    _invalidate_system_meta_cache()
    return {"ok": True, "message": "Model exported successfully.", "path": str(exported)}


@app.post("/api/export/stream")
def api_export_stream(payload: ExportRequest):
    model_path = _export_model_path(payload.model_name)
    return StreamingResponse(
        _stream_export(payload, model_path),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/api/train")
def api_train(payload: TrainRequest) -> dict[str, Any]:
    script, env_overrides = _train_script_and_env(payload)
    raw_output = "".join(
        _stream_python_script(
            script,
            "Training completed.",
            "Training failed.",
            env_overrides=env_overrides,
        )
    )
    output, status = _split_stream_result(raw_output)
    if not status or status.get("ok") is False:
        raise HTTPException(
            status_code=500,
            detail={"message": (status or {}).get("message", "Training failed."), "output": output},
        )
    _invalidate_system_meta_cache()
    return {"ok": True, "message": status.get("message", "Training completed."), "output": output}


@app.post("/api/train/stream")
def api_train_stream(payload: TrainRequest):
    _train_script_and_env(payload)
    return StreamingResponse(
        _stream_train(payload),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/api/tests/run")
async def api_tests(
    input_model: str = Form(...),
    source_method: str = Form("Default"),
    topmost: bool = Form(True),
    model_image_size: int = Form(640),
    input_device: str = Form("0"),
    input_delay: int = Form(30),
    resize_factor: int = Form(80),
    ai_conf: float = Form(0.20),
    video_file: UploadFile | None = File(None),
) -> dict[str, Any]:
    script, cleanup_paths = await _tests_script_and_cleanup(
        input_model,
        source_method,
        topmost,
        model_image_size,
        input_device,
        input_delay,
        resize_factor,
        ai_conf,
        video_file,
    )
    raw_output = "".join(_stream_tests(script, cleanup_paths))
    output, status = _split_stream_result(raw_output)
    if not status or status.get("ok") is False:
        raise HTTPException(
            status_code=500,
            detail={"message": (status or {}).get("message", "Detection test failed."), "output": output},
        )
    return {"ok": True, "message": status.get("message", "Detection test completed."), "output": output}


@app.post("/api/tests/run/stream")
async def api_tests_stream(
    input_model: str = Form(...),
    source_method: str = Form("Default"),
    topmost: bool = Form(True),
    model_image_size: int = Form(640),
    input_device: str = Form("0"),
    input_delay: int = Form(30),
    resize_factor: int = Form(80),
    ai_conf: float = Form(0.20),
    video_file: UploadFile | None = File(None),
):
    script, cleanup_paths = await _tests_script_and_cleanup(
        input_model,
        source_method,
        topmost,
        model_image_size,
        input_device,
        input_delay,
        resize_factor,
        ai_conf,
        video_file,
    )
    return StreamingResponse(
        _stream_tests(script, cleanup_paths),
        media_type="text/plain; charset=utf-8",
    )


@app.get("/", include_in_schema=False, response_model=None)
def root_page():
    index = UI_DIST_DIR / "index.html"
    if index.exists():
        return _set_helper_cookie(FileResponse(index))
    return _set_helper_cookie(JSONResponse({"ok": False, "message": "React build not found. Run npm build in helper_ui."}, status_code=503))


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def spa_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    requested = (UI_DIST_DIR / full_path).resolve()
    if requested.is_file() and str(requested).startswith(str(UI_DIST_DIR.resolve())):
        return FileResponse(requested)
    index = UI_DIST_DIR / "index.html"
    if index.exists():
        return _set_helper_cookie(FileResponse(index))
    return _set_helper_cookie(JSONResponse({"ok": False, "message": "React build not found. Run npm build in helper_ui."}, status_code=503))
