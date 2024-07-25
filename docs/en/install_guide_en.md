## Yolov8 Aimbot Manual Installation Guide
1. **(OPTIONAL FOR CLEAN INSTALLATION)** Remove all installed versions of Python and Cuda, then restart your computer.
<br></br>
2. Update your Nvidia graphics driver. Cudnn should install automatically after updating the driver.
<br></br>
3. Download and install [Python](https://www.python.org/downloads/) version 3.11.6. On the initial screen of the installer, activate the option "Add Python 3.11.6 to PATH"!
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/python.png)
<br></br>
4. Download and extract the [sunone aimbot](https://github.com/SunOner/sunone_aimbot) files.
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/aimbot.png)
<br></br>
5. Download and install Cuda version 12.4, then restart your computer [download](https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe).
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/cuda.png)
<br></br>
6. Open the command prompt and enter `python -m pip install --upgrade pip`, then `pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124`.
<br></br>
7. Next, in the command prompt, enter `cd C:/path_where_you_extracted/sunone_aimbot-main/`, then `pip install -r requirements.txt`.
<br></br>
8. Try running the aimbot. Enter `python run.py`. If the aimbot works, export the .pt model to .engine.
<br></br>
9. Enter `yolo export model="models/sunxds_0.4.1.pt" format=engine device=0 imgsz=480 half=True`. The export may take more than 10 minutes (depending on your PC components). After exporting, don't forget to change the model in `config.ini` to `sunxds_0.4.1.engine`.