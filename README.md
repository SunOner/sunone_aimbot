# YOLOv8 Aimbot
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/one.gif)
## Overview

YOLOv8 Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 model, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model has been trained on more than 17,000 images from popular first-person shooter games like Warface, Destiny 2, Battlefield 2042, CS:GO and CS2.

## Requirements

Before you get started, make sure you have the following prerequisites installed and pay attention to the versions in `Tested Environment` block, this may cause errors in launching the aimbot:

- Run the command to install the libraries `pip install -r requirements.txt`.
- I advise you to check the environment by running `checks.py`, it will let you know what and where to fix or re-install.

1. OpenCV2: Used for debugging images. You can install it using `pip install opencv-python`. Or install Dxcam right away with cv2 support (See point 8).

2. NVIDIA TensorRT: Speeds up the process of searching for objects up to 13 times. Install it following the [official guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html). You can also view the file `train_game.py` to see how the model can be exported .pt in .engine with options in code. See 'export' block of code or [Export .pt model to .engine part](https://github.com/SunOner/yolov8_aimbot#export-pt-model-to-engine).

3. Ultralytics: Required library available at [GitHub Ultralytics](https://github.com/ultralytics/ultralytics) `pip install ultralytics`.

4. PyTorch with GPU Support: Install PyTorch from [PyTorch's official website](https://pytorch.org/).

5. NumPy: You can typically install NumPy using pip: `pip install numpy`.

6. Win32 Tools for Python: These are needed for Windows-specific functionality. `pip install pywin32`.

7. NVIDIA CUDA Version 12.1.

8. Asyncio: `pip install asyncio`.

9. [Dxcam](https://github.com/ra1nty/DXcam): install using `pip install dxcam[cv2]` for quick screen capture. (I'm using this). Dxcam required cv2.

10. Screeninfo: `pip install screeninfo`.

11. Optional: OBS Studio for quick screen capture via virtual camera.

## Tested Environment

The YOLOv8 Aimbot has been tested on the following environment:

- Operating Systems: Windows 10-11
- YOLO Version: YOLOv8.0.217
- OpenCV Version: OpenCV 4.8.1
- NVIDIA cuDNN Version: 8.9.4.25
- NVIDIA CUDA Version: 12.1
- Python Version: 3.11.6 (Anaconda and non-Anaconda environments)
- PyTorch Version: 2.1.0.dev20230519+cu121
- TensorRT 8.6.1
- NumPy Version: 1.26.0

- Tested GPUs: RTX 3090, RTX 3080-ti, RTX 3070, RTX 2080, GTX 1080, GTX 1060, GTX 750-ti.

## Options

The behavior of the aim bot can be configured via the `options.py` file. Here are the available options:

Screen resolution:
- original_screen_width `int`: The current horizontal resolution of the monitor.
- original_screen_height `int`: The current vertical resolution of the monitor.

Object Search window resolution:
- screen_width `int`: Horizontal resolution of the object search window.
- screen_height `int`: Vertical resolution of the object search window.

Dxcam capture method:
- Dxcam_capture `bool`: Use [dxcam](https://github.com/ra1nty/DXcam) to capture images from the screen.
- dxcam_capture_fps `int`: Specific fps value for screen capture.
- dxcam_monitor_id `int`: Id of the monitor from which the images will be captured.
- dxcam_gpu_id `int`: Id of the GPU to be used for image capture
- dxcam_max_buffer_len `int`: [Video Buffer](https://github.com/ra1nty/DXcam#video-buffer)

Obs capture method:
- Obs_capture `bool`: Use [Obs](https://github.com/obsproject/obs-studio) to capture images from the screen.
- Obs_camera_id `int`: Virtual Camera ID.
- Obs_capture_fps `int`: Specific fps value for screen capture.

Windows capture method:
- native_Windows_capture `bool`: Use the windows native capture method.

Aim settings:
- body_y_offset `float`: Allows correction of y coordinates inside the body detected box if head is not detected.
- hideout_targets `bool`: Allows shooting at targets on the range (for example in warface on the polygon or in aimlabs).

Mouse settings:
- mouse_smoothing `float`: Smoothing when moving the mouse.
- mouse_auto_shoot `bool`: Automatic shooting. (Not working in some games).
- mouse_auto_aim `bool`: Automatic targeting.
- mouse_native `bool`: Use windows native mouse input.

AI options:
- AI_model_path `str`: AI model path.
- AI_image_size `int`: Model image size.
- AI_conf = `float`: How many percent is AI sure that this is the right goal.
- AI_iou = `float`: Intersection over union (IoU) threshold for NMS.
- AI_device = `int` or `str`: Device to run on, i.e. cuda AI_device=0/1/2/3 or device='cpu'.
- AI_max_det = `int`: Maximum number of detections per frame.

Cv2 debug window settings:
- show_window `bool`: Shows the OpenCV2 window for visual feedback.
- show_speed `bool`: Displays speed information inside the OpenCV2 window.
- show_fps `bool`: Displays FPS in the corner.
- show_boxes `bool`: Displays detectable objects.
- show_labels `bool`: Displays the name of the detected object. (TODO)
- debug_window_scale_percent `int`: Adjusts the size of the OpenCV2 window.
- debug_window_name `str`: Specifies the title of the OpenCV2 window.

## AI Models

The repository provides multiple AI models for different purposes:

- *.pt: Default AI model.
- *.onnx: Faster than *.pt model.
- *.engine: Final exported model, which is faster than the previous two.

- My .engine model was exported using specification version 8.6 (on an rtx 3080-TI graphics card). So if you were to run my .engine model on a gtx 1080 graphics card, the model would not start. You need to export it yourself. See what specification your graphics card [supports](https://ru.wikipedia.org/wiki/CUDA). So if your graphics card supports the 8.6 specification, then the model will start. The error may also occur due to the fact that I exported the model in a different version of TensorRT, it's better to just export the model yourself.

## Hot keys

- Right mouse button: Aiming at the target.
- F2: Exit.

## Export .pt model to .engine

- Run `yolo export model="models/sunxds_0.2.1_nano_320.pt" format=engine half=true device=0 workspace=8 imgsz=320 verbose=False`
<br></br>
`model="model_path/*.pt"`; Path to model.
<br></br>
`format=engine`: TensorRT model format.
<br></br>
`half=true`: Use Half-precision floating-point format.
<br></br>
`device=0`: GPU id.
<br></br>
`workspace=8`: GPU max video memory.
<br></br>
`imgsz=320`: Model image size.
<br></br>
`verbose=False`: Debug stuff. Convenient function, can show errors when exporting.
## Notes / Recommendations

- Limit the maximum value of frames per second in the game in which you will use it. Do not overload the graphics card.
- Do not set high graphics settings in games.
- Limit the browser (try not to watch YouTube while playing and working AI at the same time, for example (of course if you don't have a super duper graphics card)) and so on, which loads the video card.
- Try to use TensorRT for acceleration. `.pt` model is good, but does not have as much speed as `.engine`.
- If the program is running, everything is detected, but the mouse itself is not aimed at the target, then try running the program as an administrator.
- Turn off the cv2 debug window, this saves system resources.
- Do not increase the object search window resolution, this may affect your search speed.
- If you have started the application and nothing happens, it may be working, close it with the F2 key and change the show_window setting to True in the file options.py to make sure that the application is working.
## Support the project

- I will post new models [here](https://boosty.to/sunone).
