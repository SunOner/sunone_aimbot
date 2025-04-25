<div align="center">

# Sunone Aimbot
[![Python Version](https://img.shields.io/badge/Python-3.11.6-FFD43B?logo=python)](https://github.com/SunOner/sunone_aimbot)
[![License MIT](https://badgen.net/github/license/SunOner/sunone_aimbot)](https://github.com/SunOner/sunone_aimbot/blob/main/LICENSE)
[![Github stars](https://img.shields.io/github/stars/SunOner/sunone_aimbot?color=ffb500)](https://github.com/SunOner/sunone_aimbot)
[![Discord server](https://badgen.net/discord/online-members/sunone)](https://discord.gg/37WVp6sNEh)
  <p>
    <a href="https://github.com/SunOner/sunone_aimbot/releases" target="_blank">
      <img width="75%" src="https://raw.githubusercontent.com/SunOner/sunone_aimbot/main/media/one.gif"></a>
  </p>
</div>

## Overview
Sunone Aimbot is an AI-powered aim bot for first-person shooter games. It leverages the YOLOv8 and YOLOv10 models, PyTorch, and various other tools to automatically target and aim at enemies within the game. The AI model in repository has been trained on more than 30,000 images from popular first-person shooter games like Warface, Destiny 2, Battlefield (all series), Fortnite, The Finals, CS2 and more.
> [!WARNING]
> Use it at your own risk, we do not guarantee that you may be blocked!

> [!NOTE]
> The recommended graphics card for starting and more productive and stable operation starts with the rtx 20 series.

## Requirements
Before you get started, make sure you have the following prerequisites installed and pay attention to the versions in [Tested Environment](https://github.com/SunOner/sunone_aimbot?tab=readme-ov-file#tested-environment) block, this may cause errors in launching the aimbot.

- [Config options](https://github.com/SunOner/sunone_aimbot_docs/blob/main/config/config.md)
- [Install guide](https://github.com/SunOner/sunone_aimbot_docs/blob/main/install/helper.md)
- [Questions](https://github.com/SunOner/sunone_aimbot_docs/blob/main/questions/questions.md)
- [Arduino setup](https://github.com/SunOner/HID_Arduino)
- [Arduino Logitech G-series](https://github.com/SunOner/usb-host-shield-mouse_for_ai_aimbot)
- [Discord server](https://discord.gg/sunone)
- [AI Models docs](https://github.com/SunOner/sunone_aimbot_docs/blob/main/ai_models/ai_models.md)

<br></br>
- To launch the aimbot after all installations, start run_ai.bat or type `py run.py`.

# Use the new C++ version of the AI-Aimbot!
- [Sunone_aimbot_cpp](https://github.com/SunOner/sunone_aimbot_cpp): The Python version is good, but C++ is even better. It has an overlay, is faster, and much more. Currently, it is updated much more frequently than the Python version. It's better to use the C++ version.

## Working environment:
<table>
  <thead><tr><th>Windows</th><td>10 and 11(priority)</td></thead>
  <thead><tr><th>Python:</th><td>3.11.6</td></tr></thead>
  <thead><tr><th>CUDA:</th><td>12.4</td></tr></thead>
  <thead><tr><th>TensorRT:</th><td>10.8.0.43</td></tr></thead>
  <thead><tr><th>Ultralytics:</th><td>8.3.78</td></tr></thead>
  <thead><tr><th>GitHub AI Model:</th><td>sunxds_0.5.6 (YOLOv10)</td></tr></thead>
  <thead><tr><th>Supporters AI Model:</th><td>sunxds_0.7.6 (YOLOv12)</td></tr></thead>
</table>

## Notes / Recommendations
- Limit the maximum value of frames per second in the game in which you will use it. And also do not set the screen resolution to high. Do not overload the graphics card.
- Do not set high graphics settings in games.
- Limit the browser (try not to watch YouTube while playing and working AI at the same time, for example (of course if you don't have a super duper graphics card)) and so on, which loads the video card.
- Try to use TensorRT for acceleration. `.pt` model is good, but does not have as much speed as `.engine`.
- Turn off the cv2 debug window, this saves system resources.
- Do not increase the object search window resolution, this may affect your search speed.
- If you have started the application and nothing happens, it may be working, close it with the F2 key and change the `show_window` option to `True` in the file [config.ini](https://github.com/SunOner/sunone_aimbot/blob/main/config.ini) to make sure that the application is working.

## Support the project
[Boosty](https://boosty.to/sunone) [Patreon](https://www.patreon.com/sunone).

## License
This project is licensed under the MIT License. See **[LICENSE](https://github.com/SunOner/sunone_aimbot/blob/main/LICENSE)** for details
