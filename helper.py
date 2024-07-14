import os
import subprocess
import tempfile
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
    import numpy as np
except ModuleNotFoundError:
    os.system("pip install -r requirements.txt")
    os.system("streamlit run helper.py")
    quit()

def install_cuda():
        st.write("Cuda 12.4 is being downloaded, and installation will begin after downloading.")
        download_file("https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe", "./cuda_12.4.0_551.61_windows.exe")
        subprocess.call(f'{os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuda_12.4.0_551.61_windows.exe")}')
        
def delete_files_in_folder(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except: pass
                
def find_cuda_path():
    cuda_paths = [path for key, value in os.environ.items() if key == "PATH" for path in value.split(";") if "CUDA" in path and "12.4" in path]
    return cuda_paths if cuda_paths else None
    
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
            st.info("The version file was not found, we will consider it an old version of the program.")
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

def upgrade_pip():
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, check=True, timeout=10)
        current_version_match = re.search(r'pip (\d+\.\d+\.\d+)', result.stdout)
        if not current_version_match:
            print("Unable to determine current pip version")
            return None
        current_version = current_version_match.group(1)
        
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--dry-run"], capture_output=True, text=True, check=True, timeout=30)
        
        new_version_match = re.search(r'pip-(\d+\.\d+\.\d+)', result.stdout)
        
        if new_version_match:
            latest_version = new_version_match.group(1)
            if version.parse(current_version) < version.parse(latest_version):
                st.info(f"Upgrading pip from {current_version} to {latest_version}")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True, timeout=60)
                
                result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, check=True, timeout=10)
                updated_version_match = re.search(r'pip (\d+\.\d+\.\d+)', result.stdout)
                if updated_version_match:
                    updated_version = updated_version_match.group(1)
                    return updated_version
                else:
                    return current_version
            else:
                return current_version
        else:
            return current_version
    
    except subprocess.TimeoutExpired:
        st.error("Pip upgrade process timed out")
        return current_version
    except subprocess.CalledProcessError as e:
        st.error(f'pip: An error occurred: {e}')
        return current_version
    except Exception as e:
        st.error(f'pip: An unexpected error occurred: {e}')
        return current_version
            
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
        
if 'ultralytics_version' not in st.session_state:
    with st.spinner('Checking for ultralytics updates...'):
        st.session_state.ultralytics_version = upgrade_ultralytics()

if 'pip_version' not in st.session_state:
    with st.spinner('Checking for pip updates...'):
        st.session_state.pip_version = upgrade_pip()

if 'aimbot_versions' not in st.session_state:
    with st.spinner('Checking Aimbot versions...'):
        st.session_state.aimbot_versions = get_aimbot_offline_version(), get_aimbot_online_version()

if 'cuda' not in st.session_state:
    with st.spinner('Searching CUDA...'):
        st.session_state.cuda = find_cuda_path()

if 'python_version' not in st.session_state:
    with st.spinner("Checking Python version..."):
        st.session_state.python_version = sys.version_info

if 'torch_gpu' not in st.session_state:
    with st.spinner("Checking Torch GPU support..."):
        st.session_state.torch_gpu_support = torch.cuda.is_available()
        
HELPER, EXPORT, CONFIG, TRAIN, TESTS = st.tabs(["HELPER", "EXPORT", "CONFIG", "TRAIN", "TESTS"])

