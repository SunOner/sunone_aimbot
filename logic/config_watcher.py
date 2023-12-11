import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

config_detection_window = config['Detection window']
detection_window_width = int(config_detection_window['detection_window_width'])
detection_window_height = int(config_detection_window['detection_window_height'])

config_Dxcam_Capture = config['Dxcam Capture']
Dxcam_capture = config_Dxcam_Capture.getboolean('Dxcam_capture')
dxcam_capture_fps = int(config_Dxcam_Capture['dxcam_capture_fps'])
dxcam_monitor_id = int(config_Dxcam_Capture['dxcam_monitor_id'])
dxcam_gpu_id = int(config_Dxcam_Capture['dxcam_gpu_id'])
dxcam_max_buffer_len =int( config_Dxcam_Capture['dxcam_max_buffer_len'])

config_Obs_capture = config['Obs capture']
Obs_capture = config_Obs_capture.getboolean('Obs_capture')
Obs_camera_id = int(config_Obs_capture['Obs_camera_id'])
Obs_capture_fps = int(config_Obs_capture['Obs_capture_fps'])

config_Windows_capture = config['Windows capture']
native_Windows_capture = config_Windows_capture.getboolean('native_Windows_capture')

config_Aim_settings = config['Aim settings']
body_y_offset = float(config_Aim_settings['body_y_offset'])
hideout_targets = config_Aim_settings.getboolean('hideout_targets')
disable_headshot = config_Aim_settings.getboolean('disable_headshot')

config_Mouse_settings = config['Mouse settings']
mouse_break_force = int(config_Mouse_settings['mouse_break_force'])
mouse_smoothing = float(config_Mouse_settings['mouse_smoothing'])
mouse_auto_shoot = config_Mouse_settings.getboolean('mouse_auto_shoot')
mouse_auto_aim = config_Mouse_settings.getboolean('mouse_auto_aim')
mouse_native = config_Mouse_settings.getboolean('mouse_native')
mouse_wild_mouse = config_Mouse_settings.getboolean('mouse_wild_mouse')
mouse_move_by_arduino = config_Mouse_settings.getboolean('mouse_move_by_arduino')
mouse_shoot_by_arduino = config_Mouse_settings.getboolean('mouse_shoot_by_arduino')

config_AI_options = config['AI options']
AI_model_path = str(config_AI_options['AI_model_path'])
AI_image_size = int(config_AI_options['AI_image_size'])
AI_conf = float(config_AI_options['AI_conf'])
AI_iou = float(config_AI_options['AI_iou'])
AI_device = str(config_AI_options['AI_device'])
AI_max_det = int(config_AI_options['AI_max_det'])

config_Debug_window = config['Debug window']
show_window = config_Debug_window.getboolean('show_window')
show_speed = config_Debug_window.getboolean('show_speed')
show_fps = config_Debug_window.getboolean('show_fps')
show_boxes = config_Debug_window.getboolean('show_boxes')
show_labels = config_Debug_window.getboolean('show_labels')
show_conf = config_Debug_window.getboolean('show_conf')
debug_window_scale_percent = int(config_Debug_window['debug_window_scale_percent'])
debug_window_name = str(config_Debug_window['debug_window_name'])