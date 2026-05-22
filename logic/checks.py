import torch
import os
import sys
import importlib.util

from logic.config_watcher import cfg
from logic.logger import logger
from logic.platform import IS_WINDOWS, IS_LINUX

def convert_onnx_to_fp16():
    import onnx
    from onnxconverter_common import float16
    
    model = onnx.load(f"models/{cfg.AI_model_name}")
    model_fp16 = float16.convert_float_to_float16(model)
    new_model_name = cfg.AI_model_name.replace(".onnx", "_fp16.onnx")
    onnx.save(model_fp16, f"models/{new_model_name}")
    
    logger.info(f"""
    Converted model saved as 'models/{new_model_name}'.
    Please change the ai_model_name option to the converted version of the model ({new_model_name}).
    """)
    
def check_model_fp16():
    try:
        import onnx
        from onnxconverter_common import float16
    except ModuleNotFoundError:
        logger.error("ONNX fp16 check requires packages: onnx and onnxconverter-common.")
        raise SystemExit(1)
    
    model = onnx.load(f"models/{cfg.AI_model_name}")
    
    graph = model.graph
    
    for input_tensor in graph.input:
        tensor_type = input_tensor.type.tensor_type
        if tensor_type.elem_type == onnx.TensorProto.FLOAT16:
            return True
    
    for output_tensor in graph.output:
        tensor_type = output_tensor.type.tensor_type
        if tensor_type.elem_type == onnx.TensorProto.FLOAT16:
            return True
    
    return False

def Warnings():
    # Capture
    if cfg.capture_fps >= 120:
        logger.warning("A large number of frames per second can affect the behavior of automatic aiming. (Shaking).")
    if cfg.detection_window_width >= 600:
        logger.warning("The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance.")
    if cfg.detection_window_height >= 600:
        logger.warning("The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance.")
    
    # AI
    if _is_cpu_device():
        logger.warning("AI_device is set to CPU. This is stable, but much slower than CUDA for realtime detection.")
    if cfg.AI_model_name.endswith(".pt"):
        logger.warning("Export the model to `.engine` for better performance!\nHOW TO EXPORT TO ENGINE: 'https://github.com/SunOner/sunone_aimbot_docs/blob/main/ai_models/ai_models.md'")
    if cfg.AI_conf <= 0.10:
        logger.warning("A small value of `AI_conf ` can lead to a large number of false positives.")
    
    # Mouse
    if IS_WINDOWS:
        if not any([cfg.mouse_ghub, cfg.arduino_move, cfg.mouse_rzr]):
            logger.warning("win32api is detected in some games.")
        if cfg.mouse_ghub and not cfg.arduino_move and not cfg.arduino_shoot:
            logger.warning("ghub is detected in some games.")
        if not cfg.arduino_move:
            logger.warning("Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.")
        if not cfg.arduino_shoot and cfg.auto_shoot:
            logger.warning("Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.")
    elif IS_LINUX and importlib.util.find_spec("pynput") is None:
        logger.warning("pynput is not installed. Ubuntu hotkeys and native mouse input will be unavailable.")
    selected_methods = sum([cfg.arduino_move, cfg.mouse_ghub, cfg.mouse_rzr])
    if selected_methods > 1:
        raise ValueError("WARNING: You use more than one mouse input method.")
    
    # Debug
    if cfg.show_window:
        logger.warning("An open debug window can affect performance.")

def _is_cpu_device():
    return str(cfg.AI_device).strip().lower().startswith("cpu")

def _cuda_device_index():
    raw = str(cfg.AI_device).strip().lower()
    if raw.startswith("cuda:"):
        raw = raw.split(":", 1)[1]
    return int(raw) if raw.isdigit() else None

def _validate_capture_config():
    selected = [
        name for name, enabled in (
            ("bettercam_capture", cfg.Bettercam_capture),
            ("obs_capture", cfg.Obs_capture),
            ("mss_capture", cfg.mss_capture),
        )
        if enabled
    ]

    if len(selected) < 1:
        logger.error("Use at least one image capture method: bettercam_capture, obs_capture, or mss_capture.")
        raise SystemExit(1)

    if len(selected) > 1:
        logger.error(f"Only one capture method is possible. Enabled now: {', '.join(selected)}.")
        raise SystemExit(1)

    if cfg.capture_fps <= 0:
        logger.error("capture_fps must be greater than 0.")
        raise SystemExit(1)

    if cfg.detection_window_width <= 0 or cfg.detection_window_height <= 0:
        logger.error("Detection window width and height must be greater than 0.")
        raise SystemExit(1)

    if cfg.Bettercam_capture and not IS_WINDOWS:
        logger.error("BetterCam capture is Windows-only. Use mss_capture or obs_capture on Ubuntu.")
        raise SystemExit(1)

    if cfg.mouse_ghub and not IS_WINDOWS:
        logger.error("mouse_ghub is Windows-only. Disable mouse_ghub on Ubuntu.")
        raise SystemExit(1)

    if cfg.mouse_rzr and not IS_WINDOWS:
        logger.error("mouse_rzr is Windows-only. Disable mouse_rzr on Ubuntu.")
        raise SystemExit(1)

def _validate_torch_device():
    if _is_cpu_device() or cfg.AI_enable_AMD:
        return

    if not torch.cuda.is_available():
        torch_details = (
            f"Python executable: {sys.executable}\n"
            f"Torch version: {getattr(torch, '__version__', 'unknown')}\n"
            f"Torch CUDA build: {getattr(torch.version, 'cuda', None) or 'none'}\n"
            f"Torch file: {getattr(torch, '__file__', 'unknown')}\n"
            f"CUDA device count: {torch.cuda.device_count()}"
        )
        logger.error(
            "AI_device requires CUDA, but CUDA is not available in this Python environment.\n"
            f"{torch_details}\n"
            "For CPU mode set AI_device = cpu. For CUDA reinstall torch with a CUDA build."
        )
        raise SystemExit(1)

    device_index = _cuda_device_index()
    if device_index is not None and device_index >= torch.cuda.device_count():
        logger.error(f"AI_device points to CUDA device {device_index}, but only {torch.cuda.device_count()} CUDA device(s) are available.")
        raise SystemExit(1)

def run_checks():
    os.makedirs("screenshots", exist_ok=True)

    _validate_capture_config()
    _validate_torch_device()

    if not os.path.exists(f"models/{cfg.AI_model_name}"):
        logger.error(f"The AI model {cfg.AI_model_name} has not been found! Check the correctness of the model name in the AI_model_name option.")
        raise SystemExit(1)
    
    if cfg.AI_model_name.endswith(".onnx"):
        fp16 = check_model_fp16()
        if fp16 == False:
            check_converted_model = cfg.AI_model_name.replace(".onnx", "_fp16.onnx")
            if not os.path.exists(f"models/{check_converted_model}"):
                logger.info(f"The current AI format of the '{cfg.AI_model_name}' model is fp32. Converting model to fp16...")
                convert_onnx_to_fp16()
                raise SystemExit(0)
            else:
                logger.info(f"Please, use converted model - '{check_converted_model}'.\nChange in config.ini 'AI_model_name = {check_converted_model}'")
                raise SystemExit(0)
    Warnings()