with HELPER:
    st.title("Helper")

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
                
    ultralytics_version_text = st.empty()
    ultralytics_version_text.text(f"Ultralytics version: {st.session_state.ultralytics_version}")

    pip_version_text = st.empty()
    pip_version_text.text(f"Pip version: {st.session_state.pip_version}")

    aimbot_versions_text = st.empty()
    aimbot_versions_text.text(f"Installed/Github aimbot versions: {st.session_state.aimbot_versions[0][0]}/{st.session_state.aimbot_versions[1][0]}")

    if st.session_state.cuda is not None:
        cuda_active = st.toggle(f"CUDA 12.4 FOUND", disabled=True, value=True, key="cuda_active_toggle")
    else:
        cuda_active = st.toggle("CUDA 12.4 NOT FOUND", disabled=True, value=False, key="cuda_active_toggle")

    if st.session_state.python_version.major == 3 and st.session_state.python_version.minor == 11 and st.session_state.python_version.micro == 6:
        needed_python = st.toggle(f"Running from Python 3.11.6", disabled=True, value=True, key="needed_python_toggle")
    else:
        needed_python = st.toggle(f"Running not from Python 3.11.6", disabled=True, value=False, key="needed_python_toggle")

    torch_gpu_support = st.toggle("Torch with GPU", value=st.session_state.torch_gpu_support, disabled=True, key="torch_gpu_support_toggle")

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
            # main
            './.gitattributes', './.gitignore', './config.ini', './helper.py', 'run_helper.bat', './LICENSE', './README.md', './run.py', './requirements.txt', './version', 'window_names.txt',
             # logic
            './logic/arduino.py', './logic/capture.py', './logic/config_watcher.py', './logic/game.yaml', './logic/ghub_mouse.dll',
            './logic/buttons.py', './logic/overlay.py', './logic/mouse.py', './logic/visual.py', './logic/frame_parser.py', './logic/hotkeys_watcher.py',
            './logic/shooting.py',
            # media
            './media/aimbot.png', './media/cuda.png', './media/one.gif', './media/python.png', './media/tests/test_det.mp4',
            # docs
            './docs/en/helper_en.md', './docs/en/install_guide_en.md', './docs/en/questions_en.md',
            './docs/ru/helper_ru.md', './docs/ru/install_guide_ru.md', './docs/ru/questions_ru.md',
            # models
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
    if st.button("Update/Install Sunone Aimbot", key="reinstall_aimbot_button"):
        st.text("Are you sure?")
        if st.button("Yes", key="reinstall_aimbot_button_yes"):
            reinstall_aimbot()
        if st.button("No", key="reinstall_aimbot_button_no"):
            pass
        
    if st.button("Download CUDA 12.4", key="Download_cuda_button"):
        install_cuda()

    if st.button("Install Torch", key="install_torch_button"):
        if not find_cuda_path():
            st.error("Please, download and install CUDA first.")
        else:
            with st.spinner("Installing Torch"):
                os.system("pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124")
            
    if st.button("Install TensorRT", key="install_tensorrt_button"):
        if find_cuda_path():
            with st.spinner("Installing TensorRT"):
                os.system("pip install tensorrt")
        else:
            st.error("Please, download and install CUDA first.")

    if st.button("Run Aimbot", key="run_aimbot_button"):
        os.system("python run.py")

with EXPORT:
    st.title("Model exporter")
    
    models = []
    for root, dirs, files in os.walk("./models"):
        for file in files:
            if file.endswith(".pt"):
                models.append(file)
                
    selected_model = st.selectbox("**Select model to export.**", models, key="export_selected_model_selectbox")
    
    image_size = st.radio("**Select model size**",(320, 480, 640), help="The size of the model image must be correct.", key="export_image_size_radio")
    
    if st.button("Export model", key="export_export_model_button"):
        yolo_model = YOLO(f"./models/{selected_model}")
        
        with st.spinner(f"Model {selected_model} exporting..."):
            yolo_model.export(format="engine", imgsz=image_size, half=True, device=0)
            st.success("Model exported!", icon="✅")
            
