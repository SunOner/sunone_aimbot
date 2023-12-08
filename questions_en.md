1. All commands are executed from the command line while being in the program's directory.
   - After launching the command line, execute the command `cd where_you_unpacked_the_bot` for example 'cd C:\Users\amongus\downloads\yolov8_aimbot'
2. How to run the program?
   - `python main.py` or `py main.py`
3. How to change the settings?
   - Open the file options.py using notepad or another text editor, after changing the options save the file.
4. How to reduce excessive aim shaking?
   - Increase the value of `mouse_break_force`
5. I want the mouse movement to be even smoother.
   - Increase the value of `mouse_smoothing` by 2, 4, 8, 16, etc., also increment the fps value.
6. The model does not export, and the line appears TensorRT: export failure ❌ 0.5s: Could not find: cublas64_12.dll. Is it on your PATH?
   - Download [cudnn64_8.zip](https://disk.yandex.ru/d/cm1Wi7OdkLtcLQ) and unpack it in C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/(cuda version)/bin
7. How to install a new model that I downloaded from boosty?
   - Place it in the `models/` folder, go to options.py and change AI_model_path = `models/sunxds_0.3.4.pt` or AI_model_path = `models/sunxds_0.3.4.engine`
8. How to export the model?
   - Run `python train_game.py` if you're using a model from GitHub. For models from boosty, you must first change the parameter `AI_model_path` in options.py to the new model and then run the file.
9. How to run it if the game is in full-screen mode?
   - Minimize the game, launch the bot, and then maximize the game. (this is a dxcam bug).
10. The aim shoots above the head, how to adjust?
    - Modify the `body_y_offset` parameter. The lower the value, the lower the aiming.
11. Auto-shoot does not work in some games.
    - Some games have protection against programmatic mouse clicks.
12. Errors are reported and fixed [here](https://github.com/SunOner/yolov8_aimbot/issues?q=is%3Aissue)
13. I have a suggestion for improvement!
    - [Create a topic here](https://github.com/SunOner/yolov8_aimbot/discussions)

