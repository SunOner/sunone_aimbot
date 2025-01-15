_C='_fp16.onnx'
_B='.onnx'
_A=False
import torch,os
from logic.config_watcher import cfg
def convert_onnx_to_fp16():import onnx as B;from onnxconverter_common import float16 as C;D=B.load(f"models/{cfg.AI_model_name}");E=C.convert_float_to_float16(D);A=cfg.AI_model_name.replace(_B,_C);B.save(E,f"models/{A}");print(f"Converted model saved as 'models/{A}'.\nPlease change the ai_model_name option to the converted version of the model ({A}).")
def check_model_fp16():
        try:import onnx as A;from onnxconverter_common import float16
        except ModuleNotFoundError:os.system('pip install onnx onnxconverter-common')
        D=A.load(f"models/{cfg.AI_model_name}");C=D.graph
        for E in C.input:
                B=E.type.tensor_type
                if B.elem_type==A.TensorProto.FLOAT16:return True
        for F in C.output:
                B=F.type.tensor_type
                if B.elem_type==A.TensorProto.FLOAT16:return True
        return _A
def Warnings():
        if'.pt'in cfg.AI_model_name:print("WARNING: Export the model to `.engine` for better performance!\nHOW TO EXPORT TO ENGINE: 'https://github.com/SunOner/sunone_aimbot_docs/blob/main/ai_models/ai_models.md'")
        if cfg.show_window:print('WARNING: An open debug window can affect performance.')
        if cfg.bettercam_capture_fps>=120:print('WARNING: A large number of frames per second can affect the behavior of automatic aiming. (Shaking).')
        if cfg.detection_window_width>=600:print('WARNING: The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance.')
        if cfg.detection_window_height>=600:print('WARNING: The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance.')
        if cfg.AI_conf<=.15:print('WARNING: A small value of `AI_conf ` can lead to a large number of false positives.')
        if cfg.mouse_ghub==_A and cfg.arduino_move==_A and cfg.arduino_shoot==_A:print('WARNING: win32api is detected in some games.')
        if cfg.mouse_ghub and cfg.arduino_move==_A and cfg.arduino_shoot==_A:print('WARNING: ghub is detected in some games.')
        if cfg.arduino_move==_A:print('WARNING: Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.arduino_shoot==_A and cfg.auto_shoot:print('WARNING: Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        A=sum([cfg.arduino_move,cfg.mouse_ghub,cfg.mouse_rzr])
        if A>1:raise ValueError('WARNING: You use more than one mouse input method.')
def run_checks():
        if torch.cuda.is_available()is _A:print("You need to install a version of pytorch that supports CUDA.\nFirst uninstall all torch packages.\nRun command 'pip uninstall torch torchvision torchaudio'\nNext go to 'https://pytorch.org/get-started/locally/' and install torch with CUDA support.\nDon't forget your CUDA version (Minimum version is 12.1, max version is 12.4).");quit()
        if cfg.Bettercam_capture==_A and cfg.Obs_capture==_A:print('Use at least one image capture method.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.');quit()
        if cfg.Bettercam_capture and cfg.Obs_capture:print('Only one capture method is possible.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.');quit()
        if not os.path.exists(f"models/{cfg.AI_model_name}"):print(f"The AI model {cfg.AI_model_name} has not been found! Check the correctness of the model name in the AI_model_name option.");quit()
        if cfg.AI_model_name.endswith(_B):
                B=check_model_fp16()
                if B==_A:
                        A=cfg.AI_model_name.replace(_B,_C)
                        if not os.path.exists(f"models/{A}"):print(f"The current AI format of the '{cfg.AI_model_name}' model is fp32. Converting model to fp16...");convert_onnx_to_fp16();quit()
                        else:print(f"Please, use converted model - '{A}'.\nChange in config.ini 'AI_model_name = {A}'");quit()
        Warnings()