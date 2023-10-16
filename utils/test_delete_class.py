import os

for filename in os.listdir("C:/Users/sun/source/repos/yolov8_trt/datasets/game/labels/"):
    with open('C:/Users/sun/source/repos/yolov8_trt/datasets/game/labels/{0}'.format(filename), 'r') as f:
        all_lines = f.readlines()
        f.close()

        f = open('C:/Users/sun/source/repos/yolov8_trt/datasets/game/labels/{0}'.format(filename), 'w')
        for line in all_lines:
            if line.startswith('3 '):
                pass
            else:        
                f.write(line)
        f.close()