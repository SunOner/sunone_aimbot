# yolov8_aimbot
- Aim bot for first-person shooter based on pytorch and yolov8.
- The AI model is trained on more than 9,000 images (Warface, Destiny 2, Battlefield 2042 and more).
- Requirements:
1. Open CV2 (To debug images) [install from here](https://pypi.org/project/opencv-python/) [or compile with GPU support from this guide](https://www.youtube.com/watch?v=HsuKxjQhFU0&ab_channel=NicolaiNielsen)
1. NVIDIA TensorRT (To speed up the process of searching for objects up to 13 times) [Install Guide](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html)
1. Ultralytics [link](https://github.com/ultralytics/ultralytics)
-Tested on:
1. YOLOv8.0.198
1. Opencv 4.8.1
1. Nvidia CUDNN 8.9.4.25
1. Nvidia Cuda 12.1
1. Python 3.11.6 (Anaconda env and not anaconda)