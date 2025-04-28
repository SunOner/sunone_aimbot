import os
import subprocess
import tempfile
import time
import re
import sys
import shutil
import zipfile
import configparser
import signal
import streamlit as st

def restart():
    os.system("streamlit run helper.py")
    quit()

import streamlit as st

st.set_page_config(
    page_title="HELPER",
    page_icon=":wrench:",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    import requests
    import mss
    import supervision
    import numpy
    import bettercam
    import win32api, win32con, win32gui
    import screeninfo
    import asyncio
    import serial
    import cuda
    import onnxruntime
    import keyboard
    from packaging import version
    import numpy as np
    import ultralytics
    from ultralytics import YOLO
    from logic.logger import logger
except (ModuleNotFoundError, ImportError):
    with st.spinner("Installing the needed components"):
        if os.path.exists("./requirements.txt"):
            os.system("pip install -r requirements.txt")
        else:
            logger.info("requirements.txt file not found. Please, redownload aimbot.")
    restart()

try:
    import cv2
except Exception as e:
    logger.info(f"OpenCV import error:\n{e}")

# Aimbot modules
try:
    from logic.config_watcher import cfg
    from logic.buttons import Buttons
except ModuleNotFoundError:
    st.error("Some modules not found. Please, reinstall Aimbot.")

def download_file(url, filename):
    if os.path.exists(filename):
        existing_file_size = os.path.getsize(filename)
    else:
        existing_file_size = 0

    headers = {"Range": f"bytes={existing_file_size}-"}
    response = requests.get(url, headers=headers, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0)) + existing_file_size
    progress_bar = st.progress(0)
    downloaded_size = existing_file_size
    start_time = time.time()

    speed_text = st.empty()

    mode = 'ab' if existing_file_size > 0 else 'wb'
    with open(filename, mode) as file:
        last_update_time = start_time
        last_update_size = downloaded_size
        for data in response.iter_content(8192):
            downloaded_size += len(data)
            file.write(data)
            if total_size_in_bytes > 0:
                progress_bar.progress(downloaded_size / total_size_in_bytes)

            current_time = time.time()

            if current_time - last_update_time >= 1:
                interval_time = current_time - last_update_time
                interval_size = downloaded_size - last_update_size
                speed = interval_size / interval_time if interval_time > 0 else 0
                speed_text.text(f"Speed: {speed / 1024:.2f} KB/s")
                last_update_time = current_time
                last_update_size = downloaded_size

    if total_size_in_bytes != 0 and downloaded_size != total_size_in_bytes:
        st.error("Error with downloading file.")
    else:
        st.success("File downloaded successfully.")
            
def install_cuda():
    file_name = "cuda_12.8.0_571.96_windows.exe"
    st.write("Cuda 12.8 is being downloaded, and installation will begin after downloading.")
    download_file("https://developer.download.nvidia.com/compute/cuda/12.8.0/local_installers/cuda_12.8.0_571.96_windows.exe", file_name)
    try:
        subprocess.call(f'{os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)}')
    except OSError:
        st.error(f"The Cuda file has been downloaded but cannot be executed because administrator permission is required, please install cuda manually, the file ({file_name}) is available in the project folder.")
        
def delete_files_in_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except: pass
                
def find_cuda_path(cuda_version: str = "12.8"):
    cuda_paths = [path for key, value in os.environ.items() if key == "PATH" for path in value.split(";") if "CUDA" in path and cuda_version in path]
    return cuda_paths if cuda_paths else None
    
