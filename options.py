# Your original screen resolution at the moment:
original_screen_height = 2560
original_screen_width = 1440
'''
...but I want to reduce the screen capture resolution to increase performance:
For some it is better to leave the same settings as on the original original_screen_height=1920 and screen_height=1920.
Not all screen resolutions work at the moment, play around with them, for example your original screen resolution: original_screen_height = 1920 original_screen_width=1080 set screen_height=800 screen_width=450, it should work.)
'''
screen_height = 1280
screen_width = 720

auto_aim = False
auto_shot = False
head_correction = False
y_offset = 0.35

show_window = False
show_speed = False
show_fps = True
debug_window_scale_percent = 100
debug_window_name = 'RT'
model_path='models/all_1.engine'

#TEMP#
aim_x = 0
aim_y = 0
aim_x_left = 0
aim_x_right = 0
aim_y_up = 0
aim_y_down = 0

def Calculate_screen_offset():
    if original_screen_height == screen_height and original_screen_width == screen_width:
        return (int(original_screen_height / 4), int(original_screen_width / 4), int(original_screen_height - original_screen_height / 4), int(original_screen_width -  original_screen_width / 4))
    else:
        original_point_1 = original_screen_height / 4
        original_point_2 = original_screen_width / 4
        original_point_3 = original_screen_height - original_point_1
        original_point_4 = original_screen_width - original_point_2

        increase_point_1 = screen_height / 4
        increase_point_2 = screen_width / 4
        increase_point_3 = screen_height - increase_point_1
        increase_point_4 = screen_width - increase_point_2

        new_point_1 = original_screen_height / 4 + original_point_1 - increase_point_1
        new_point_2 = original_screen_width / 4 + original_point_2 - increase_point_2
        new_point_3 = original_screen_height - original_point_3 + original_point_3 - increase_point_3
        new_point_4 = original_screen_width - original_point_4 + original_point_4 - increase_point_4
    return (int(new_point_1), int(new_point_2), int(new_point_3), int(new_point_4))