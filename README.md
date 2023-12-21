<div align="center">
  
### YOLOv8 Aimbot
[![Python Version](https://img.shields.io/badge/Python-3.11.6-FFD43B?logo=python)](https://github.com/SunOner/yolov8_aimbot)
[![License MIT](https://badgen.net/github/license/SunOner/yolov8_aimbot)](https://github.com/SunOner/yolov8_aimbot/blob/main/LICENSE)
[![Discord server](https://badgen.net/discord/online-members/sMZVvVV)](https://discord.gg/sMZVvVV)
[![Github stars](https://img.shields.io/github/stars/SunOner/yolov8_aimbot?color=ffb500)](https://github.com/SunOner/yolov8_aimbot)
  <p>
    <a href="https://github.com/SunOner/yolov8_aimbot/releases" target="_blank">
      <img width="75%" src="https://raw.githubusercontent.com/SunOner/yolov8_aimbot/main/media/one.gif"></a>
  </p>
</div>

## Overview
YOLOv8 Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 model, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model in repository has been trained on more than 17,000 images from popular first-person shooter games like Warface, Destiny 2, Battlefield 2042, CS:GO and CS2.
> [!WARNING]
> Use it at your own risk, we do not guarantee that you may be blocked!

## Requirements
Before you get started, make sure you have the following prerequisites installed and pay attention to the versions in `Tested Environment` block, this may cause errors in launching the aimbot:

- Information in English:
  - [Install guide](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/en/install_guide_en.md)
  - [Questions and answers](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/en/questions_en.md)
  - [Arduino setup](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/en/arduino_en.md)
<br></br>
- Информация на Русском языке:
  - [Инструкция по установке](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/ru/install_guide_ru.md)
  - [Вопросы и ответы](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/ru/questions_ru.md)
  - [Установка ардуино](https://github.com/SunOner/yolov8_aimbot/blob/main/docs/ru/arduino_ru.md)
<br></br>
- I advise you to check the environment by running `checks.py`, it will let you know what and where to fix or re-install.
- To launch the aimbot after all installations, type ``python run.py`` or `py run.py` in cmd.

## Tested Environment
### The YOLOv8 Aimbot has been tested on the following environment:
<table>
  <thead><tr><th>Operating Systems:</th><td>Windows 10</td><td>Windows 11</td></tr></thead>
  <thead><tr><th>NVIDIA CUDA Version:</th><td>12.1</td></tr></thead>
  <thead><tr><th>NVIDIA cuDNN Version:</th><td>8.9.4.25</td></thead>
  <thead><tr><th>TensorRT Version:</th><td>8.6.1</td></tr></thead>
  <thead><tr><th>Python Version:</th><td>3.11.6</td></tr></thead>
  <thead><tr><th>PyTorch Version:</th><td>2.1.1+cu121</td><td>2.1.0.dev20230519+cu121</td></tr></thead>
  <thead><tr><th>YOLO Version:</th><td>YOLOv8.0.226</td></tr></thead>
  <thead><tr><th>OpenCV Version:</th><td>4.8.1</td></tr></thead>
  <thead><tr><th>NumPy Version:</th><td>1.26.0</td></tr></thead>
</table>
<details><summary><b>Tested GPUs:</b></summary><table style="table-layout: fixed; width: 100%">
   <thead><tr><td>RTX 4080</td><td>RTX 4070</td><td>RTX 4060</td><td>RTX 3090</td><td>RTX 3080-ti</td><td>RTX 3070</td><td>RTX 3050</td>
   <td>RTX 2080</td><td>RTX 2060-super</td><td>GTX 1660-super</td><td>GTX 1660</td><td>GTX 1650</td><td>GTX 1080</td><td>GTX 1060</td><td>GTX 1050-ti</td><td>GTX 1050</td><td>GTX 750-ti</td><td>GTX 750</td></tr></thead>
</table></details>

## Options
The behavior of the aim bot can be configured via the [`config.ini`](https://github.com/SunOner/yolov8_aimbot/blob/main/config.ini) file. Here are the available options:

### Object Search window resolution:
- detection_window_width `int`: Horizontal resolution of the object search window.
- detection_window_height `int`: Vertical resolution of the object search window.

### Dxcam capture method:
- Dxcam_capture `bool`: Use [dxcam](https://github.com/ra1nty/DXcam) to capture images from the screen.
- dxcam_capture_fps `int`: Specific fps value for screen capture.
- dxcam_monitor_id `int`: Id of the monitor from which the images will be captured.
- dxcam_gpu_id `int`: Id of the GPU to be used for image capture
- dxcam_max_buffer_len `int`: [Video Buffer](https://github.com/ra1nty/DXcam#video-buffer)

### Obs capture method:
- Obs_capture `bool`: Use [Obs](https://github.com/obsproject/obs-studio) to capture images from the screen.
- Obs_camera_id `int`: Virtual Camera ID.
- Obs_capture_fps `int`: Specific fps value for screen capture.

### Windows capture method:
- native_Windows_capture `bool`: Use the windows native capture method.

### Aim settings:
- body_y_offset `float`: Allows correction of y coordinates inside the body detected box if head is not detected.
- hideout_targets `bool`: Allows shooting at targets on the range (for example in warface on the polygon or in aimlabs).
- disable_headshot `bool`: Disable head targerting.

### Hot keys:
- Right mouse button `str`: Aiming at the target.
- F2 `str`: Exit.
- F3 `str`: Pause AIM.

### Mouse settings:
- mouse_smoothing `float`: Smoothing when moving the mouse.
- mouse_auto_shoot `bool`: Automatic shooting. (Not working in some games).
- mouse_auto_aim `bool`: Automatic targeting.
- mouse_native `bool`: Use windows native mouse input.
- mouse_wild_mouse `bool`: Simulate human like mouse input.

### AI options:
- AI_model_path `str`: AI model path.
- AI_image_size `int`: Model image size.
- AI_conf `float`: How many percent is AI sure that this is the right goal.
- AI_iou `float`: Intersection over union (IoU) threshold for NMS.
- AI_device `int` or `str`: Device to run on, i.e. cuda AI_device=0/1/2/3 or AI_device='cpu'.
- AI_max_det `int`: Maximum number of detections per frame.

### Cv2 debug window settings:
- show_window `bool`: Shows the OpenCV2 window for visual feedback.
- show_speed `bool`: Displays speed information inside the OpenCV2 window.
- show_fps `bool`: Displays FPS in the corner.
- show_boxes `bool`: Displays detectable objects.
- show_labels `bool`: Displays the name of the detected object.
- show_conf `bool`: Displays object confidence threshold for detection.
- debug_window_scale_percent `int`: Adjusts the size of the OpenCV2 window.
- debug_window_name `str`: Specifies the title of the OpenCV2 window.

## AI Models
### The repository provides multiple AI models for different purposes:
- *.pt: Default AI model.
- *.onnx: The model is optimized to run on processors.
- *.engine: Final exported model, which is faster than the previous two.
<br></br>
- My .engine model was exported using specification version 8.6 (on an rtx 3080-TI graphics card). So if you were to run my .engine model on a gtx 1080 graphics card, the model would not start. You need to export it yourself. See what specification your graphics card [supports](https://ru.wikipedia.org/wiki/CUDA). So if your graphics card supports the 8.6 specification, then the model will start. The error may also occur due to the fact that I exported the model in a different version of TensorRT, it's better to just export the model yourself.

## Export .pt model to .engine
Run in console:
```cmd
yolo export model="models/sunxds_0.2.1_nano_320.pt" format=engine half=true device=0 imgsz=320
```
  - `model="model_path/*.pt"`: Path to model.
  - `format=engine`: TensorRT model format.
  - `half=true`: Use Half-precision floating-point format.
  - `device=0`: GPU id.
  - `workspace=8`: GPU max video memory.
  - `imgsz=320`: Model image size.
  - `verbose=False`: Debug stuff. Convenient function, can show errors when exporting.

## Notes / Recommendations
- Limit the maximum value of frames per second in the game in which you will use it. Do not overload the graphics card.
- Do not set high graphics settings in games.
- Limit the browser (try not to watch YouTube while playing and working AI at the same time, for example (of course if you don't have a super duper graphics card)) and so on, which loads the video card.
- Try to use TensorRT for acceleration. `.pt` model is good, but does not have as much speed as `.engine`.
- If the program is running, everything is detected, but the mouse itself is not aimed at the target, then try running the program as an administrator.
- Turn off the cv2 debug window, this saves system resources.
- Do not increase the object search window resolution, this may affect your search speed.
- If you have started the application and nothing happens, it may be working, close it with the F2 key and change the show_window setting to Yes in the file [config.ini](https://github.com/SunOner/yolov8_aimbot/blob/main/config.ini) to make sure that the application is working.

## Support the project
I will post new models [here](https://boosty.to/sunone).

## License
This project is licensed under the MIT License. See **[LICENSE](https://github.com/SunOner/yolov8_aimbot/blob/main/LICENSE)** for details
