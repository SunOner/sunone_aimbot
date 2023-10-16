# yolov8_aimbot
- Aim bot for first-person shooter based on pytorch and yolov8.
- The AI model is trained on more than 9,000 images (Warface, Destiny 2, Battlefield 2042 and more).
- Requirements:
1. Open CV2 (To debug images) [install from here](https://pypi.org/project/opencv-python/) [or compile with GPU support from this guide](https://www.youtube.com/watch?v=HsuKxjQhFU0&ab_channel=NicolaiNielsen)
2. NVIDIA TensorRT (To speed up the process of searching for objects up to 13 times) [Install Guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html)
3. Install via "pip install -r requirements.txt"
- Tested on:
1. Windows 10-11
2. YOLOv8.0.198
3. Opencv 4.8.1
4. Nvidia CUDNN 8.9.4.25
5. Nvidia Cuda 12.1
6. Python 3.11.6 (Anaconda env and not anaconda)
7. Pytorch 2.1.0.dev20230519+cu121
- Options:
> options.py file
1. auto_aim Automatic targeting of enemies without pressing keys
2. auto_shot Automatic targeting of enemies and automatic shooting at it
3. head_correction Automatic calculation of aiming between the detected head and the body of the enemy
4. y_portion correction of y coordinates inside the detected box
5. show_window Show cv2 window
6. show_speed Show speed inside cv2 window
7. debug_window_scale_percent adjusting the cv2 window size
8. debug_window_name cv2 window title
- AI models:
1. *.pt is default model
2. *.onnx faster than *.pt
3. *.engine is final exported model, faster than the two previously described.