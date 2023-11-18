from options import *
import ultralytics
from cv2 import __version__
import tensorrt
import numpy
import dxcam
import importlib.metadata
import os

def run_checks():
    ultralytics.utils.checks.collect_system_info()

    print('\nCuda support: {0}'.format(ultralytics.utils.checks.cuda_is_available()))

    print('OpenCV version: {0}'.format(__version__))

    print('TensorRT version: {0}'.format(tensorrt.__version__))

    print('numpy version: {0}'.format(numpy.version.version))

    print('DXcam devices info:\n{0}'.format(dxcam.output_info()))

    print('asyncio version: {0}'.format(importlib.metadata.version('asyncio')))

    print('Options file:\n')

    print('original_screen_width', original_screen_width)
    print('original_screen_height', original_screen_height, '\n')

    print('screen_width', screen_width)
    print('screen_height', screen_height, '\n')

    print('Dxcam_capture', Dxcam_capture)
    print('dxcam_capture_fps', dxcam_capture_fps)
    print('dxcam_monitor_id', dxcam_monitor_id)
    print('dxcam_gpu_id', dxcam_gpu_id)
    print('dxcam_max_buffer_len', dxcam_max_buffer_len, '\n')

    print('Obs_capture', Obs_capture)
    print('Obs_camera_id', Obs_camera_id)
    print('Obs_capture_fps', Obs_capture_fps, '\n')

    print('native_Windows_capture', native_Windows_capture, '\n')

    print('body_y_offset', body_y_offset)
    print('hideout_targets', hideout_targets, '\n')

    print('mouse_smoothing', mouse_smoothing)
    print('mouse_auto_shoot', mouse_auto_shoot)
    print('mouse_auto_aim', mouse_auto_aim)
    print('mouse_native', mouse_native, '\n')

    print('AI_model_path', AI_model_path)
    print('AI_image_size', AI_image_size)
    print('AI_conf', AI_conf)
    print('AI_iou', AI_iou)
    print('AI_device', AI_device)
    print('AI_half', AI_half)
    print('AI_max_det', AI_max_det)
    print('AI_verbose', AI_verbose, '\n')

    print('show_window', show_window)
    print('show_speed', show_speed)
    print('show_fps', show_fps)
    print('debug_window_scale_percent', debug_window_scale_percent)
    print('debug_window_name', debug_window_name, '\n')

    print('Environment variables:\n')
    for key, value in os.environ.items():
        print(f'{key}: {value}')

if __name__ == "__main__":
    run_checks()