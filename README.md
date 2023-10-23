# YOLOv8 Aimbot

## Overview

YOLOv8 Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 model, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model has been trained on more than 9,000 images from popular first-person shooter games like Warface, Destiny 2, and Battlefield 2042.

## Requirements

Before you get started, make sure you have the following prerequisites installed:

1. OpenCV2: Used for debugging images. You can install it using [this link](https://pypi.org/project/opencv-python) or compile it with GPU support using [this guide](https://www.youtube.com/watch?v=HsuKxjQhFU0&ab_channel=NicolaiNielsen).

2. NVIDIA TensorRT: Speeds up the process of searching for objects up to 13 times. Install it following the [official guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html).

3. Ultralytics: Required library available at [GitHub Ultralytics](https://github.com/ultralytics/ultralytics).

4. PyTorch with GPU Support: Install PyTorch from [PyTorch's official website](https://pytorch.org/).

5. NumPy: You can typically install NumPy using pip: `pip install numpy`.

6. Win32 Tools for Python: These are needed for Windows-specific functionality.

## Tested Environment

The YOLOv8 Aimbot has been tested on the following environment:

- Operating Systems: Windows 10-11
- YOLO Version: YOLOv8.0.198
- OpenCV Version: OpenCV 4.8.1
- NVIDIA cuDNN Version: 8.9.4.25
- NVIDIA CUDA Version: 12.1
- Python Version: 3.11.6 (Anaconda and non-Anaconda environments)
- PyTorch Version: 2.1.0.dev20230519+cu121
- NumPy Version: 1.26.0
- Dxcam pip install dxcam[cv2]

## Options

The behavior of the aim bot can be configured via the `options.py` file. Here are the available options:
- original_screen_width: The current horizontal resolution of the monitor.
- original_screen_height: The current vertical resolution of the monitor.

- screen_width: Horizontal resolution of the object search window.
- screen_height: Vertical resolution of the object search window.

- Dxcam_capture: Use [dxcam](https://github.com/ra1nty/DXcam) to capture images from the screen.
- dxcam_capture_fps: Specific fps value for screen capture.
- dxcam_monitor_id: Id of the monitor from which the images will be captured.
- dxcam_gpu_id: Id of the GPU to be used for image capture
- dxcam_max_buffer_len: [Video Buffer](https://github.com/ra1nty/DXcam#video-buffer)

- Obs_capture: Use [Obs](https://github.com/obsproject/obs-studio) to capture images from the screen.
- Obs_camera_id: Virtual Camera ID.

- Windows_capture: Use the old capture method.

- head_correction: Automatically calculates aiming between the detected head and the body of the enemy.
- y_portion: Allows correction of y coordinates inside the detected box.

- mouse_sensitivity: The sensitivity of the mouse, the higher the value, the less the shaking of the sight.

- show_window: Shows the OpenCV2 window for visual feedback.
- show_speed: Displays speed information inside the OpenCV2 window.
- debug_window_scale_percent: Adjusts the size of the OpenCV2 window.
- debug_window_name: Specifies the title of the OpenCV2 window.

- model_path: Model path.
## AI Models

The repository provides multiple AI models for different purposes:

- *.pt: Default AI model.
- *.onnx: Faster than *.pt model.
- *.engine: Final exported model, which is faster than the previous two.
## Hot keys

- Right mouse button: Capturing a target.
- F2: Exit.

Feel free to contribute and make this aim bot even more powerful and versatile!

## Export .pt model to .engine

- Run "yolo export model="path_to_model\model.pt" format=engine half=true device=0"
## Acknowledgments

We'd like to express our gratitude to the open-source community, the Ultralytics team, and the developers of the YOLOv8 model for making this project possible.
