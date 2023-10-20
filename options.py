# Your original screen resolution at the moment:
original_screen_width = 2560
original_screen_height = 1440
# Object Search screen resolution
screen_width = 640
screen_height = 360

auto_aim = False
auto_shot = False
head_correction = False
y_offset = 0.37

show_window = False
show_speed = False
show_fps = True
debug_window_scale_percent = 100
debug_window_name = 'RT'
model_path='models/all_1.pt'

#TEMP#
aim_x = 0
aim_y = 0
aim_x_left = 0
aim_x_right = 0
aim_y_up = 0
aim_y_down = 0

def Calculate_screen_offset():
    left = original_screen_width / 2 - screen_width / 2
    top = original_screen_height / 2 - screen_height / 2
    width = left + screen_width
    height = top + screen_height
    return (int(left), int(top), int(width), int(height))