with CONFIG:
    st.title("Config Editor")
    
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

    # Detection window
    st.header("Detection window")
    detection_window_width = st.number_input("Detection window width", value=config.getint('Detection window', 'detection_window_width'))
    detection_window_height = st.number_input("Detection window height", value=config.getint('Detection window', 'detection_window_height'))
    config.set('Detection window', 'detection_window_width', str(detection_window_width))
    config.set('Detection window', 'detection_window_height', str(detection_window_height))

    # Capture Methods
    st.header("Capture Methods")
    selected_capture_method = st.radio(label="Capture Method", options=["Bettercam capture", "OBS"])
    
    if selected_capture_method == "Bettercam capture":        
        bettercam_capture_fps = st.number_input("Bettercam capture FPS", value=config.getint('Capture Methods', 'bettercam_capture_fps'))
        bettercam_monitor_id = st.number_input("Bettercam monitor ID", value=config.getint('Capture Methods', 'bettercam_monitor_id'))
        bettercam_gpu_id = st.number_input("Bettercam GPU ID", value=config.getint('Capture Methods', 'bettercam_gpu_id'))
        config.set('Capture Methods', 'Bettercam_capture', "True")
        config.set('Capture Methods', 'Obs_capture', "False")
        config.set('Capture Methods', 'bettercam_capture_fps', str(bettercam_capture_fps))
        config.set('Capture Methods', 'bettercam_monitor_id', str(bettercam_monitor_id))
        config.set('Capture Methods', 'bettercam_gpu_id', str(bettercam_gpu_id))
    else:
        obs_camera_id = st.selectbox(label="Obs camera ID", options=["auto", "0","1","2","3","4","5","6","7","8","9","10"], index=0)
        obs_capture_fps = st.number_input("Obs capture FPS", value=config.getint('Capture Methods', 'Obs_capture_fps'))
        config.set('Capture Methods', 'Bettercam_capture', "False")
        config.set('Capture Methods', 'Obs_capture', "True")
        config.set('Capture Methods', 'Obs_camera_id', obs_camera_id)
        config.set('Capture Methods', 'Obs_capture_fps', str(obs_capture_fps))

    # Aim
    st.header("Aim")
    body_y_offset = st.slider(label="Body Y offset", min_value=-0.99, max_value=0.99, value=config.getfloat('Aim', 'body_y_offset'))
    hideout_targets = st.checkbox("Hideout targets", value=config.getboolean('Aim', 'hideout_targets'))
    disable_headshot = st.checkbox("Disable headshot", value=config.getboolean('Aim', 'disable_headshot'))
    disable_prediction = st.checkbox("Disable prediction", value=config.getboolean('Aim', 'disable_prediction'))
    prediction_interval = st.number_input("Prediction interval", value=config.getfloat('Aim', 'prediction_interval'), format="%.1f", min_value=0.1, max_value=5.0, step=0.1)
    third_person = st.checkbox("Third person mode", value=config.getboolean('Aim', 'third_person'))
    config.set('Aim', 'body_y_offset', str(body_y_offset))
    config.set('Aim', 'hideout_targets', str(hideout_targets))
    config.set('Aim', 'disable_headshot', str(disable_headshot))
    config.set('Aim', 'disable_prediction', str(disable_prediction))
    config.set('Aim', 'prediction_interval', str(prediction_interval))
    config.set('Aim', 'third_person', str(third_person))

    # Hotkeys
    st.header("Hotkeys")
    hotkey_options = []
    for i in logic.buttons.Buttons.KEY_CODES:
        hotkey_options.append(i)
    hotkey_targeting = st.selectbox(label="Hotkey targeting", options=hotkey_options, index=hotkey_options.index(config.get('Hotkeys', 'hotkey_targeting')))
    hotkey_exit = st.selectbox(label="Hotkey exit", options=hotkey_options, index=hotkey_options.index(config.get('Hotkeys', 'hotkey_exit')))
    hotkey_pause = st.selectbox(label="Hotkey pause",options=hotkey_options,  index=hotkey_options.index(config.get('Hotkeys', 'hotkey_pause')))
    hotkey_reload_config = st.selectbox(label="Hotkey reload config",options=hotkey_options,  index=hotkey_options.index(config.get('Hotkeys', 'hotkey_reload_config')))
    config.set('Hotkeys', 'hotkey_targeting', hotkey_targeting)
    config.set('Hotkeys', 'hotkey_exit', hotkey_exit)
    config.set('Hotkeys', 'hotkey_pause', hotkey_pause)
    config.set('Hotkeys', 'hotkey_reload_config', hotkey_reload_config)

    # Mouse
    st.header("Mouse")
    mouse_dpi = st.number_input("Mouse DPI", min_value=100, step=100, value=config.getint('Mouse', 'mouse_dpi'))
    mouse_sensitivity = st.number_input("Mouse sensitivity", min_value=0.1, value=config.getfloat('Mouse', 'mouse_sensitivity'))
    mouse_fov_width = st.number_input("Mouse FOV width", value=config.getint('Mouse', 'mouse_fov_width'))
    mouse_fov_height = st.number_input("Mouse FOV height", value=config.getint('Mouse', 'mouse_fov_height'))
    mouse_lock_target = st.checkbox("Mouse lock target", value=config.getboolean('Mouse', 'mouse_lock_target'))
    mouse_auto_aim = st.checkbox("Mouse auto aim", value=config.getboolean('Mouse', 'mouse_auto_aim'))
    mouse_ghub = st.checkbox("Mouse GHUB", value=config.getboolean('Mouse', 'mouse_ghub'))
    config.set('Mouse', 'mouse_dpi', str(mouse_dpi))
    config.set('Mouse', 'mouse_sensitivity', str(mouse_sensitivity))
    config.set('Mouse', 'mouse_fov_width', str(mouse_fov_width))
    config.set('Mouse', 'mouse_fov_height', str(mouse_fov_height))
    config.set('Mouse', 'mouse_lock_target', str(mouse_lock_target))
    config.set('Mouse', 'mouse_auto_aim', str(mouse_auto_aim))
    config.set('Mouse', 'mouse_ghub', str(mouse_ghub))

    # Shooting
    st.header("Shooting")
    auto_shoot = st.checkbox("Auto shoot", value=config.getboolean('Shooting', 'auto_shoot'))
    triggerbot = st.checkbox("Triggerbot", value=config.getboolean('Shooting', 'triggerbot'))
    force_click = st.checkbox("Force click", value=config.getboolean('Shooting', 'force_click'))
    bScope_multiplier = st.number_input("bScope multiplier", step=.10, value=config.getfloat('Shooting', 'bScope_multiplier'))
    config.set('Shooting', 'auto_shoot', str(auto_shoot))
    config.set('Shooting', 'triggerbot', str(triggerbot))
    config.set('Shooting', 'force_click', str(force_click))
    config.set('Shooting', 'bScope_multiplier', str(bScope_multiplier))

    # Arduino
    st.header("Arduino")
    arduino_move = st.checkbox("Arduino move", value=config.getboolean('Arduino', 'arduino_move'))
    arduino_shoot = st.checkbox("Arduino shoot", value=config.getboolean('Arduino', 'arduino_shoot'))
    if arduino_move or arduino_shoot:
        arduino_port = st.text_input("Arduino port", value=config.get('Arduino', 'arduino_port'))
        
        baudrates = [2400,
                     4800,
                     9600,
                     19200,
                     31250,
                     38400,
                     57600,
                     74880,
                     115200]
        arduino_baudrate = st.selectbox(label="Arduino baudrate", options=baudrates, index=baudrates.index(config.getint('Arduino', 'arduino_baudrate')))
        
        arduino_16_bit_mouse = st.checkbox("Arduino 16 bit mouse", value=config.getboolean('Arduino', 'arduino_16_bit_mouse'))
        config.set('Arduino', 'arduino_move', str(arduino_move))
        config.set('Arduino', 'arduino_shoot', str(arduino_shoot))
        config.set('Arduino', 'arduino_port', arduino_port)
        config.set('Arduino', 'arduino_baudrate', str(arduino_baudrate))
        config.set('Arduino', 'arduino_16_bit_mouse', str(arduino_16_bit_mouse))

    # AI
    st.header("AI")
    
    models = []
    for root, dirs, files in os.walk("./models"):
        for file in files:
            if file.endswith(".pt") or file.endswith(".engine"):
                models.append(file)
    
    AI_model_name = st.selectbox(label="AI model", options=models)
    
    imgsz = [320, 480, 640]
    AI_model_image_size = st.selectbox(label="AI model image size", options=imgsz, index=imgsz.index(config.getint('AI', 'AI_model_image_size')))
    
    AI_conf = st.slider("AI confidence", min_value=0.01, max_value=0.99, value=config.getfloat('AI', 'AI_conf'))
    
    devices = ["cpu", "0", "1", "2", "3", "4", "5"]
    AI_device = st.selectbox(label="AI device", options=devices, index=devices.index(config.get('AI', 'AI_device')))
    AI_enable_AMD = st.checkbox("AI enable AMD", value=config.getboolean('AI', 'AI_enable_AMD'))
    AI_mouse_net = st.checkbox("AI mouse net", value=config.getboolean('AI', 'AI_mouse_net'))
    config.set('AI', 'AI_model_name', AI_model_name)
    config.set('AI', 'AI_model_image_size', str(AI_model_image_size))
    config.set('AI', 'AI_conf', str(AI_conf))
    config.set('AI', 'AI_device', AI_device)
    config.set('AI', 'AI_enable_AMD', str(AI_enable_AMD))
    config.set('AI', 'AI_mouse_net', str(AI_mouse_net))

    # Overlay
    st.header("Overlay")
    show_overlay = st.toggle("Show overlay", value=config.getboolean('overlay', 'show_overlay'))
    if show_overlay:
        overlay_show_borders = st.checkbox("Overlay show borders", value=config.getboolean('overlay', 'overlay_show_borders'))
        overlay_show_boxes = st.checkbox("Overlay show boxes", value=config.getboolean('overlay', 'overlay_show_boxes'))
        overlay_show_target_line = st.checkbox("Overlay show target line", value=config.getboolean('overlay', 'overlay_show_target_line'))
        overlay_show_target_prediction_line = st.checkbox("Overlay show target prediction line", value=config.getboolean('overlay', 'overlay_show_target_prediction_line'))
        overlay_show_labels = st.checkbox("Overlay show labels", value=config.getboolean('overlay', 'overlay_show_labels'))
        overlay_show_conf = st.checkbox("Overlay show confidence", value=config.getboolean('overlay', 'overlay_show_conf'))
        config.set('overlay', 'show_overlay', "True")
        config.set('overlay', 'overlay_show_borders', str(overlay_show_borders))
        config.set('overlay', 'overlay_show_boxes', str(overlay_show_boxes))
        config.set('overlay', 'overlay_show_target_line', str(overlay_show_target_line))
        config.set('overlay', 'overlay_show_target_prediction_line', str(overlay_show_target_prediction_line))
        config.set('overlay', 'overlay_show_labels', str(overlay_show_labels))
        config.set('overlay', 'overlay_show_conf', str(overlay_show_conf))
    else:
        config.set('overlay', 'show_overlay', "False")

    # Debug window
    st.header("Debug window")
    show_window = st.toggle("Show debug window", value=config.getboolean('Debug window', 'show_window'))
    if show_window:
        show_detection_speed = st.checkbox("Show detection speed", value=config.getboolean('Debug window', 'show_detection_speed'))
        show_window_fps = st.checkbox("Show window FPS", value=config.getboolean('Debug window', 'show_window_fps'))
        show_boxes = st.checkbox("Show boxes", value=config.getboolean('Debug window', 'show_boxes'))
        show_labels = st.checkbox("Show labels", value=config.getboolean('Debug window', 'show_labels'))
        show_conf = st.checkbox("Show confidence", value=config.getboolean('Debug window', 'show_conf'))
        show_target_line = st.checkbox("Show target line", value=config.getboolean('Debug window', 'show_target_line'))
        show_target_prediction_line = st.checkbox("Show target prediction line", value=config.getboolean('Debug window', 'show_target_prediction_line'))
        show_bScope_box = st.checkbox("Show bScope box", value=config.getboolean('Debug window', 'show_bScope_box'))
        show_history_points = st.checkbox("Show history points", value=config.getboolean('Debug window', 'show_history_points'))
        debug_window_always_on_top = st.checkbox("Debug window always on top", value=config.getboolean('Debug window', 'debug_window_always_on_top'))
        spawn_window_pos_x = st.number_input("Spawn window position X", value=config.getint('Debug window', 'spawn_window_pos_x'))
        spawn_window_pos_y = st.number_input("Spawn window position Y", value=config.getint('Debug window', 'spawn_window_pos_y'))
        debug_window_scale_percent = st.number_input("Debug window scale percent:", value=config.getint('Debug window', 'debug_window_scale_percent'))
        config.set('Debug window', 'show_window', "True")
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
    else:
        config.set('Debug window', 'show_window', "False")

    if st.button('Save Config'):
        save_config(config)

