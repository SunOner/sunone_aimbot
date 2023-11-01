# YOLOv8 Aimbot

## Overview

YOLOv8 Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 model, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model has been trained on more than 17,000 images from popular first-person shooter games like Warface, Destiny 2, Battlefield 2042, CS:GO and CS2.

## Requirements

Before you get started, make sure you have the following prerequisites installed:

1. OpenCV2: Used for debugging images. You can install it using `pip install opencv-python`. Or install DDxcam right away with cv2 support (See point 8).

2. NVIDIA TensorRT: Speeds up the process of searching for objects up to 13 times. Install it following the [official guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html). You can also view the file `train_game.py` to see how the model can be exported .pt in .engine with options. See 'export' block of code.

3. Ultralytics: Required library available at [GitHub Ultralytics](https://github.com/ultralytics/ultralytics) `pip install ultralytics`.

4. PyTorch with GPU Support: Install PyTorch from [PyTorch's official website](https://pytorch.org/).

5. NumPy: You can typically install NumPy using pip: `pip install numpy`.

6. Win32 Tools for Python: These are needed for Windows-specific functionality. `pip install pywin32`.

7. NVIDIA CUDA Version 12.1.

8. Optional: [Dxcam](https://github.com/ra1nty/DXcam): install using `pip install dxcam[cv2]` for quick screen capture. (I'm using this). Dxcam required cv2.

9. Optional: OBS Studio for quick screen capture from obs studio (via virtual camera).

## Tested Environment

The YOLOv8 Aimbot has been tested on the following environment:

- Operating Systems: Windows 10-11
- YOLO Version: YOLOv8.0.203
- OpenCV Version: OpenCV 4.8.1
- NVIDIA cuDNN Version: 8.9.4.25
- NVIDIA CUDA Version: 12.1
- Python Version: 3.11.6 (Anaconda and non-Anaconda environments)
- PyTorch Version: 2.1.0.dev20230519+cu121
- TensorRT 8.6.1
- NumPy Version: 1.26.0

- Tested GPUs: RTX 3080-ti, RTX 3070, RTX 2080, GTX 1080, GTX 1060.

## Options

The behavior of the aim bot can be configured via the `options.py` file. Here are the available options:
- original_screen_width `int`: The current horizontal resolution of the monitor.
- original_screen_height `int`: The current vertical resolution of the monitor.

- screen_width `int`: Horizontal resolution of the object search window.
- screen_height `int`: Vertical resolution of the object search window.

- Dxcam_capture `bool`: Use [dxcam](https://github.com/ra1nty/DXcam) to capture images from the screen.
- dxcam_capture_fps `int`: Specific fps value for screen capture.
- dxcam_monitor_id `int`: Id of the monitor from which the images will be captured.
- dxcam_gpu_id `int`: Id of the GPU to be used for image capture
- dxcam_max_buffer_len `int`: [Video Buffer](https://github.com/ra1nty/DXcam#video-buffer)

- Obs_capture `bool`: Use [Obs](https://github.com/obsproject/obs-studio) to capture images from the screen.
- Obs_camera_id `int`: Virtual Camera ID.

- Windows_capture `bool`: Use the old capture method.

- head_correction `bool`: If there is a head in the detected object, then it is aimed at the head.
- body_y_offset `float`: Allows correction of y coordinates inside the body detected box.
- head_y_offset `float`: Allows correction of y coordinates inside the head detected box.

- mouse_smoothing `float`: Smoothing when moving the mouse.
- mouse_auto_shoot `bool`: Automatic shooting.
- mouse_auto_shoot_timer `bool`: Adds a delay before firing.
- mouse_auto_shoot_sleep_time `float`: Delay before firing in seconds and milliseconds.
- mouse_auto_aim `bool`: Automatic targeting.

- show_window `bool`: Shows the OpenCV2 window for visual feedback.
- show_speed `bool`: Displays speed information inside the OpenCV2 window.
- debug_window_scale_percent `int`: Adjusts the size of the OpenCV2 window.
- debug_window_name `str`: Specifies the title of the OpenCV2 window.

- model_path `str`: Model path.

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

- Run "yolo export model="model_path/*.pt" format=engine half=true device=0 workspace=8 imgsz=640"


## Notes / Recommendations

- Limit the maximum value of frames per second in the game in which you will use it. Do not overload the graphics card.
- Do not set high graphics settings in games.
- Limit the browser (try not to watch YouTube while playing and working AI at the same time, for example (of course if you don't have a super duper graphics card)) and so on, which loads the video card.
- Try to use TensorRT for acceleration. `.pt` model is good, but does not have as much speed as `.engine`.
- If the program is running, everything is detected, but the mouse itself is not aimed at the target, then try running the program as an administrator.
- Turn off the cv2 debug window, this saves system resources.

## Support the project

- Support this project by training a model for a variety of games and improving algorithms. [DonationAlerts](https://www.donationalerts.com/r/sunxds).
