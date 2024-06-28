import os
import subprocess
import time
import re
import sys
import shutil
import zipfile

try:
    import streamlit as st
    import requests
    import numpy
    import bettercam
    import win32api, win32con, win32gui
    import ultralytics
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
        './.gitattributes', './.gitignore', './config.ini', './helper.py', 'run_helper.bat', './LICENSE', './README.md', './run.py', './requirements.txt', './version', 'launcher.py', 'window_names.txt', 
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