def get_aimbot_offline_version():
    version_filename = "version"
    
    app, config = 0, 0
    
    if not os.path.exists(version_filename):
        st.toast("The version file was not found, we will consider it an old version of the program.")
        return app, config
    
    try:
        with open(version_filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        for line in lines:
            key, value = line.strip().split('=')
            if key == "app":
                app = value
            if key == 'config':
                config = value
        return app, config
    except Exception:
        st.toast("Error, can't read version file, we will consider it an old version of the program.")
        return app, config

def get_aimbot_online_version():
    app = 0
    config = 0
    try:
        content = requests.get('https://raw.githubusercontent.com/SunOner/sunone_aimbot/main/version').content.decode('utf-8').split('\n')
    except:
        logger.info("[Error] It is impossible to get the current щтдшту version.")
    
    for line in content:
        if line:
            key, value = line.strip().split('=')
            if key == "app":
                app = value
            if key == 'config':
                config = value
    return app, config
            
def upgrade_ultralytics():
    ultralytics_current_version = ultralytics.__version__

    ultralytics_repo_version = requests.get(
        'https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py'
    ).content.decode('utf-8')
    ultralytics_repo_version = re.search(r"__version__\s*=\s*\"([^\"]+)", ultralytics_repo_version).group(1)

    if ultralytics_current_version != ultralytics_repo_version:
        os.system("pip install ultralytics -U")
        return ultralytics_repo_version
    else:
        return ultralytics_current_version

def update_config(new_config_path, current_config_path='config.ini'):
    logger.info("Updating config...")
    shutil.copy(new_config_path, current_config_path)
    logger.info("Config updated successfully.")
    return True

def reinstall_aimbot():    
    logger.info("Checking config versions...")
    config_online_version = int(get_aimbot_online_version()[1])
    config_current_version = get_aimbot_offline_version()
    
    if config_current_version:
        config_current_version = int(config_current_version[1])
    
    logger.info(f"Config current version: {config_current_version}\nConfig online version {config_online_version}")
    
    replace_config = config_online_version != config_current_version
    
    if replace_config:
        logger.info("Config needs update. Will replace with new version.")
    else:
        logger.info("Config is up to date. Will keep current version.")

    logger.info("Deleting old files...")
    for folder in ["./logic", "./media"]:
        try:
            delete_files_in_folder(folder)
        except:
            pass

    base_dir_files = [
        './.gitattributes', './.gitignore', './LICENSE', './README.md', './helper.py', 'run_helper.bat', 
        './run.py', 'run_ai.bat', './requirements.txt', './launcher.py', 'window_names.txt', './version'
    ]
    for file in base_dir_files:
        try:
            os.remove(file)
        except:
            logger.info(f"{file} not found, continued")

    logger.info("Downloading repo. Please wait...")
    download_file("https://github.com/SunOner/sunone_aimbot/archive/refs/heads/main.zip", "main.zip")
    
    logger.info("Unpacking...")
    with zipfile.ZipFile("./main.zip", "r") as zip_ref:
        zip_ref.extractall("./temp_extract")
    
    logger.info("Moving files...")
    for root, dirs, files in os.walk("./temp_extract"):
        for file in files:
            src_path = os.path.join(root, file)
            dest_path = os.path.join(".", os.path.relpath(src_path, "./temp_extract/sunone_aimbot-main"))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if file != "config.ini" or replace_config:
                shutil.move(src_path, dest_path)

    logger.info("Cleaning up...")
    os.remove("./main.zip")
    shutil.rmtree("./temp_extract")

    logger.info("Reinstallation complete. Restarting...")
    
    restart()

def torch_check():
    try:
        import torch
        return torch.cuda.is_available()
    except ModuleNotFoundError:
        return None

def tensorrt_version_check():
    try:
        import tensorrt
        return (True, tensorrt.__version__)
    except ModuleNotFoundError:
        return (False, 0)

if 'ultralytics_version' not in st.session_state:
    with st.spinner('Checking for ultralytics updates...'):
        st.session_state.ultralytics_version = upgrade_ultralytics()

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
        st.session_state.torch_gpu_support = torch_check()

if 'tensorrt_version' not in st.session_state:
    with st.spinner("Checking Tensorrt..."):
        st.session_state.tensorrt_version = tensorrt_version_check()
        
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "HELPER"

with st.sidebar:
    tabs = ["HELPER", "EXPORT", "CONFIG", "TRAIN", "TESTS"]
    st.session_state.current_tab = st.radio(label="**Select tab**", options=tabs, horizontal=False, label_visibility="visible", key="radio_global_tabs")

    if st.button(label="Run Aimbot", key="sidebar_run_aimbot_button"):
        os.system("python run.py")
    
    exit_button_col, send_buttons_col = st.columns(2)
    
    send_c_w = False
    with send_buttons_col:
        send_c_w = st.toggle(
            label="Send ctrl+w",
            value=True,
            key="sidebar_send_c_w_toggle",
            help="Use the automatic keyboard shortcut 'ctrl+w' to close the tab."
        )    
    
    with exit_button_col:
        if st.button(label="Exit", key="sidebar_send_exit_button"):
            if send_c_w == True:
                keyboard.press_and_release('ctrl+w')
            os.kill(os.getpid(), signal.SIGTERM)
    
if st.session_state.current_tab == "HELPER":
    st.title("Helper")

    # AIMBOT
    st.subheader("Aimbot", divider=True)
    
    aimbot_version_col, aimbot_reinstall_button = st.columns(2)
    
    with aimbot_version_col:
        st.markdown(f"Installed Aimbot version: {st.session_state.aimbot_versions[0][0]}  \\\n Github version: {st.session_state.aimbot_versions[1][0]}")
    
    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False
    
    with aimbot_reinstall_button:
        if not st.session_state.show_confirm:
            if st.button(label="Update/Install Sunone Aimbot", key="reinstall_aimbot_button"):
                st.session_state.show_confirm = True
                st.rerun()
        else:
            st.write("Are you sure you want to reinstall?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes", key="confirm_yes"):
                    reinstall_aimbot()
                    st.session_state.show_confirm = False
            with col2:
                if st.button("No", key="confirm_no"):
                    st.session_state.show_confirm = False
                    st.rerun()
    
    # CUDA
    st.subheader("CUDA", divider=True)
    cuda_version_col, cuda_install_button = st.columns(2)
    
    with cuda_version_col:
        if st.session_state.cuda is not None:
            st.markdown("✅ CUDA 12.8 FOUND")
        else:
            st.markdown("❌ CUDA 12.8 NOT FOUND")
    
    with cuda_install_button:
        if st.button(label="Download CUDA 12.8", key="Download_cuda_button"):
            install_cuda()
        
    # TORCH
    st.subheader("Torch", divider=True)
    torch_support_col, torch_reinstall_button = st.columns(2)
    
    with torch_support_col:
        if st.session_state.torch_gpu_support is not None:
            if st.session_state.torch_gpu_support == True:
                st.markdown("✅ Torch is installed with GPU support")
            else:
                st.markdown("❌ Torch is installed without GPU support, reinstall Torch.")
        else:
            st.markdown("❌ Torch is not installed, install Torch.")

    with torch_reinstall_button:
        if st.button(label="Reinstall Torch", key="install_torch_button"):
            if not find_cuda_path():
                st.error("Please, download and install CUDA first.")
            else:
                with st.spinner("Reinstalling Torch. After installation, the application will restart and a new window will open."):
                    os.system("pip uninstall torch torchvision torchaudio -y ")
                    os.system("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")
                    restart()
    # TENSORRT
    st.subheader("TensorRT", divider=True)
    tensorrt_ver_col, tensorrt_reinstall_col = st.columns(2)
    
    with tensorrt_ver_col:
        if st.session_state.tensorrt_version[0] == True:
            st.markdown(f"✅ TensorRT version: {st.session_state.tensorrt_version[1]}")
        else:
            st.markdown("❌ TensorRT not installed")
        
    with tensorrt_reinstall_col:
        if st.button(label="Reinstall TensorRT", key="install_tensorrt_button"):
            if find_cuda_path():
                with st.spinner("Installing TensorRT. After installation, the application will restart and a new window will open."):
                    os.system("pip uninstall tensorrt tensorrt-bindings tensorrt-cu12 tensorrt-cu12_bindings tensorrt-cu12_libs tensorrt-libs -y")
                    os.system("pip install tensorrt")
                    restart()
            else:
                st.error("❌ Please, download and install CUDA first.")

elif st.session_state.current_tab == "EXPORT":
    st.title(body="Model exporter")
    
    models = []
    for root, dirs, files in os.walk("./models"):
        for file in files:
            if file.endswith(".pt"):
                models.append(file)
    
    selected_model = st.selectbox(label="**Select model to export.**", options=models, key="export_selected_model_selectbox")
    
    image_size = st.radio(label="**Select model size**",options=(320, 480, 640), help="The size of the model image must be correct.", key="export_image_size_radio")
    
    if st.button(label="Export model", key="export_export_model_button") and selected_model is not None:
        yolo_model = YOLO(f"./models/{selected_model}")
        
        with st.spinner(text=f"Model {selected_model} exporting..."):
            yolo_model.export(format="engine", imgsz=image_size, half=True, device=0)
            st.success("Model exported!", icon="✅")
            
elif st.session_state.current_tab == "CONFIG":
    st.title(body="Config Editor")
    
    def load_config():
        config = configparser.ConfigParser()
        config.read('./config.ini')
        return config

    def save_config(config):
        config_file_path = 'config.ini'
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as configfile:
                lines = configfile.readlines()

            with open(config_file_path, 'w', encoding='utf-8') as configfile:
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
    st.subheader(body="Detection window", divider=True)
    detection_window_width = st.number_input(
        label="Detection window width",
        value=config.getint('Detection window', 'detection_window_width'),
        key="config_detection_window_width"
    )
    
    detection_window_height = st.number_input(
        label="Detection window height",
        value=config.getint('Detection window', 'detection_window_height'),
        key="config_detection_window_height"
    )
    
    config.set('Detection window', 'detection_window_width', str(detection_window_width))
    config.set('Detection window', 'detection_window_height', str(detection_window_height))

    # Capture Methods
    st.subheader("Capture Methods", divider=True)
    selected_capture_method = st.radio(
        label="Capture Method",
        options=["Bettercam capture", "OBS", "mss"],
        key="config_selected_capture_method"
    )
    
    global_capture_fps = st.number_input(
        label="Global capture FPS",
        min_value=1,
        max_value=240,
        value=cfg.capture_fps,
        key="config_global_capture_fps"
    )
    config.set('Capture Methods', 'capture_fps', str(global_capture_fps))
    
    if selected_capture_method == "Bettercam capture":        
        bettercam_monitor_id = st.number_input(
            label="Bettercam monitor ID",
            value=config.getint('Capture Methods', 'bettercam_monitor_id'),
            key="config_bettercam_monitor_id"
        )
        
        bettercam_gpu_id = st.number_input(
            label="Bettercam GPU ID",
            value=config.getint('Capture Methods', 'bettercam_gpu_id'),
            key="config_bettercam_gpu_id"
        )
        
        config.set('Capture Methods', 'Bettercam_capture', "True")
        config.set('Capture Methods', 'Obs_capture', "False")
        config.set('Capture Methods', 'Obs_capture', "False")
        config.set('Capture Methods', 'bettercam_monitor_id', str(bettercam_monitor_id))
        config.set('Capture Methods', 'bettercam_gpu_id', str(bettercam_gpu_id))
        
    if selected_capture_method == "mss":
        config.set('Capture Methods', 'Bettercam_capture', "False")
        config.set('Capture Methods', 'Obs_capture', "False")
        config.set('Capture Methods', 'Mss_capture', "True")

    if selected_capture_method == "OBS":
        obs_camera_id = st.selectbox(
            label="Obs camera ID",
            options=["auto", "0","1","2","3","4","5","6","7","8","9","10"],
            index=0,
            key="config_obs_camera_id"
        )
        
        config.set('Capture Methods', 'mss_capture', "False")
        config.set('Capture Methods', 'Obs_capture', "True")
        config.set('Capture Methods', 'Obs_camera_id', obs_camera_id)
    
    # Aim
    st.subheader("Aim", divider=True)
    
    body_y_offset = st.slider(
        label="Body Y offset",
        min_value=-0.99,
        max_value=0.99,
        value=config.getfloat('Aim', 'body_y_offset'),
        key="config_body_y_offset"
    )
    
    hideout_targets = st.checkbox(
        label="Hideout targets",
        value=config.getboolean('Aim', 'hideout_targets'),
        key="config_hideout_targets"
    )
    
    disable_headshot = st.checkbox(
        label="Disable headshot",
        value=config.getboolean('Aim', 'disable_headshot'),
        key="config_disable_headshot"
    )
    
    disable_prediction = st.checkbox(
        label="Disable prediction",
        value=config.getboolean('Aim', 'disable_prediction'),
        key="config_disable_prediction"
    )
    
    if not disable_prediction:
        prediction_interval = st.number_input(
            label="Prediction interval",
            value=config.getfloat('Aim', 'prediction_interval'),
            format="%.1f",
            min_value=0.1,
            max_value=5.0,
            step=0.1,
            key="config_prediction_interval"
        )
        
        config.set('Aim', 'disable_prediction', str(disable_prediction))
        config.set('Aim', 'prediction_interval', str(prediction_interval))
        
    third_person = st.checkbox(
        label="Third person mode",
        value=config.getboolean('Aim', 'third_person'),
        key="config_third_person"
    )
    
    config.set('Aim', 'body_y_offset', str(body_y_offset))
    config.set('Aim', 'hideout_targets', str(hideout_targets))
    config.set('Aim', 'disable_headshot', str(disable_headshot))
    config.set('Aim', 'third_person', str(third_person))

    # Hotkeys
    st.subheader("Hotkeys", divider=True)
    hotkey_options = []
    
    for i in Buttons.KEY_CODES:
        hotkey_options.append(str(i))
        
    hotkey_targeting = st.multiselect(
        label="Hotkey targeting",
        options=hotkey_options,
        default=cfg.hotkey_targeting_list,
        key="config_hotkey_targeting"
    )
    
    hotkey_exit = st.selectbox(
        label="Hotkey exit",
        options=hotkey_options,
        index=hotkey_options.index(config.get('Hotkeys', 'hotkey_exit')),
        key="config_hotkey_exit"
    )
    
    hotkey_pause = st.selectbox(
        label="Hotkey pause",
        options=hotkey_options,
        index=hotkey_options.index(config.get('Hotkeys', 'hotkey_pause')),
        key="config_hotkey_pause"
        )
    
    hotkey_reload_config = st.selectbox(
        label="Hotkey reload config",
        options=hotkey_options,
        index=hotkey_options.index(config.get('Hotkeys', 'hotkey_reload_config')),
        key="config_hotkey_reload_config"
    )
    
    targeting_hotkeys_list = ",".join(hotkey_targeting)
    
    config.set('Hotkeys', 'hotkey_targeting', targeting_hotkeys_list)
    config.set('Hotkeys', 'hotkey_exit', hotkey_exit)
    config.set('Hotkeys', 'hotkey_pause', hotkey_pause)
    config.set('Hotkeys', 'hotkey_reload_config', hotkey_reload_config)

    # Mouse
    st.subheader("Mouse", divider=True)
    mouse_dpi = st.number_input(
        label="Mouse DPI",
        min_value=100,
        step=100,
        value=config.getint('Mouse', 'mouse_dpi'),
        key="config_mouse_dpi"
    )
    
    mouse_sensitivity = st.number_input(
        label="Mouse sensitivity",
        min_value=0.1,
        value=config.getfloat('Mouse', 'mouse_sensitivity'),
        key="config_mouse_sensitivity"
    )
    
    mouse_fov_width = st.number_input(
        label="Mouse FOV width",
        value=config.getint('Mouse', 'mouse_fov_width'),
        key="config_mouse_fov_width"
    )
    
    mouse_fov_height = st.number_input(
        label="Mouse FOV height",
        value=config.getint('Mouse', 'mouse_fov_height'),
        key="config_mouse_fov_height"
    )
    
    mouse_min_speed_multiplier = st.number_input(
        label="Mouse minimum speed multiplier",
        value=config.getfloat('Mouse', 'mouse_min_speed_multiplier'),
        key="config_mouse_min_speed_multiplier"
    )
    
    mouse_max_speed_multiplier = st.number_input(
        label="Mouse maximum speed multiplier",
        value=config.getfloat('Mouse', 'mouse_max_speed_multiplier'),
        key="config_mouse_max_speed_multiplier"
    )
    
    mouse_lock_target = st.checkbox(
        label="Mouse lock target",
        value=config.getboolean('Mouse', 'mouse_lock_target'),
        key="config_mouse_lock_target"
    )
    
    mouse_auto_aim = st.checkbox(
        label="Mouse auto aim",
        value=config.getboolean('Mouse', 'mouse_auto_aim'),
        key="config_mouse_auto_aim"
    )
    
    mouse_ghub = st.checkbox(
        label="Mouse GHUB",
        value=config.getboolean('Mouse', 'mouse_ghub'),
        key="config_mouse_ghub"
    )
    
    mouse_rzr = st.checkbox(
        label="Mouse Razer",
        value=config.getboolean('Mouse', 'mouse_rzr'),
        key="config_mouse_rzr")
    
    config.set('Mouse', 'mouse_dpi', str(mouse_dpi))
    config.set('Mouse', 'mouse_sensitivity', str(mouse_sensitivity))
    config.set('Mouse', 'mouse_fov_width', str(mouse_fov_width))
    config.set('Mouse', 'mouse_fov_height', str(mouse_fov_height))
    config.set('Mouse', 'mouse_min_speed_multiplier', str(mouse_min_speed_multiplier))
    config.set('Mouse', 'mouse_max_speed_multiplier', str(mouse_max_speed_multiplier))
    config.set('Mouse', 'mouse_lock_target', str(mouse_lock_target))
    config.set('Mouse', 'mouse_auto_aim', str(mouse_auto_aim))
    config.set('Mouse', 'mouse_ghub', str(mouse_ghub))
    config.set('Mouse', 'mouse_rzr', str(mouse_rzr))

    # Shooting
    st.subheader("Shooting", divider=True)
    
    auto_shoot = st.checkbox(
        label="Auto shoot",
        value=config.getboolean('Shooting', 'auto_shoot'),
        key="config_auto_shoot"
    )
    
    triggerbot = st.checkbox(
        label="Triggerbot",
        value=config.getboolean('Shooting', 'triggerbot'),
        key="config_triggerbot"
    )
    
    force_click = st.checkbox(
        label="Force click",
        value=config.getboolean('Shooting', 'force_click'),
        key="config_force_click"
    )
    
    bScope_multiplier = st.number_input(
        label="bScope multiplier",
        step=.10,
        value=config.getfloat('Shooting', 'bScope_multiplier'),
        key="config_bScope_multiplier"
    )
    
    config.set('Shooting', 'auto_shoot', str(auto_shoot))
    config.set('Shooting', 'triggerbot', str(triggerbot))
    config.set('Shooting', 'force_click', str(force_click))
    config.set('Shooting', 'bScope_multiplier', str(bScope_multiplier))

    # Arduino
    st.subheader("Arduino", divider=True)
    
    arduino_move = st.checkbox(
        label="Arduino move",
        value=config.getboolean('Arduino', 'arduino_move'),
        key="config_arduino_move"
    )
    
    arduino_shoot = st.checkbox(
        label="Arduino shoot",
        value=config.getboolean('Arduino', 'arduino_shoot'),
        key="config_arduino_shoot"
    )
    
    if arduino_move or arduino_shoot:
        arduino_port = st.text_input(
            label="Arduino port",
            value=config.get('Arduino', 'arduino_port'),
            key="config_arduino_port"
        )
        
        baudrates = [2400,
                     4800,
                     9600,
                     19200,
                     31250,
                     38400,
                     57600,
                     74880,
                     115200]
        
        arduino_baudrate = st.selectbox(
            label="Arduino baudrate",
            options=baudrates,
            index=baudrates.index(config.getint('Arduino', 'arduino_baudrate')),
            key="config_arduino_baudrate"
        )
        
        arduino_16_bit_mouse = st.checkbox(
            label="Arduino 16 bit mouse",
            value=config.getboolean('Arduino', 'arduino_16_bit_mouse'),
            key="config_arduino_16_bit_mouse"
        )
        
        config.set('Arduino', 'arduino_move', str(arduino_move))
        config.set('Arduino', 'arduino_shoot', str(arduino_shoot))
        config.set('Arduino', 'arduino_port', arduino_port)
        config.set('Arduino', 'arduino_baudrate', str(arduino_baudrate))
        config.set('Arduino', 'arduino_16_bit_mouse', str(arduino_16_bit_mouse))

    # AI
    st.subheader("AI", divider=True)
    
    models = []
    for root, dirs, files in os.walk("./models"):
        for file in files:
            if file.endswith(".pt") or file.endswith(".engine"):
                models.append(file)
    
    AI_model_name = st.selectbox(
        label="AI model",
        options=models,
        key="config_AI_model_name"
    )
    
    imgsz = [320, 480, 640]
    AI_model_image_size = st.selectbox(
        label="AI model image size",
        options=imgsz,
        index=imgsz.index(config.getint('AI', 'AI_model_image_size')),
        key="config_AI_model_image_size"
    )
    
    AI_conf = st.slider(
        label="AI confidence",
        min_value=0.01,
        max_value=0.99,
        value=config.getfloat('AI', 'AI_conf'),
        key="config_AI_conf"
    )
    
    devices = ["cpu", "0", "1", "2", "3", "4", "5"]
    AI_device = st.selectbox(
        label="AI device",
        options=devices,
        index=devices.index(config.get('AI', 'AI_device')),
        key="config_AI_device"
    )
    
    AI_enable_AMD = st.checkbox(
        label="AI enable AMD",
        value=config.getboolean('AI', 'AI_enable_AMD'),
        key="config_AI_enable_AMD"
    )
    
    config.set('AI', 'AI_model_name', AI_model_name)
    config.set('AI', 'AI_model_image_size', str(AI_model_image_size))
    config.set('AI', 'AI_conf', str(AI_conf))
    config.set('AI', 'AI_device', AI_device)
    config.set('AI', 'AI_enable_AMD', str(AI_enable_AMD))

    # Overlay
    st.subheader("Overlay", divider=True)
    
    show_overlay = st.toggle(
        label="Show overlay",
        value=config.getboolean('overlay', 'show_overlay'),
        key="config_show_overlay"
    )
    
    if show_overlay:
        overlay_show_borders = st.checkbox(
            label="Overlay show borders",
            value=config.getboolean('overlay', 'overlay_show_borders'),
            key="config_overlay_show_borders"
        )
        
        overlay_show_boxes = st.checkbox(
            label="Overlay show boxes",
            value=config.getboolean('overlay', 'overlay_show_boxes'),
            key="config_overlay_show_boxes"
        )
        
        overlay_show_target_line = st.checkbox(
            label="Overlay show target line",
            value=config.getboolean('overlay', 'overlay_show_target_line'),
            key="config_overlay_show_target_line"
        )
        
        overlay_show_target_prediction_line = st.checkbox(
            label="Overlay show target prediction line",
            value=config.getboolean('overlay', 'overlay_show_target_prediction_line'),
            key="config_overlay_show_target_prediction_line"
        )
        
        overlay_show_labels = st.checkbox(
            label="Overlay show labels",
            value=config.getboolean('overlay', 'overlay_show_labels'),
            key="config_overlay_show_labels"
        )
        
        overlay_show_conf = st.checkbox(
            label="Overlay show confidence",
            value=config.getboolean('overlay', 'overlay_show_conf'),
            key="config_overlay_show_conf"
        )
        
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
    st.subheader("Debug window", divider=True)
    
    show_window = st.toggle(
        label="Show debug window",
        value=config.getboolean('Debug window', 'show_window'),
        key="config_show_window"
    )
    
    if show_window:
        show_detection_speed = st.checkbox(
            label="Show detection speed",
            value=config.getboolean('Debug window', 'show_detection_speed'),
            key="config_show_detection_speed"
        )
        
        show_window_fps = st.checkbox(
            label="Show window FPS",
            value=config.getboolean('Debug window', 'show_window_fps'),
            key="config_show_window_fps"
        )
        
        show_boxes = st.checkbox(
            label="Show boxes",
            value=config.getboolean('Debug window', 'show_boxes'),
            key="config_show_boxes"
        )
        
        show_labels = st.checkbox(
            label="Show labels",
            value=config.getboolean('Debug window', 'show_labels'),
            key="config_show_labels"
        )
        
        show_conf = st.checkbox(
            label="Show confidence",
            value=config.getboolean('Debug window', 'show_conf'),
            key="config_show_conf"
        )
        
        show_target_line = st.checkbox(
            label="Show target line",
            value=config.getboolean('Debug window', 'show_target_line'),
            key="config_show_target_line"
        )
        
        show_target_prediction_line = st.checkbox(
            label="Show target prediction line",
            value=config.getboolean('Debug window', 'show_target_prediction_line'),
            key="config_show_target_prediction_line"
        )
        
        show_bScope_box = st.checkbox(
            label="Show bScope box",
            value=config.getboolean('Debug window', 'show_bScope_box'),
            key="config_show_bScope_box"
        )
        
        show_history_points = st.checkbox(
            label="Show history points",
            value=config.getboolean('Debug window', 'show_history_points'),
            key="config_show_history_points"
        )
        
        debug_window_always_on_top = st.checkbox(
            label="Debug window always on top",
            value=config.getboolean('Debug window', 'debug_window_always_on_top'),
            key="config_debug_window_always_on_top"
        )
        
        spawn_window_pos_x = st.number_input(
            label="Spawn window position X",
            value=config.getint('Debug window', 'spawn_window_pos_x'),
            key="config_spawn_window_pos_x"
        )
        
        spawn_window_pos_y = st.number_input(
            label="Spawn window position Y",
            value=config.getint('Debug window', 'spawn_window_pos_y'),
            key="config_spawn_window_pos_y"
        )
        
        debug_window_scale_percent = st.number_input(
            label="Debug window scale percent:",
            value=config.getint('Debug window', 'debug_window_scale_percent'),
            key="config_debug_window_scale_percent"
        )
        
        debug_window_screenshot_key = st.selectbox(
            label="Screenshot key",
            options=hotkey_options,
            index=hotkey_options.index(config.get('Debug window', 'debug_window_screenshot_key')),
            key="config_debug_window_screenshot_key"
        )
        
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
        config.set('Debug window', 'debug_window_screenshot_key', str(debug_window_screenshot_key))
    else:
        config.set('Debug window', 'show_wpip indow', "False")

    with st.sidebar:
        if st.button('Save Config', key="sidebar_config_save_button"):
            save_config(config)

elif st.session_state.current_tab == "TRAIN":
    st.title("Train model")
    
    # model selection
    pretrained_models = [
        "yolov8n.pt", "yolov8s.pt", "yolov8m.pt",
        "yolov10n.pt", "yolov10s.pt", "yolov10m.pt",
        "yolo11n.pt", "yolo11s.pt", "yolo11m.pt",
        "yolo12n.pt", "yolo12s.pt", "yolo12m.pt"
    ]
    
    resume = False
    user_trained_models = st.checkbox(
        label="Use user pretrained models",
        value=False,
        key="TRAIN_user_trained_models"
    )
    
    if user_trained_models:
        last_pt_files = []
        root_folder = r'runs\detect'

        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file == 'last.pt':
                    last_pt_files.append(os.path.join(root, file))
                    
        selected_model_path = st.selectbox(
            label="Select model",
            options=last_pt_files,
            key="TRAIN_ai_model"
        )
        
        resume = st.checkbox(
            label="Resume training",
            value=False,
            key="TRAIN_resume"
        )
    else:
        selected_model_path = st.selectbox(
            label="Select model",
            options=pretrained_models,
            index=7,
            key="TRAIN_ai_model"
        )
    
    if not resume:
        data_yaml = st.text_input(
            label="Path to the dataset configuration file",
            value="logic/game.yaml",
            key="TRAIN_data_yaml"
        )
        
        epochs = st.number_input(
            label="Epochs",
            value=80,
            format="%u",
            min_value=1,
            step=10,
            key="TRAIN_epochs"
        )
        
        img_size = st.selectbox(
            label="Image size",
            options=[1280, 640, 320, 160],
            index=1,
            key="TRAIN_img_size"
        )
        
        use_cache = st.checkbox(
            label="Enables caching of dataset images in memory",
            value=False,
            key="TRAIN_use_cache"
        )
        
        augment = st.checkbox(
            label="Use augmentation",
            value=True,
            key="TRAIN_use_augmentation")
        
        if augment:
            augment_degrees = st.number_input(
                label="Degrees",
                format="%u",
                value=5,
                min_value=-180,
                max_value=180,
                step=5,
                key="TRAIN_augment_degrees"
            )
            
            augment_flipud = st.number_input(
                label="Flipud",
                format="%.1f",
                value=0.2,
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                key="TRAIN_augment_flipud"
            )
    
    input_devices = ["cpu", "0", "1", "2", "3", "4", "5"]
    train_device = st.selectbox(
        label="Specifies the computational device for training",
        options=input_devices,
        index=1,
        help="cpu - Train on processor, 0-5 GPU ID for training.",
        key="TRAIN_train_device"
    )
    
    if train_device != "cpu":
        train_device = int(train_device)
    
    batch_size_options = ["Percentage ratio", "auto", "4", "8", "16", "32", "64", "128", "256"]
    batch_size = st.selectbox(
        label="Batch size",
        options=batch_size_options,
        index=1,
        key="TRAIN_batch_size"
    )
    
    if batch_size == "auto":
        batch_size = "-1"
    
    if batch_size == "Percentage ratio":
        batch_size = st.number_input(
            label="Enter percentage ratio usage GPU vram",
            min_value=0.05,
            max_value=0.95,
            step=0.05,
            value=0.70,
            format="%0.02f",
            key="TRAIN_custom_percentage_ratio"
        )
    
    profile = st.checkbox(
        label="Profile",
        value=False,
        key="TRAIN_profile"
    )
        
    wandb = st.checkbox(
        label="Force disable WANDB logger",
        value=True,
        key="TRAIN_wandb"
    )
    
    if wandb:
        os.environ['WANDB_DISABLED'] = 'true'
    else:
        os.environ['WANDB_DISABLED'] = 'false'
    
    if st.button(label="Start", key="TRAIN_start_train_button"):
        with st.spinner("Train in process, check terminal window.", show_time=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_script:
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
                    profile={profile},
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
                os.system(f'python3 {temp_script_path}')

            st.success(body="Training started in a new terminal window.")
    
elif st.session_state.current_tab == "TESTS":
    def test_detections(
        input_model: str = None,
        source_method="Default",
        video_source=None,
        TOPMOST=True,
        model_image_size = None,
        input_device = 0,
        input_delay = 30,
        resize_factor = 100,
        ai_conf = 0.20
):
        if input_model is None:
            return ("error", "Model not selected")
        
        # CUDA GPU RETURN
        cuda_support = st.session_state.torch_gpu_support
        if not cuda_support:
            return ("error", "Cuda is not supported")
        
        # Apply video source
        if source_method == "Default":
            default_source_video = "media/tests/test_det.mp4"
            
            if os.path.exists(default_source_video):
                video_source = default_source_video
            else:
                st.error(f"Default source media for detection tests not found!")
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
                
                cv2.putText(annotated_frame, "When life gives you lemons, Make orange juice.", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                
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
    ai_model = st.selectbox(
        label="AI Model",
        options=models,
        key="TESTS_ai_model_selectbox",
        help="Put model to './models' path."
    )

    # SELECT MODEL IMAGE SIZE
    model_image_sizes = [320, 480, 640]
    model_size = st.selectbox(
        label="AI Model image size",
        options=model_image_sizes,
        key="TESTS_model_size_selectbox",
        index=2
    )
    
    # VIDEO SOURCE
    methods = ["Default", "Input file"]
    video_source_method = st.selectbox(
        label="Select video input method",
        options=methods,
        index=0,
        key="TESTS_video_source_method_selectbox"
    )

    # TOPMOST
    TOPMOST = st.toggle(
        label="Test window on top",
        value=True,
        key="tests_topmost"
    )
    
    # DEVICE
    test_devices = ["cpu", "0", "1", "2", "3", "4", "5"]
    device = st.selectbox(
        label="Device",
        options=test_devices,
        index=1,
        key="tests_test_devices"
    )
    
    if device != "cpu":
        device = int(device)
    
    # DELAY
    cv2_delay = st.number_input(
        label="CV2 frame wait delay",
        min_value=1,
        max_value=120,
        step=1,
        format="%u",
        value=30,
        key="TESTS_cv2_delay_number_input"
    )
    
    # RESIZE
    cv2_resize = st.number_input(
        label="Resize test window",
        min_value=10,
        max_value=100,
        value=80,
        step=1,
        format="%u",
        key="ESTS_cv2_resize_number_input"
    )
    
    # DETECTION CONF
    ai_conf = st.number_input(
        label="Minimum confidence threshold",
        min_value=0.01,
        max_value=0.99,
        step=0.01,
        format="%.2f",
        value=0.20,
        key="tests_ai_conf"
    )
    
    input_video = None
    if video_source_method == "Input file":
        video_source_input_file = st.file_uploader(
            label="Import video file",
            accept_multiple_files=False,
            type=(["mp4"]),
            key="TESTS_input_file_video_source_input_file"
        )
        
        input_video = video_source_input_file

    if st.button(label="Test detections", key="TESTS_text_detections_button"):
        if video_source_method in methods:
            if input_video == None and video_source_method == "Input file":
                st.error("Video source not found.")
            else:
                test_detections(
                    input_model=ai_model,
                    source_method=video_source_method,
                    video_source=input_video,
                    model_image_size=model_size,
                    TOPMOST=TOPMOST,
                    input_delay=cv2_delay,
                    input_device=device,
                    resize_factor=cv2_resize,
                    ai_conf=ai_conf
                )
        else:
            st.error("Select correct video input method.")