with TRAIN:
    st.title("Train model")
    resume = False
    
    # model selection
    pretrained_models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov10n.pt", "yolov10s.pt", "yolov10m.pt"]
    
    user_trained_models = st.checkbox(label="Use user pretrained models", value=False)
    if user_trained_models:
        last_pt_files = []
        root_folder = r'runs\detect'

        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file == 'last.pt':
                    last_pt_files.append(os.path.join(root, file))
                    
        selected_model_path = st.selectbox(label="Select model", options=last_pt_files, key="TRAIN_ai_model")
        resume = st.checkbox(label="Resume training", value=False)
    else:
        selected_model_path = st.selectbox(label="Select model", options=pretrained_models, index=4, key="TRAIN_ai_model")
    
    if not resume:
        # data yaml
        data_yaml = st.text_input(label="Path to the dataset configuration file", value="logic/game.yaml")
        
        # epochs
        epochs = st.number_input(label="Epochs", value=80, format="%u", min_value=10, step=10)
        
        # image size
        img_size = st.number_input(label="Image size", value=640, format="%u", min_value=120, max_value=1280, step=10)
        
        # cache
        use_cache = st.checkbox(label="Enables caching of dataset images in memory", value=False)
        
        augment = st.checkbox(label="Use augmentation", value=True)
        
        if augment: #TODO Add more settings
            augment_degrees = st.number_input(label="Degrees", format="%u", value=5, min_value=-180, max_value=180, step=5)
            augment_flipud = st.number_input(label="Flipud", format="%.1f", value=0.2, min_value=0.0, max_value=1.0, step=0.1)
    
    # device
    input_devices = ["cpu", "0", "1", "2", "3", "4", "5"]
    train_device = st.selectbox(label="Specifies the computational device for training",
                                options=input_devices,
                                index=1,
                                help="cpu - Train on processor, 0-5 GPU ID for training.")
    if train_device != "cpu":
        train_device = int(train_device)
    
    # batch size
    batch_size_options = ["auto", "4", "8", "16", "32", "64", "128", "256"]
    batch_size = st.selectbox(label="Batch size",
                            options=batch_size_options,
                            index=0)
    if batch_size == "auto":
        batch_size = "-1"
    batch_size = int(batch_size)
        
    # WANDB
    wandb = st.checkbox(label="Force disable WANDB logger", value=True)
    if wandb:
        os.environ['WANDB_DISABLED'] = 'true'
    else:
        os.environ['WANDB_DISABLED'] = 'false'
    
    # START TRAIN
    if st.button(label="Start"):
        with st.spinner("Train in process, check terminal window."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_script:
                # for multiprocessing "if __name__ == '__main__':" required
                script_content = f"""
if __name__ == '__main__':
    from ultralytics import YOLO
    yolo_model = YOLO(r'{selected_model_path}')
    yolo_model.train(
                    device={train_device},
                    batch={batch_size},
                    resume={resume}
                """
                
                if not resume:
                    script_content += f""",
                    data='{data_yaml}',
                    epochs={epochs},
                    imgsz={img_size},
                    cache={use_cache},
                    augment={augment},
                    degrees={augment_degrees},
                    flipud={augment_flipud}
                    """
                
                script_content += "\n    )"
                
                temp_script.write(script_content.encode('utf-8'))
                temp_script_path = temp_script.name
            
            if os.name == 'nt':
                os.system(f'start cmd /k python {temp_script_path}')
            else:
                os.system(f'xterm -e python {temp_script_path}')

            st.success("Training started in a new terminal window.")
    
    with TESTS:
        def test_detections(input_model, source_method="Default", video_source=None, TOPMOST=True, model_image_size = None, input_device = 0, input_delay = 30, resize_factor = 100, ai_conf = 0.20):
            if input_model is None:
                return ("error", "Model not selected")
            
            # CUDA GPU RETURN
            cuda_support = st.session_state.torch_gpu_support
            if not cuda_support:
                return ("error", "Cuda is not supported")
            
            # Apply video source
            if source_method == "Default":
                video_source = "media/tests/test_det.mp4"
            elif source_method == "Input file":
                video_source = video_source.getvalue()
                
                with open("uploaded_video.mp4", "wb") as f:
                    f.write(video_source)
                    
                video_source = "uploaded_video.mp4"
            
            cap = cv2.VideoCapture(video_source)
            
            if not cap.isOpened():
                st.error("Error: Could not open video.")
                return
            
            window_name = "Detections test"
            cv2.namedWindow(window_name)
            
            if TOPMOST:
                debug_window_hwnd = win32gui.FindWindow(None, window_name)
                win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)
            
            model = YOLO(f'models/{input_model}', task='detect')
            
            while cap.isOpened():
                success, frame = cap.read()
                if success:
                    result = model(frame, stream=False, show=False, imgsz=model_image_size, device=input_device, verbose=False, conf=ai_conf)
                    
                    annotated_frame = result[0].plot()
                    
                    cv2.putText(annotated_frame, "When life gives you lemons, don't make lemonade.", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                    
                    frame_height, frame_width = frame.shape[:2]
                    height = int(frame_height * resize_factor / 100)
                    width = int(frame_width * resize_factor / 100)
                    dim = (width, height)
                    cv2.resizeWindow(window_name, dim)
                    resised = cv2.resize(annotated_frame, dim, cv2.INTER_NEAREST)
                    cv2.imshow(window_name, resised)
                    if cv2.waitKey(input_delay) & 0xFF == ord("q"):
                        break
                else:
                    break

            cap.release()
            cv2.destroyAllWindows()
            
            if source_method == "Input file":
                try:
                    os.remove("./uploaded_video.mp4")
                except: pass
                
            del model

        st.title("Tests")

        models = []
        for root, dirs, files in os.walk("./models"):
            for file in files:
                if file.endswith(".pt") or file.endswith(".engine"):
                    models.append(file)

        # SELECT MODEL
        ai_model = st.selectbox(label="AI Model", options=models, key="TESTS_ai_model_selectbox", help="Put model to './models' path.")

        # SELECT MODEL IMAGE SIZE
        model_image_sizes = [320, 480, 640]
        model_size = st.selectbox(label="AI Model image size", options=model_image_sizes, key="TESTS_model_size_selectbox", index=2)
        
        # VIDEO SOURCE
        methods = ["Default", "Input file"]
        video_source_method = st.selectbox(label="Select video input method", options=methods, index=0, key="TESTS_video_source_method_selectbox")

        # TOPMOST
        TOPMOST = st.toggle(label="Test window on top", value=True)
        
        # DEVICE
        test_devices = ["cpu", "0", "1", "2", "3", "4", "5"]
        device = st.selectbox(label="Device", options=test_devices, index=1)
        if device != "cpu":
            device = int(device)
        
        # DELAY
        cv2_delay = st.number_input(label="CV2 frame wait delay", min_value=1, max_value=120, step=1, format="%u", value=30, key="TESTS_cv2_delay_number_input")
        
        # RESIZE
        cv2_resize = st.number_input(label="Resize test window", min_value=10, max_value=100, value=80, step=1, format="%u", key="ESTS_cv2_resize_number_input")
        
        # DETECTION CONF
        ai_conf = st.number_input(label="Minimum confidence threshold", min_value=0.01, max_value=0.99, step=0.01, format="%.2f", value=0.20)
        
        input_video = None
        if video_source_method == "Input file":
            video_source_input_file = st.file_uploader(label="Import video file", accept_multiple_files=False, type=(["mp4"]), key="TESTS_input_file_video_source_input_file")
            input_video = video_source_input_file

        if st.button(label="Test detections", key="TESTS_text_detections_button"):
            if video_source_method in methods:
                if input_video == None and video_source_method == "Input file":
                    st.error("Video source not found.")
                else:
                    test_detections(input_model=ai_model,
                                    source_method=video_source_method,
                                    video_source=input_video,
                                    model_image_size=model_size,
                                    TOPMOST=TOPMOST,
                                    input_delay=cv2_delay,
                                    input_device=device,
                                    resize_factor=cv2_resize,
                                    ai_conf=ai_conf)
            else:
                st.error("Select correct video input method.")