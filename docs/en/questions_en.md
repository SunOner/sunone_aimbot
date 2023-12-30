1. All commands are executed from the command line when you are in the program's directory.
   - After launching the command line, execute the command `cd path_to_bot_unpacking`, for example, `cd C:\Users\amongus\downloads\yolov8_aimbot`
2. How to run the program?
   - `python run.py` or `py run.py`
3. How to change settings?
   - Open the file config.ini using Notepad or another text editor, after changing options save the file.
4. Model export interrupts at `ONNX: starting export with onnx 1.15.0 opset 17...`
   - This is a bug of the onnx module. Each time before exporting a model, execute the command `pip uninstall onnx`.
5. I want the mouse movement to be even smoother.
   - Increase the value of `mouse_smoothing` by 2, 4, 8, 16, etc., also increase the fps value.
6. The model does not export, and the line appears TensorRT: export failure ❌ 0.5s: Could not find: cublas64_12.dll. Is it on your PATH?
   - Download [cudnn64_8.zip](https://disk.yandex.ru/d/cm1Wi7OdkLtcLQ) and unpack it in C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/(your cuda version)/bin
7. How to install a new model that I downloaded from boosty?
   - Place it in the `models/` folder, go to config.ini and change AI_model_path = sunxds_0.3.4.pt or AI_model_path = sunxds_0.3.4.engine, if you exported the model to .engine.
8. How to export a model?
   - Go to the [export](https://github.com/SunOner/yolov8_aimbot?tab=readme-ov-file#export-pt-model-to-engine) section on the github page.
9. How to run it if the game is in full screen mode? / Why does the aimbot crash when I enter the game in full screen mode?
   - Minimize the game, start the bot, and then quickly maximize the game (this is a bettercam error).
10. The sight shoots above the head, how to adjust?
    - Change the `body_y_offset` parameter. The lower the value, the lower the aim.
11. Autoshot does not work in some games.
    - Some games have protection against programmed mouse clicks. Use [Arduino](https://github.com/SunOner/HID_Arduino).
12. Errors are reported and fixed [here](https://github.com/SunOner/yolov8_aimbot/issues?q=is%3Aissue)
13. I have a suggestion for improvement!
    - [Create a topic here](https://github.com/SunOner/yolov8_aimbot/discussions)
14. The aimbot takes a long time to aim. It's kind of jerky. / WARNING NMS time limit exceeded
	- Do not overload the graphics card!
	- Do not set high game settings.
	- Lock the frame rate (for example, if you have a 144Hz monitor, lock FPS to 144 in the game).
	- Turn off instant replays.
	- Try changing the screen resolution in the system to a lower one.
	- And so on...
15. Where to download new models?
	- They can be obtained by supporting the project [here](https://boosty.to/sunone).
16. There are false positives, how to eliminate them?
	- Increase the value of `AI_conf` in the config.
17. AttributeError: 'Bettercam' object has no attribute 'is_capturing'
	- Go to "Settings->System->Display->Graphics->Classic Application-Overview" and add the python executable file (It should be here by default "C:\Users\your_user_name\AppData\Local\Programs\Python\Python311\python.exe"), specify "energy saving" in the parameters. This is due to the fact that on most laptops, the duplicator is powered by an integrated graphics processor.