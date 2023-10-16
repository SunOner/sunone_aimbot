from ultralytics import YOLO
from pathlib import Path
import os

delete_cache = True

def init():
    cache_file_images = Path("C:/Users/sun/source/repos/yolov8_trt/datasets/game/labels.cache")
    cache_file_val = Path("C:/Users/sun/source/repos/yolov8_trt/datasets/game/val/labels.cache")

    if cache_file_images.is_file() and delete_cache == True:
        os.remove(cache_file_images)
        print('Images cache removed')

    if cache_file_val.is_file() and delete_cache == True:
        os.remove(cache_file_val)
        print('Val cache removed')

    model = YOLO('yolov8s.pt')
    model.info()

    model.train(
    data='coco8.yaml',
    imgsz=640,
    epochs=40,
    device=[0,1],
    val=False,
    resume=False,
    batch=16)

    model.export(format='engine', device=[0,1])
        
if __name__ == "__main__":
    init()