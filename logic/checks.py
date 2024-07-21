import torch
from logic.config_watcher import cfg

def Warnings():
        if '.pt' in cfg.AI_model_name:
            print("WARNING: Export the model to `.engine` for better performance!\nHOW TO EXPORT TO ENGINE DOCS: 'https://github.com/SunOner/sunone_aimbot?tab=readme-ov-file#export-pt-model-to-engine'")
        if cfg.mouse_ghub == False and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print('WARNING: win32api is detected in some games.')
        if cfg.mouse_ghub and cfg.arduino_move == False and cfg.arduino_shoot == False:
            print('WARNING: ghub is detected in some games.')
        if cfg.show_window:
            print('WARNING: An open debug window can affect performance.')
        if cfg.bettercam_capture_fps >= 120:
            print('WARNING: A large number of frames per second can affect the behavior of automatic aiming. (Shaking).')
        if cfg.detection_window_width >= 600:
            print('WARNING: The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance.')
        if cfg.detection_window_height >= 600:
            print('WARNING: The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance.')
        if cfg.arduino_move == False:
            print('WARNING: Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.arduino_shoot == False and cfg.auto_shoot:
            print('WARNING: Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk.')
        if cfg.AI_conf <= 0.15:
            print('WARNING: A small value of `AI_conf ` can lead to a large number of false positives.')
            
def run_checks():
    if torch.cuda.is_available() is False:
        print("You need to install a version of pytorch that supports CUDA.\n"
            "First uninstall all torch packages.\n"
            "Run command 'pip uninstall torch torchvision torchaudio'\n"
            "Next go to 'https://pytorch.org/get-started/locally/' and install torch with CUDA support.\n"
            "Don't forget your CUDA version (Minimum version is 12.1, max version is 12.4).")
        quit()
        
    if cfg.Bettercam_capture == False and cfg.Obs_capture == False:
        print('Use at least one image capture method.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
        quit()
        
    if cfg.Bettercam_capture and cfg.Obs_capture:
        print('Only one capture method is possible.\nSet the value to `True` in the `bettercam_capture` option or in the `obs_capture` option.')
        quit()

    Warnings()