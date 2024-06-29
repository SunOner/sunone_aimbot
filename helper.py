import os
import subprocess
import time
import re
import sys
import shutil
import zipfile
import ctypes
import configparser
import threading

try:
    import streamlit as st
    import requests
    import numpy
    import bettercam
    import win32api, win32con, win32gui
    import ultralytics
    from ultralytics import YOLO
    import screeninfo
    import asyncio
    import serial
    import cv2
    import cuda
    import onnxruntime
    import torch
    from packaging import version
except ModuleNotFoundError:
    os.system("pip install -r requirements.txt")
    os.system("streamlit run helper.py")
    quit()

HELPER, EXPORT, CONFIG = st.tabs(["HELPER", "EXPORT", "CONFIG"])
    
with HELPER:
    st.title("Sunone Aimbot Helper")

    # Tools
    def download_file(url, filename):
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get("content-length", 0))
        progress_bar = st.progress(0)
        downloaded_size = 0
        start_time = time.time()

        speed_text = st.empty()

        with open(filename, 'wb') as file:
            for data in response.iter_content(1024):
                downloaded_size += len(data)
                file.write(data)
                if total_size_in_bytes > 0:
                    progress_bar.progress(downloaded_size / total_size_in_bytes)

                elapsed_time = time.time() - start_time
                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                speed_text.text(f"Speed: {speed / 1024:.2f} KB/s")

        if total_size_in_bytes != 0 and downloaded_size != total_size_in_bytes:
            st.error("Error with downloading file.")
        else:
            st.success("File downloaded successfully.")

    def delete_files_in_folder(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
                
    # ultralytics
    def upgrade_ultralytics():
        ultralytics_current_version = ultralytics.__version__

        ultralytics_repo_version = requests.get(
            'https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py'
        ).content.decode('utf-8')
        ultralytics_repo_version = re.search(r"__version__\s*=\s*\"([^\"]+)", ultralytics_repo_version).group(1)

        if ultralytics_current_version != ultralytics_repo_version:
            os.system("pip install ultralytics --upgrade")
            return ultralytics_repo_version
        else:
            return ultralytics_current_version

    ultralytics_version = upgrade_ultralytics()
    ultralytics_version_text = st.empty()
    ultralytics_version_text.text(f"Ultralytics version: {ultralytics_version}")

    # pip
    def upgrade_pip():
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, check=True)
            current_version = result.stdout.split(' ')[1]
            
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--dry-run"], capture_output=True, text=True, check=True)
            latest_version = None
            for line in result.stdout.splitlines():
                if "Collecting pip" in line:
                    latest_version = line.split(' ')[-1].strip('()')
                    break
            
            if latest_version and version.parse(current_version) < version.parse(latest_version):
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
                return current_version
            else:
                return current_version
        except subprocess.CalledProcessError as e:
            print(f'pip: An error occurred: {e}')
        except Exception as e:
            print(f'pip: An unexpected error occurred: {e}')

    pip_version = upgrade_pip()
    pip_version_text = st.empty()
    pip_version_text.text(f"Pip version: {pip_version}")

    # aimbot online and offline versions
    def get_aimbot_offline_version():
        try:
            with open('./version', 'r') as file:
                lines = file.readlines()
            app, config = 0, 0
            for line in lines:
                key, value = line.strip().split('=')
                if key == "app":
                    app = value
                if key == 'config':
                    config = value
            return app, config
        except FileNotFoundError:
            print('The version file was not found, we will consider it an old version of the program.')
            return 0, 0

    def get_aimbot_online_version():
        content = requests.get('https://raw.githubusercontent.com/SunOner/sunone_aimbot/main/version').content.decode('utf-8').split('\n')
        app, config = 0, 0
        for line in content:
            key, value = line.strip().split("=")
            if key == "app":
                app = value
            if key == 'config':
                config = value
        return app, config

    aimbot_offline_version_app, aimbot_offline_version_config = get_aimbot_offline_version()
    aimbot_online_version_app, aimbot_online_version_config = get_aimbot_online_version()
    aimbot_versions_text = st.empty()
    aimbot_versions_text.text(f"Installed/Github aimbot versions: {aimbot_offline_version_app}/{aimbot_online_version_app}")

    # CUDA
    def find_cuda_path():
        cuda_paths = [path for key, value in os.environ.items() if key == "PATH" for path in value.split(";") if "CUDA" in path and "12.4" in path]
        return cuda_paths if cuda_paths else None

    cuda = find_cuda_path()
    if cuda != None:
        try:
            cuda_active = st.toggle(f"CUDA 12.4 FOUND {cuda[0]}", disabled=True, value=True)
        except IndexError:
            cuda_active = st.toggle(f"CUDA 12.4 FOUND", disabled=True, value=True)
    else:
        cuda_active = st.toggle("CUDA 12.4 NOT FOUND", disabled=True, value=False)

    def install_cuda():
        st.write("Cuda 12.4 is being downloaded, and installation will begin after downloading.")
        download_file("https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe', './cuda_12.4.0_551.61_windows.exe")
        subprocess.call(f'{os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuda_12.4.0_551.61_windows.exe")}')

    # Python version checker
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor == 11 and python_version.micro == 6:
        needed_python = st.toggle(f"Running from Python 3.11.6", disabled=True, value=True)
    else:
        needed_python = st.toggle(f"Running not from Python 3.11.6", disabled=True, value=False)

    def test_detections():
        import ultralytics
        from ultralytics import YOLO
        import cv2
        import win32gui, win32con
        cuda_support = ultralytics.utils.checks.cuda_is_available()
        if cuda_support:
            print("Cuda support True")
        else:
            print("Cuda is not supported\nTrying to reinstall torch with GPU support...")
            
        model = YOLO(f'models/{cfg.AI_model_name}', task='detect')
        cap = cv2.VideoCapture('media/tests/test_det.mp4')
        window_name = f"Model: {cfg.AI_model_name} imgsz: {cfg.ai_model_image_size}"
        cv2.namedWindow(window_name)
        debug_window_hwnd = win32gui.FindWindow(None, window_name)
        win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)
        
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                result = model(frame, stream=False, show=False, imgsz=cfg.ai_model_image_size, device=cfg.AI_device, verbose=False, conf=0.40)
                annotated_frame = result[0].plot()
                cv2.putText(annotated_frame, "TEST 1234567890", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.imshow(window_name, annotated_frame)
                if cv2.waitKey(30) & 0xFF == ord("q"):
                    break
            else:
                break

        cap.release()
        cv2.destroyAllWindows()

    def reinstall_aimbot():
        log_text = st.empty()
        log_text.text("Deleting old files...")
        try:
            delete_files_in_folder("./logic")
        except:
            pass
        try:
            delete_files_in_folder("./media")
        except:
            pass

        base_dir_files = [
            './.gitattributes', './.gitignore', './LICENSE', './README.md', './helper.py', './run.py', './requirements.txt', './launcher.py', 'window_names.txt',
        ]
        for file in base_dir_files:
            try:
                os.remove(file)
            except:
                log_text.text(f"{file} not found, continued")

        replace_config = False
        config_online_version = int(get_aimbot_online_version()[1])
        config_current_version = get_aimbot_offline_version()
        
        if config_current_version:
            config_current_version = int(config_current_version[1])
        
        log_text.text(f"Config current version: {config_current_version}\nConfig online version {config_online_version}")
        
        if config_online_version != config_current_version:
            log_text.text("Removing config with old version and installing fresh.")
            try:
                os.remove("./config.ini")
            except:
                pass
            replace_config = True
        else:
            log_text.text("Config has a fresh version. We don't touch him.")
            
        try:
            os.remove("./version")
        except:
            pass
        
        log_text.text("Downloading repo. Please wait...")
        download_file("https://github.com/SunOner/sunone_aimbot/archive/refs/heads/main.zip", "main.zip")
        log_text.text("Unpacking...")
        with zipfile.ZipFile(r"./main.zip", "r") as zip_ref:
            zip_ref.extractall("./")
        log_text.text("Deleting downloaded zip...")
        os.remove(r"./main.zip")
        
        new_dirs = ['./logic', './media', './media/tests', './docs/en', './docs/ru', './models']
        for dir in new_dirs:
            if not os.path.isdir(dir):
                os.makedirs(dir)

        temp_aimbot_files = [
            './.gitattributes', './.gitignore', './config.ini', './helper.py', 'run_helper.bat', './LICENSE', './README.md', './run.py', './requirements.txt', './version', 'window_names.txt', 
            './logic/arduino.py', './logic/capture.py', './logic/config_watcher.py', './logic/game.yaml', './logic/ghub_mouse.dll', './logic/buttons.py', './logic/overlay.py', './logic/mouse.py', './logic/visual.py', './logic/frame_parser.py', './logic/hotkeys_watcher.py',
            './media/aimbot.png', './media/cmd_admin_en.png', './media/cmd_admin_ru.png', './media/cmd_cd_path.png',
            './media/copy_explorer_path.png', './media/python_add_to_path.png', './media/cuda.png', './media/environment_variables.png',
            './media/environment_variables_path.png', './media/one.gif', './media/python.png', './media/tests/test_det.mp4',
            './docs/en/helper_en.md', './docs/en/install_guide_en.md', './docs/en/questions_en.md',
            './docs/ru/helper_ru.md', './docs/ru/install_guide_ru.md', './docs/ru/questions_ru.md',
            './models/sunxds_0.4.1.pt'
        ]

        for temp_file in temp_aimbot_files:
            try:
                if temp_file == "./sunone_aimbot-main/config.ini" and not replace_config:
                    continue
                shutil.move(f"sunone_aimbot-main/{temp_file}", temp_file)
            except:
                pass

        try:
            delete_files_in_folder("./sunone_aimbot-main")
            os.rmdir("./sunone_aimbot-main")
        except:
            pass

        os.system("streamlit run helper.py")
        quit()

    try:
        from logic.config_watcher import cfg
        import logic.buttons
    except ModuleNotFoundError:
        reinstall_aimbot()

    # Buttons
    if st.button("Update/Install Sunone Aimbot"):
        reinstall_aimbot()
        
    if st.button("Download CUDA 12.4"):
        install_cuda()

    if st.button("Install Torch"):
        if not find_cuda_path():
            st.write("Please, download and install CUDA first.")
        else:
            with st.spinner("Installing Torch"):
                os.system("pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124")
            
    if st.button("Install TensorRT"):
        if find_cuda_path():
            with st.spinner("Installing TensorRT"):
                os.system("pip install tensorrt")
        else:
            st.write("Please, download and install CUDA first.")
        
    if st.button("Test detections"):
        test_detections()

    if st.button("Run Aimbot"):
        os.system("python run.py")

with EXPORT:
    st.title("Export Helper")
    
    models = []
    for root, dirs, files in os.walk("./models"):
        for file in files:
            if file.endswith(".pt"):
                models.append(file)
                
    selected_model = st.selectbox("**Select model to export.**", models)
    
    image_size = st.radio("**Select models size**",(320, 480, 640))
    
    if st.button("Export model"):
        yolo_model = YOLO(f"./models/{selected_model}")
        with st.spinner(f"Model {selected_model} exporting..."):
            yolo_model.export(format="engine", imgsz=image_size, half=True, device=0)
            st.success("Model exported!", icon="✅")
            
with CONFIG: # TODO
    def load_config():
        config = configparser.ConfigParser()
        config.read('./config.ini')
        return config

    def save_config(config):
        config_file_path = 'config.ini'
        try:
            with open(config_file_path, 'r') as configfile:
                lines = configfile.readlines()

            with open(config_file_path, 'w') as configfile:
                current_section = None
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('[') and stripped_line.endswith(']'):
                        current_section = stripped_line[1:-1]
                        configfile.write(line)
                    elif '=' in line and not stripped_line.startswith('#') and current_section:
                        key, _ = map(str.strip, line.split('=', 1))
                        if config.has_option(current_section, key):
                            value = config.get(current_section, key)
                            configfile.write(f'{key} = {value}\n')
                        else:
                            configfile.write(line)
                    else:
                        configfile.write(line)

            st.success('Config saved successfully!')
        except Exception as e:
            st.error(f'Error writing to config file: {e}')

    config = load_config()

    st.title("Config Editor")

    # Detection window
    st.header("Detection window")
    detection_window_width = st.number_input("Detection window width:", value=config.getint('Detection window', 'detection_window_width'))
    detection_window_height = st.number_input("Detection window height:", value=config.getint('Detection window', 'detection_window_height'))
    config.set('Detection window', 'detection_window_width', str(detection_window_width))
    config.set('Detection window', 'detection_window_height', str(detection_window_height))

    # Capture Methods
    st.header("Capture Methods")
    bettercam_capture = st.checkbox("Bettercam capture:", value=config.getboolean('Capture Methods', 'Bettercam_capture'))
    bettercam_capture_fps = st.number_input("Bettercam capture FPS:", value=config.getint('Capture Methods', 'bettercam_capture_fps'))
    bettercam_monitor_id = st.number_input("Bettercam monitor ID:", value=config.getint('Capture Methods', 'bettercam_monitor_id'))
    bettercam_gpu_id = st.number_input("Bettercam GPU ID:", value=config.getint('Capture Methods', 'bettercam_gpu_id'))
    config.set('Capture Methods', 'Bettercam_capture', str(bettercam_capture))
    config.set('Capture Methods', 'bettercam_capture_fps', str(bettercam_capture_fps))
    config.set('Capture Methods', 'bettercam_monitor_id', str(bettercam_monitor_id))
    config.set('Capture Methods', 'bettercam_gpu_id', str(bettercam_gpu_id))

    obs_capture = st.checkbox("Obs capture:", value=config.getboolean('Capture Methods', 'Obs_capture'))
    obs_camera_id = st.text_input("Obs camera ID:", value=config.get('Capture Methods', 'Obs_camera_id'))
    obs_capture_fps = st.number_input("Obs capture FPS:", value=config.getint('Capture Methods', 'Obs_capture_fps'))
    config.set('Capture Methods', 'Obs_capture', str(obs_capture))
    config.set('Capture Methods', 'Obs_camera_id', obs_camera_id)
    config.set('Capture Methods', 'Obs_capture_fps', str(obs_capture_fps))

    # Aim
    st.header("Aim")
    body_y_offset = st.number_input("Body Y offset:", value=config.getfloat('Aim', 'body_y_offset'))
    hideout_targets = st.checkbox("Hideout targets:", value=config.getboolean('Aim', 'hideout_targets'))
    disable_headshot = st.checkbox("Disable headshot:", value=config.getboolean('Aim', 'disable_headshot'))
    disable_prediction = st.checkbox("Disable prediction:", value=config.getboolean('Aim', 'disable_prediction'))
    config.set('Aim', 'body_y_offset', str(body_y_offset))
    config.set('Aim', 'hideout_targets', str(hideout_targets))
    config.set('Aim', 'disable_headshot', str(disable_headshot))
    config.set('Aim', 'disable_prediction', str(disable_prediction))

    # Hotkeys
    st.header("Hotkeys")
    hotkey_targeting = st.text_input("Hotkey targeting:", value=config.get('Hotkeys', 'hotkey_targeting'))
    hotkey_exit = st.text_input("Hotkey exit:", value=config.get('Hotkeys', 'hotkey_exit'))
    hotkey_pause = st.text_input("Hotkey pause:", value=config.get('Hotkeys', 'hotkey_pause'))
    hotkey_reload_config = st.text_input("Hotkey reload config:", value=config.get('Hotkeys', 'hotkey_reload_config'))
    config.set('Hotkeys', 'hotkey_targeting', hotkey_targeting)
    config.set('Hotkeys', 'hotkey_exit', hotkey_exit)
    config.set('Hotkeys', 'hotkey_pause', hotkey_pause)
    config.set('Hotkeys', 'hotkey_reload_config', hotkey_reload_config)

    # Mouse
    st.header("Mouse")
    mouse_dpi = st.number_input("Mouse DPI:", value=config.getint('Mouse', 'mouse_dpi'))
    mouse_sensitivity = st.number_input("Mouse sensitivity:", value=config.getfloat('Mouse', 'mouse_sensitivity'))
    mouse_fov_width = st.number_input("Mouse FOV width:", value=config.getint('Mouse', 'mouse_fov_width'))
    mouse_fov_height = st.number_input("Mouse FOV height:", value=config.getint('Mouse', 'mouse_fov_height'))
    mouse_lock_target = st.checkbox("Mouse lock target:", value=config.getboolean('Mouse', 'mouse_lock_target'))
    mouse_auto_aim = st.checkbox("Mouse auto aim:", value=config.getboolean('Mouse', 'mouse_auto_aim'))
    mouse_ghub = st.checkbox("Mouse GHUB:", value=config.getboolean('Mouse', 'mouse_ghub'))
    config.set('Mouse', 'mouse_dpi', str(mouse_dpi))
    config.set('Mouse', 'mouse_sensitivity', str(mouse_sensitivity))
    config.set('Mouse', 'mouse_fov_width', str(mouse_fov_width))
    config.set('Mouse', 'mouse_fov_height', str(mouse_fov_height))
    config.set('Mouse', 'mouse_lock_target', str(mouse_lock_target))
    config.set('Mouse', 'mouse_auto_aim', str(mouse_auto_aim))
    config.set('Mouse', 'mouse_ghub', str(mouse_ghub))

    # Shooting
    st.header("Shooting")
    auto_shoot = st.checkbox("Auto shoot:", value=config.getboolean('Shooting', 'auto_shoot'))
    triggerbot = st.checkbox("Triggerbot:", value=config.getboolean('Shooting', 'triggerbot'))
    force_click = st.checkbox("Force click:", value=config.getboolean('Shooting', 'force_click'))
    bScope_multiplier = st.number_input("bScope multiplier:", value=config.getfloat('Shooting', 'bScope_multiplier'))
    config.set('Shooting', 'auto_shoot', str(auto_shoot))
    config.set('Shooting', 'triggerbot', str(triggerbot))
    config.set('Shooting', 'force_click', str(force_click))
    config.set('Shooting', 'bScope_multiplier', str(bScope_multiplier))

    # Arduino
    st.header("Arduino")
    arduino_move = st.checkbox("Arduino move:", value=config.getboolean('Arduino', 'arduino_move'))
    arduino_shoot = st.checkbox("Arduino shoot:", value=config.getboolean('Arduino', 'arduino_shoot'))
    arduino_port = st.text_input("Arduino port:", value=config.get('Arduino', 'arduino_port'))
    arduino_baudrate = st.number_input("Arduino baudrate:", value=config.getint('Arduino', 'arduino_baudrate'))
    arduino_16_bit_mouse = st.checkbox("Arduino 16 bit mouse:", value=config.getboolean('Arduino', 'arduino_16_bit_mouse'))
    config.set('Arduino', 'arduino_move', str(arduino_move))
    config.set('Arduino', 'arduino_shoot', str(arduino_shoot))
    config.set('Arduino', 'arduino_port', arduino_port)
    config.set('Arduino', 'arduino_baudrate', str(arduino_baudrate))
    config.set('Arduino', 'arduino_16_bit_mouse', str(arduino_16_bit_mouse))

    # AI
    st.header("AI")
    AI_model_name = st.text_input("AI model name:", value=config.get('AI', 'AI_model_name'))
    AI_model_image_size = st.number_input("AI model image size:", value=config.getint('AI', 'AI_model_image_size'))
    AI_conf = st.number_input("AI confidence:", value=config.getfloat('AI', 'AI_conf'))
    AI_device = st.text_input("AI device:", value=config.get('AI', 'AI_device'))
    AI_enable_AMD = st.checkbox("AI enable AMD:", value=config.getboolean('AI', 'AI_enable_AMD'))
    AI_mouse_net = st.checkbox("AI mouse net:", value=config.getboolean('AI', 'AI_mouse_net'))
    config.set('AI', 'AI_model_name', AI_model_name)
    config.set('AI', 'AI_model_image_size', str(AI_model_image_size))
    config.set('AI', 'AI_conf', str(AI_conf))
    config.set('AI', 'AI_device', AI_device)
    config.set('AI', 'AI_enable_AMD', str(AI_enable_AMD))
    config.set('AI', 'AI_mouse_net', str(AI_mouse_net))

    # Overlay
    st.header("Overlay")
    show_overlay = st.checkbox("Show overlay:", value=config.getboolean('overlay', 'show_overlay'))
    overlay_show_borders = st.checkbox("Overlay show borders:", value=config.getboolean('overlay', 'overlay_show_borders'))
    overlay_show_boxes = st.checkbox("Overlay show boxes:", value=config.getboolean('overlay', 'overlay_show_boxes'))
    overlay_show_target_line = st.checkbox("Overlay show target line:", value=config.getboolean('overlay', 'overlay_show_target_line'))
    overlay_show_target_prediction_line = st.checkbox("Overlay show target prediction line:", value=config.getboolean('overlay', 'overlay_show_target_prediction_line'))
    overlay_show_labels = st.checkbox("Overlay show labels:", value=config.getboolean('overlay', 'overlay_show_labels'))
    overlay_show_conf = st.checkbox("Overlay show confidence:", value=config.getboolean('overlay', 'overlay_show_conf'))
    config.set('overlay', 'show_overlay', str(show_overlay))
    config.set('overlay', 'overlay_show_borders', str(overlay_show_borders))
    config.set('overlay', 'overlay_show_boxes', str(overlay_show_boxes))
    config.set('overlay', 'overlay_show_target_line', str(overlay_show_target_line))
    config.set('overlay', 'overlay_show_target_prediction_line', str(overlay_show_target_prediction_line))
    config.set('overlay', 'overlay_show_labels', str(overlay_show_labels))
    config.set('overlay', 'overlay_show_conf', str(overlay_show_conf))

    # Debug window
    st.header("Debug window")
    show_window = st.checkbox("Show window:", value=config.getboolean('Debug window', 'show_window'))
    show_detection_speed = st.checkbox("Show detection speed:", value=config.getboolean('Debug window', 'show_detection_speed'))
    show_window_fps = st.checkbox("Show window FPS:", value=config.getboolean('Debug window', 'show_window_fps'))
    show_boxes = st.checkbox("Show boxes:", value=config.getboolean('Debug window', 'show_boxes'))
    show_labels = st.checkbox("Show labels:", value=config.getboolean('Debug window', 'show_labels'))
    show_conf = st.checkbox("Show confidence:", value=config.getboolean('Debug window', 'show_conf'))
    show_target_line = st.checkbox("Show target line:", value=config.getboolean('Debug window', 'show_target_line'))
    show_target_prediction_line = st.checkbox("Show target prediction line:", value=config.getboolean('Debug window', 'show_target_prediction_line'))
    show_bScope_box = st.checkbox("Show bScope box:", value=config.getboolean('Debug window', 'show_bScope_box'))
    show_history_points = st.checkbox("Show history points:", value=config.getboolean('Debug window', 'show_history_points'))
    debug_window_always_on_top = st.checkbox("Debug window always on top:", value=config.getboolean('Debug window', 'debug_window_always_on_top'))
    spawn_window_pos_x = st.number_input("Spawn window position X:", value=config.getint('Debug window', 'spawn_window_pos_x'))
    spawn_window_pos_y = st.number_input("Spawn window position Y:", value=config.getint('Debug window', 'spawn_window_pos_y'))
    debug_window_scale_percent = st.number_input("Debug window scale percent:", value=config.getint('Debug window', 'debug_window_scale_percent'))
    config.set('Debug window', 'show_window', str(show_window))
    config.set('Debug window', 'show_detection_speed', str(show_detection_speed))
    config.set('Debug window', 'show_window_fps', str(show_window_fps))
    config.set('Debug window', 'show_boxes', str(show_boxes))
    config.set('Debug window', 'show_labels', str(show_labels))
    config.set('Debug window', 'show_conf', str(show_conf))
    config.set('Debug window', 'show_target_line', str(show_target_line))
    config.set('Debug window', 'show_target_prediction_line', str(show_target_prediction_line))
    config.set('Debug window', 'show_bScope_box', str(show_bScope_box))
    config.set('Debug window', 'show_history_points', str(show_history_points))
    config.set('Debug window', 'debug_window_always_on_top', str(debug_window_always_on_top))
    config.set('Debug window', 'spawn_window_pos_x', str(spawn_window_pos_x))
    config.set('Debug window', 'spawn_window_pos_y', str(spawn_window_pos_y))
    config.set('Debug window', 'debug_window_scale_percent', str(debug_window_scale_percent))

    if st.button('Save Config'):
        save_config(config)