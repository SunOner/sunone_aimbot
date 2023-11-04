# Your screen resolution
original_screen_width = 1920
original_screen_height = 1080

# Object Search window resolution
screen_width = 480
screen_height = 300

# dxcam Capture method
Dxcam_capture = True
dxcam_capture_fps = 30 # More value, more mouse swing
dxcam_monitor_id = 0
dxcam_gpu_id = 0
dxcam_max_buffer_len = 64

# Obs capture method
Obs_capture = False
Obs_camera_id = 1

# Windows capture method
Windows_capture = False

# Aim settings
body_y_offset = 0.35
head_y_offset = 0.35
hideout_targets = True

# Mouse settings 
mouse_smoothing = 1 # 1 is default
mouse_auto_shoot = False
mouse_auto_shoot_timer = False
mouse_auto_shoot_sleep_time = 0.2
mouse_auto_aim = False

# Cv2 debug window settings
show_window = True
show_speed = False
show_fps = False
debug_window_scale_percent = 100
debug_window_name = 'RT'

# AI settings
model_path='models/sunxds_0.2.1.pt'

def Calculate_screen_offset():
    left = original_screen_width / 2 - screen_width / 2
    top = original_screen_height / 2 - screen_height / 2
    width = left + screen_width
    height = top + screen_height
    return (int(left), int(top), int(width), int(height))

# Targets
players = []
heads = []
bots= []
hideout_target_human = []
hideout_target_balls = []