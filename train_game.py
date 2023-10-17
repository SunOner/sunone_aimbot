from ultralytics import YOLO

def init():
    model = YOLO('yolov8s.pt') # Load pretrained model
    model.info()

    model.train(
    data='coco8.yaml',
    imgsz=640,
    epochs=40,
    device=0,
    val=False,
    resume=False,
    batch=16)

    model.export(format='engine', device=0) # Export to .engine
        
if __name__ == "__main__":
    init()