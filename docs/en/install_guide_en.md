##  Yolov8 aimbot Install guide
[![](https://img.youtube.com/vi/qxz_vm806j0/hqdefault.jpg)](https://youtu.be/qxz_vm806j0)
<br></br>
1. (OPTIONAL FOR CLEAN INSTALL) Uninstall all versions of Python and Cuda then reboot PC.
<br></br>
2. Update the Nvidia graphics driver. Cudnn should be installed automatically after updating the driver
<br></br>
3. Download and install python 3.11.6. On startup installer screen enable "Add Python 3.11.6 to PATH" option! [link](https://www.python.org/downloads/)
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/python.png)
<br></br>
4. Download and export aimbot files yolov8 aimbot [link](https://github.com/SunOner/yolov8_aimbot)
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/aimbot.png)
<br></br>
5. Download and install Cuda 12.1 the reboot PC [link](https://developer.nvidia.com/cuda-12-1-0-download-archive)
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/cuda.png)
<br></br>
6. Open cmd and type `python -m pip install --upgrade pip`, then type `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`
<br></br>
7. Download [TensorRT](https://disk.yandex.ru/d/mgiPzH8fCL83qw) and unpack the files in yolov8_aimbot-main folder.
<br></br>
8. Open cmd and type `cd C:/your_export_path/yolov8_aimbot-main/TensorRT-8.6.1.6/python` then type `pip install tensorrt-8.6.1-cp311-none-win_amd64.whl`
<br></br>
9. Hit WIN + R and type `sysdm.cpl`.
- Click on advanced then on environment variables...
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/environment_variables.png)
- Double click on `path`
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/environment_variables_path.png)
- Press `new` and type `C:/your_export_path/yolov8_aimbot-main/TensorRT-8.6.1.6/lib`
- (OPTIONAL) Reboot PC.
<br></br>
10. Copy all files from `C:/your_export_path/yolov8_aimbot-main/TensorRT-8.6.1.6/lib` and paste in `C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.1/bin`
<br></br>
11. Open cmd and type `cd C:/your_export_path/yolov8_aimbot-main/` then type `pip install -r requirements.txt`
<br></br>
12. Try run aimbot. `python run.py`. If aimbot works, export .pt model to .engine.
<br></br>
13. Type `yolo export model="models/sunxds_0.2.9.6.pt" format=engine half=true device=0 imgsz=320`
