# YOLOv8 Aimbot
![](https://github.com/SunOner/yolov8_aimbot/blob/main/media/one.gif)
## Overview

YOLOv8 Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 model, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model in repository has been trained on more than 17,000 images from popular first-person shooter games like Warface, Destiny 2, Battlefield 2042, CS:GO and CS2.

## Requirements

Before you get started, make sure you have the following prerequisites installed and pay attention to the versions in `Tested Environment` block, this may cause errors in launching the aimbot:

- [EN Install guide](https://github.com/SunOner/yolov8_aimbot/blob/main/install_guide_en.md)
- [RU Install guide](https://github.com/SunOner/yolov8_aimbot/blob/main/install_guide_ru.md)

- I advise you to check the environment by running `checks.py`, it will let you know what and where to fix or re-install.
- To launch the aimbot after all installations, type `python main.py` in cmd.
## Tested Environment

The YOLOv8 Aimbot has been tested on the following environment:

- Operating Systems: Windows 10-11
- YOLO Version: YOLOv8.0.222
- OpenCV Version: OpenCV 4.8.1
- NVIDIA cuDNN Version: 8.9.4.25
- NVIDIA CUDA Version: 12.1
- Python Version: 3.11.6 (Anaconda and non-Anaconda environments)
- PyTorch Version: 2.1.0.dev20230519+cu121
- TensorRT 8.6.1
- NumPy Version: 1.26.0

| Tested GPUs |
|----------|
| RTX 4080 |
| RTX 4070 |
| RTX 4060 |
| RTX 3090 |
| RTX 3080-ti |
| RTX 3070 |
| RTX 3050 |
| RTX 2080 |
| GTX 1660 |
| GTX 1080 |
| GTX 1060 |
| GTX 1050-ti |
| GTX 750-ti |

## Options

The behavior of the aim bot can be configured via the `options.py` file. Here are the available options:

Object Search window resolution:
- detection_window_width `int`: Horizontal resolution of the object search window.
- detection_window_height `int`: Vertical resolution of the object search window.

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
- disable_headshot `bool`: Disable head targerting.

Mouse settings:
- mouse_smoothing `float`: Smoothing when moving the mouse.
- mouse_auto_shoot `bool`: Automatic shooting. (Not working in some games).
- mouse_auto_aim `bool`: Automatic targeting.
- mouse_native `bool`: Use windows native mouse input.
- mouse_wild_mouse `bool`: Simulate human like mouse input.

AI options:
- AI_model_path `str`: AI model path.
- AI_image_size `int`: Model image size.
- AI_conf `float`: How many percent is AI sure that this is the right goal.
- AI_iou `float`: Intersection over union (IoU) threshold for NMS.
- AI_device `int` or `str`: Device to run on, i.e. cuda AI_device=0/1/2/3 or device='cpu'.
- AI_max_det `int`: Maximum number of detections per frame.

Cv2 debug window settings:
- show_window `bool`: Shows the OpenCV2 window for visual feedback.
- show_speed `bool`: Displays speed information inside the OpenCV2 window.
- show_fps `bool`: Displays FPS in the corner.
- show_boxes `bool`: Displays detectable objects.
- show_labels `bool`: Displays the name of the detected object.
- show_conf `bool`: Displays object confidence threshold for detection.
- debug_window_scale_percent `int`: Adjusts the size of the OpenCV2 window.
- debug_window_name `str`: Specifies the title of the OpenCV2 window.

## AI Models

The repository provides multiple AI models for different purposes:

- *.pt: Default AI model.
- *.onnx: The model is optimized to run on processors.
- *.engine: Final exported model, which is faster than the previous two.

- My .engine model was exported using specification version 8.6 (on an rtx 3080-TI graphics card). So if you were to run my .engine model on a gtx 1080 graphics card, the model would not start. You need to export it yourself. See what specification your graphics card [supports](https://ru.wikipedia.org/wiki/CUDA). So if your graphics card supports the 8.6 specification, then the model will start. The error may also occur due to the fact that I exported the model in a different version of TensorRT, it's better to just export the model yourself.

## Hot keys

- `Right mouse button`: Aiming at the target.
- `F2`: Exit.

## Export .pt model to .engine

- Run `yolo export model="models/sunxds_0.2.1_nano_320.pt" format=engine half=true device=0 imgsz=320`
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
