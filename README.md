# yolov8_aimbot
- Aim bot for first-person shooter based on pytorch and yolov8.
- The AI model is trained on more than 9,000 images (Warface, Destiny 2, Battlefield 2042 and more).
- Requirements:
1. Open CV2 (To debug images) [install from here](https://pypi.org/project/opencv-python/) [or compile with GPU support from this guide](https://www.youtube.com/watch?v=HsuKxjQhFU0&ab_channel=NicolaiNielsen)
1. NVIDIA TensorRT (To speed up the process of searching for objects up to 13 times) [Install Guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html)
1. Ultralytics [link](https://github.com/ultralytics/ultralytics)
1. Pytorch with GPU support [link](https://pytorch.org/)
1. Numpy
1. Win32 tools for python
- Tested on:
1. Windows 10-11
1. YOLOv8.0.198
1. Opencv 4.8.1
1. Nvidia CUDNN 8.9.4.25
1. Nvidia Cuda 12.1
1. Python 3.11.6 (Anaconda env and not anaconda)
1. Pytorch 2.1.0.dev20230519+cu121
1. Numpy 1.26.0
- Options:
> options.py file
1. auto_aim Automatic targeting of enemies without pressing keys
1. auto_shot Automatic targeting of enemies and automatic shooting at it
1. head_correction Automatic calculation of aiming between the detected head and the body of the enemy
1. y_portion correction of y coordinates inside the detected box
1. show_window Show cv2 window
1. show_speed Show speed inside cv2 window
1. debug_window_scale_percent adjusting the cv2 window size
1. debug_window_name cv2 window title
- AI models:
1. *.pt is default model
1. *.onnx faster than *.pt
1. *.engine is final exported model, faster than the two previously described.