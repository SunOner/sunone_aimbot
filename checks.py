from logic.config_watcher import Config
cfg = Config()
try:
    from screeninfo import get_monitors
except:
    print('install screeninfo: pip install screeninfo')
    exit(0)

try:   
    import ultralytics
    from ultralytics import YOLO
except:
    print('install ultralytics: pip install ultralytics')
    exit(0)

if '.engine' in cfg.AI_model_path:
    import tensorrt

try:
    import numpy
except:
    print('install numpy: pip install numpy')
    exit(0)

if cfg.Bettercam_capture == True:
    try:
        import bettercam
    except:
        print('Install bettercam: pip install bettercam')
        exit(0)

import importlib.metadata
import os

try:
    import cv2
    from cv2 import __version__
except:
    print('install cv2: pip install opencv-python')
    exit(0)

def run_checks():
    ultralytics.utils.checks.collect_system_info()

    cuda_support = ultralytics.utils.checks.cuda_is_available()
    if cuda_support == True:
        print('\nCuda support True')
    else:
        print('Cuda is not supported. Please reinstall pytorch with GPU support. https://pytorch.org/get-started/locally/\nIf you have reinstalled but there is no GPU support, Google how to solve this problem.')
        quit(0)

    print('OpenCV version: {0}'.format(__version__))

    if '.engine' in cfg.AI_model_path:
        print('TensorRT version: {0}'.format(tensorrt.__version__))
    if '.pt' in cfg.AI_model_path:
        print(ultralytics.YOLO('models/{}'.format(cfg.AI_model_path), task='detect').info())

    print('numpy version: {0}'.format(numpy.version.version))

    if cfg.Bettercam_capture:
        print('Bettercam devices info:\n{0}'.format(bettercam.output_info()))
    # TODO: ADD OBS_CAPTURE CHECKS
    try:
        print('asyncio version: {0}'.format(importlib.metadata.version('asyncio')))
    except:
        print('Please install asyncio: pip install asyncio')

    print('\n********** Options **********\n')

    print('screen_width', cfg.detection_window_width)
    print('screen_height', cfg.detection_window_height, '\n')

    print('Bettercam_capture', cfg.Bettercam_capture)
    print('bettercam_capture_fps', cfg.bettercam_capture_fps)
    print('bettercam_monitor_id', cfg.bettercam_monitor_id)
    print('bettercam_gpu_id', cfg.bettercam_gpu_id, '\n')

    print('Obs_capture',cfg. Obs_capture)
    print('Obs_camera_id', cfg.Obs_camera_id)
    print('Obs_capture_fps', cfg.Obs_capture_fps, '\n')

    print('body_y_offset', cfg.body_y_offset)
    print('hideout_targets', cfg.hideout_targets, '\n')

    print('mouse_smoothing', cfg.mouse_smoothing)
    print('mouse_slow_down_factor', cfg.mouse_slow_down_factor)
    print('mouse_auto_shoot', cfg.mouse_auto_shoot)
    print('mouse_auto_aim', cfg.mouse_auto_aim)
    print('mouse_native', cfg.mouse_native)
    print('mouse_move_by_arduino', cfg.mouse_move_by_arduino)
    print('mouse_shoot_by_arduino', cfg.mouse_shoot_by_arduino, '\n')

    print('hotkey_targeting', cfg.hotkey_targeting)
    print('hotkey_exit', cfg.hotkey_exit)
    print('hotkey_pause', cfg.hotkey_pause, '\n')

    print('AI_model_path', cfg.AI_model_path)
    print('AI_image_size', cfg.AI_image_size)
    print('AI_conf', cfg.AI_conf)
    print('AI_iou', cfg.AI_iou)
    print('AI_device', cfg.AI_device)
    print('AI_max_det', cfg.AI_max_det, '\n')

    print('show_window', cfg.show_window)
    print('show_speed', cfg.show_speed)
    print('show_fps', cfg.show_fps)
    print('show_boxes', cfg.show_boxes)
    print('show_labels', cfg.show_labels)
    print('show_conf', cfg.show_conf)
    print('show_target_line', cfg.show_target_line)
    print('debug_window_always_on_top', cfg.debug_window_always_on_top)
    print('debug_window_scale_percent', cfg.debug_window_scale_percent)
    print('debug_window_name', cfg.debug_window_name, '\n')

    print('Environment variables:\n')
    for key, value in os.environ.items():
        if key == 'PATH':
            print('--------------------------- PATH ---------------------------')
            for i in value.split(';'):
                print(i)
            print('--------------------------- PATH ---------------------------')
        else:
            print(f'{key}: {value}')
    
    detection_test = detections_check()
    print(detection_test)

def detections_check():
    model = YOLO('models/{}'.format(cfg.AI_model_path), task='detect')
    cap = cv2.VideoCapture('media/tests/test_det.mp4')
    clss = []
    while cap.isOpened():
        success, frame = cap.read()

        if success:
            result = model(frame, stream=False, show=False, imgsz=cfg.AI_image_size, device=cfg.AI_device, verbose=False)
            for frame in result:
                clss.append(frame.boxes.cls)
            annotated_frame = result[0].plot()

            cv2.putText(annotated_frame, 'TEST 1234567890', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            
            cv2.imshow("ETECTION TEST", annotated_frame)
            if cv2.waitKey(30) & 0xFF == ord("q"):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(clss) <= 0:
        return '\nDetection test: Failed'
    else:
        return '\nDetection test: Passed. Number of detections: {}'.format(len(clss))

if __name__ == "__main__":
    run_checks()