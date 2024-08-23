import torch
import os

from logic.config_watcher import cfg

def convert_onnx_to_fp16():
    import onnx
    from onnxconverter_common import float16
    
    model = onnx.load(f"models/{cfg.AI_model_name}")
    model_fp16 = float16.convert_float_to_float16(model)
    new_model_name = cfg.AI_model_name.replace(".onnx", "_fp16.onnx")
    onnx.save(model_fp16, f"models/{new_model_name}")
    
    print(f"Converted model saved as 'models/{new_model_name}'.\n"
          f"Please change the ai_model_name option to the converted version of the model ({new_model_name}).")
    
def check_model_fp16():
    try:
        import onnx
        from onnxconverter_common import float16
    except ModuleNotFoundError:
        os.system("pip install onnx onnxconverter-common")
    
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
        if ".pt" in cfg.AI_model_name:
            print("WARNING: Export the model to `.engine` for better performance!\nHOW TO EXPORT TO ENGINE: 'https://github.com/SunOner/sunone_aimbot_docs/blob/main/ai_models/ai_models.md'")
        if cfg.show_window:
            print("WARNING: An open debug window can affect performance.")
        if cfg.bettercam_capture_fps >= 120:
            print("WARNING: A large number of frames per second can affect the behavior of automatic aiming. (Shaking).")
        if cfg.detection_window_width >= 600:
            print("WARNING: The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance.")
        if cfg.detection_window_height >= 600:
            print("WARNING: The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance.")
        if cfg.AI_conf <= 0.15:
            print("WARNING: A small value of `AI_conf ` can lead to a large number of false positives.")
        
        # mouse
        if cfg.mouse_ghub == False and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print("WARNING: win32api is detected in some games.")
        if cfg.mouse_ghub and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print("WARNING: ghub is detected in some games.")
        if cfg.arduino_move == False:
            print("WARNING: Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.")
        if cfg.arduino_shoot == False and cfg.auto_shoot:
            print("WARNING: Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.")
        
        selected_methods = sum([cfg.arduino_move, cfg.mouse_ghub, cfg.mouse_rzr])
        if selected_methods > 1:
            raise ValueError("WARNING: You use more than one mouse input method.")
        
def run_checks():
    if torch.cuda.is_available() is False:
        print("You need to install a version of pytorch that supports CUDA.\n"
            "First uninstall all torch packages.\n"
            "Run command 'pip uninstall torch torchvision torchaudio'\n"
            "Next go to 'https://pytorch.org/get-started/locally/' and install torch with CUDA support.\n"
            "Don't forget your CUDA version (Minimum version is 12.1, max version is 12.4).")
        quit()
        
    if cfg.Bettercam_capture == False and cfg.Obs_capture == False:
        print("Use at least one image capture method.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.")
        quit()
        
    if cfg.Bettercam_capture and cfg.Obs_capture:
        print("Only one capture method is possible.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.")
        quit()

    if not os.path.exists(f"models/{cfg.AI_model_name}"):
        print(f"The AI model {cfg.AI_model_name} has not been found! Check the correctness of the model name in the AI_model_name option.")
        quit()
    
    if cfg.AI_model_name.endswith(".onnx"):
        fp16 = check_model_fp16()
        if fp16 == False:
            check_converted_model = cfg.AI_model_name.replace(".onnx", "_fp16.onnx")
            if not os.path.exists(f"models/{check_converted_model}"):
                print(f"The current AI format of the '{cfg.AI_model_name}' model is fp32. Converting model to fp16...")
                convert_onnx_to_fp16()
                quit()
            else:
                print(f"Please, use converted model - '{check_converted_model}'.\nChange in config.ini 'AI_model_name = {check_converted_model}'")
                quit()
    Warnings()