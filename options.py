# Detection window resolution. In its current form, this is 20% of the screen resolution.
detection_window_width = 384
detection_window_height = 216 

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
disable_headshot = False

# Mouse settings 
mouse_smoothing = 1
mouse_auto_shoot = False
mouse_auto_aim = False
mouse_native = True
mouse_wild_mouse = True

# AI options
AI_model_path = 'models/sunxds_0.2.1_nano_320.pt' # You can find new improved models here https://boosty.to/sunone
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
show_labels = True
show_conf = True
debug_window_scale_percent = 100
debug_window_name = 'Calculator'