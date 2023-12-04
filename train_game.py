from ultralytics import YOLO
import os
os.environ['CUDA_MODULE_LOADING'] = 'LAZY'

def init(_task='train', _model=YOLO('yolov8s.pt', task='detect'), _data = 'game.yaml', _imgsz = 320, _epochs = 40, _device = 0, _val = False, _half = True, _cache = False, _batch = -1, _export_after_train = False, _export_format = 'engine', _export_workspace = 8, _export_nms = False):
    _model.info()

    if _task == 'train':
        _model.train(
        data=_data,
        imgsz=_imgsz,
        epochs=_epochs,
        device=_device,
        val=_val,
        resume=False,
        half=_half,
        cache=_cache,
        batch=_batch)
        if _export_after_train:
            export(_model, _export_format, _device, _half, _export_workspace, _imgsz, _export_nms)

    if _task == 'export':
        export(_model, _export_format, _device, _half, _export_workspace, _imgsz, _export_nms)
    
    if _task == 'resume':
        _model.train(resume=True)
        
    if _task == 'tune':
        _model.tune(
        data=_data,
        epochs=30,
        iterations=300,
        optimizer='AdamW',
        imgsz=320,
        plots=False,
        save=False,
        val=False)

def export(model, _format, _device, _half, _workspace, _imgsz, _nms):
    model.export( 
    format=_format,
    device=_device,
    half=_half,
    workspace=_workspace,
    imgsz=_imgsz,
    nms=_nms) 

if __name__ == "__main__":
    _task = 'export' # train / export / resume / tune
    _model = YOLO('models/sunxds_0.2.1_nano_320.pt', task='detect') # yolov8n.pt yolov8s.pt yolov8m.pt yolov8h.pt yolov8x.pt
    _data = 'game.yaml'
    _imgsz = 320
    _epochs = 40
    _device = 0
    _val = False
    _half = True
    _cache = False
    _batch = -1

    _export_after_train = True
    _export_format = 'engine'
    _export_workspace = 10
    _export_nms = False

    init(_task, _model, _data, _imgsz, _epochs, _device, _val, _half, _cache, _batch, _export_after_train, _export_format, _export_workspace, _export_nms)