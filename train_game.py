from ultralytics import YOLO

def init():
    model = YOLO('yolov8s.pt', task='detect') # Load pretrained model (You can use my model)
    model.info()

    model.train(
    data='game.yaml',
    imgsz=640, # Image size
    epochs=40, # How long train a model
    device=0, # GPU id (For multi-gpu use device=[0,1])
    val=False, # validate
    resume=False, # resume from last epoch
    batch=16)

    model.export(
    format='engine', # export format .engine
    device=0, # GPU id (For multi-gpu use device=[0,1])
    half=True, # half for TensorRT
    workspace=8, # GPU max video memory
    imgsz=640,
    nms=True) # Export to .engine
        
if __name__ == "__main__":
    init()