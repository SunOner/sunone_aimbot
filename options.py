# Desktop screen resolution
original_screen_width = 1920
original_screen_height = 1080

# Object Search window resolution
screen_width = 480
screen_height = 300

# Dxcam Capture method
Dxcam_capture = True
dxcam_capture_fps = 30 # 30 fps is OK
dxcam_monitor_id = 0
dxcam_gpu_id = 0
dxcam_max_buffer_len = 64

# Obs capture method
Obs_capture = False
Obs_camera_id = 1
Obs_capture_fps = 30 # 30 fps is OK

# Windows capture method
native_Windows_capture = False

# Aim settings
body_y_offset = 0.35
hideout_targets = True

# Mouse settings 
mouse_smoothing = 1 # 1 is default
mouse_auto_shoot = False
mouse_auto_aim = False
mouse_native = True

# AI options
AI_model_path = 'models/sunxds_0.2.1_nano_320.pt'
AI_image_size = 320
AI_conf = 0.35
AI_iou = 0.1
AI_device = 0
AI_max_det = 10

# Cv2 debug window settings
show_window = False
show_speed = False
show_fps = False
show_boxes = True
# show_labels = True :TODO
# show_conf = True :TODO
debug_window_scale_percent = 100
debug_window_name = 'Calculator'