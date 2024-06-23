import os
import re
import sys
import shutil
import zipfile
import subprocess
import requests
import ctypes
import time
import winreg
import os.path
from packaging import version
from tqdm import tqdm

reload_prestart = False

def install_package(package_name):
    os.system(f'pip install {package_name}')
    global reload_prestart
    reload_prestart = True

def check_and_install_packages():
    packages = [
        ('tqdm', 'tqdm'),
        ('requests', 'requests'),
        ('cuda', 'cuda_python'),
        ('bettercam', 'bettercam'),
        ('numpy', 'numpy'),
        ('win32gui', 'pywin32'),
        ('ultralytics', 'ultralytics'),
        ('screeninfo', 'screeninfo'),
        ('asyncio', 'asyncio'),
        ('onnxruntime', 'onnxruntime onnxruntime-gpu'),
        ('serial', 'pyserial'),
        ('torch', '--pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124'),
        ('cv2', 'opencv-python')
    ]

    for module_name, package_name in packages:
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            install_package(package_name)

    if reload_prestart:
        os.system('py helper.py')
        print('restarting...')
        quit()

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(filename, 'wb') as file:
        for data in response.iter_content(1024):
            progress_bar.update(len(data))
            file.write(data)
    
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print('Error with downloading file.')

def upgrade_ultralytics():
    import ultralytics
    print('Checking for new ultralytics version...')
    ultralytics_current_version = ultralytics.__version__

    ultralytics_repo_version = requests.get(
        'https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py'
    ).content.decode('utf-8')
    ultralytics_repo_version = re.search(r"__version__\s*=\s*\"([^\"]+)", ultralytics_repo_version).group(1)

    if ultralytics_current_version != ultralytics_repo_version:
        print('The versions of ultralytics do not match\nAn update is in progress...')
        os.system('pip install ultralytics --upgrade')
    else:
        os.system('cls')

def upgrade_pip():
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, text=True, check=True)
        current_version = result.stdout.split(' ')[1]
        
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', '--dry-run'], capture_output=True, text=True, check=True)
        latest_version = None
        for line in result.stdout.splitlines():
            if 'Collecting pip' in line:
                latest_version = line.split(' ')[-1].strip('()')
                break
        
        if latest_version and version.parse(current_version) < version.parse(latest_version):
            print(f'Current pip version: {current_version}')
            print(f'Upgrading pip to version: {latest_version}')
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        else:
            print('Pip is already up-to-date.')
    except subprocess.CalledProcessError as e:
        print(f'An error occurred: {e}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

def get_aimbot_current_version():
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
    content = requests.get('https://raw.githubusercontent.com/SunOner/yolov8_aimbot/main/version').content.decode('utf-8').split('\n')
    if content == ['404: Not Found']:
        print('Something wrong with https://raw.githubusercontent.com.\nSunOner repository is still alive?')
        return 0, 0
    else:
        app, config = 0, 0
        for line in content:
            key, value = line.strip().split('=')
            if key == "app":
                app = value
            if key == 'config':
                config = value
        return app, config

def delete_files_in_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def update_yolov8_aimbot():
    print('Deleting old files...')
    try:
        delete_files_in_folder('./logic')
    except:
        pass
    try:
        delete_files_in_folder('./media')
    except:
        pass

    base_dir_files = [
        './.gitattributes', './.gitignore', './LICENSE', './README.md', './helper.py', './run.py', './requirements.txt', './launcher.py', 'window_names.txt',
    ]
    for file in base_dir_files:
        try:
            os.remove(file)
        except:
            print(f'{file} not found, continued')

    replace_config = False
    config_online_version = int(get_aimbot_online_version()[1])
    config_current_version = get_aimbot_current_version()
    
    if config_current_version:
        config_current_version = int(config_current_version[1])
    
    print(f'Config current version: {config_current_version}\nConfig online version {config_online_version}')
    
    if config_online_version != config_current_version:
        print('Removing config with old version and installing fresh.')
        try:
            os.remove('./config.ini')
        except:
            pass
        replace_config = True
    else:
        print('Config has a fresh version. We don\'t touch him.')
        
    try:
        os.remove('./version')
    except:
        pass
    
    print("Downloading repo. Please wait...")
    download_file('https://github.com/SunOner/yolov8_aimbot/archive/refs/heads/main.zip', 'main.zip')
    print('Unpacking...')
    with zipfile.ZipFile(r'./main.zip', 'r') as zip_ref:
        zip_ref.extractall('./')
    print('Deleting downloaded zip...')
    os.remove(r'./main.zip')
    
    new_dirs = ['./logic', './media', './media/tests', './docs/en', './docs/ru', './models']
    for dir in new_dirs:
        if not os.path.isdir(dir):
            os.makedirs(dir)

    temp_aimbot_files = [
        './.gitattributes', './.gitignore', './config.ini', './helper.py', './LICENSE', './README.md', './run.py', './requirements.txt', './version', 'launcher.py', 'window_names.txt', 
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
            if temp_file == './yolov8_aimbot-main/config.ini' and not replace_config:
                continue
            shutil.move(f'yolov8_aimbot-main/{temp_file}', temp_file)
        except:
            pass

    try:
        delete_files_in_folder('./yolov8_aimbot-main')
        os.rmdir('./yolov8_aimbot-main')
    except:
        pass

    os.system('py helper.py')
    quit()

def find_cuda_path():
    cuda_paths = [path for key, value in os.environ.items() if key == 'PATH' for path in value.split(';') if 'CUDA' in path and '12.4' in path]
    return cuda_paths if cuda_paths else None

def install_tensorrt():
    if find_cuda_path():
        os.system('pip install tensorrt')
    else:
        print('First install Cuda')

def install_cuda():
    os.system('cls')
    print('Cuda 12.4 is being downloaded, and installation will begin after downloading.')
    download_file('https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe', './cuda_12.4.0_551.61_windows.exe')
    subprocess.call(f'{os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuda_12.4.0_551.61_windows.exe")}')

def test_detections():
    import ultralytics
    from ultralytics import YOLO
    import cv2
    import win32gui, win32con
    cuda_support = ultralytics.utils.checks.cuda_is_available()
    if cuda_support:
        print('Cuda support True')
    else:
        print('Cuda is not supported\nTrying to reinstall torch with GPU support...')
        force_reinstall_torch()
        
    model = YOLO(f'models/{cfg.AI_model_name}', task='detect')
    cap = cv2.VideoCapture('media/tests/test_det.mp4')
    window_name = f'Model: {cfg.AI_model_name} imgsz: {cfg.ai_model_image_size}'
    cv2.namedWindow(window_name)
    debug_window_hwnd = win32gui.FindWindow(None, window_name)
    win32gui.SetWindowPos(debug_window_hwnd, win32con.HWND_TOPMOST, 100, 100, 200, 200, 0)
    
    while cap.isOpened():
        success, frame = cap.read()
        if success:
            result = model(frame, stream=False, show=False, imgsz=cfg.ai_model_image_size, device=cfg.AI_device, verbose=False, conf=0.40)
            annotated_frame = result[0].plot()
            cv2.putText(annotated_frame, 'TEST 1234567890', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.imshow(window_name, annotated_frame)
            if cv2.waitKey(30) & 0xFF == ord("q"):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()

def force_reinstall_torch():
    os.system('pip uninstall torch torchvision torchaudio')
    os.system('pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124')

def print_menu():
    os.system('cls')
    print(f'Installed version: {get_aimbot_current_version()[0]}, online version: {get_aimbot_online_version()[0]}\n')
    print("1: Update/Reinstall YOLOv8_aimbot")
    print("2: Download Cuda 12.4")
    print("3: Install TensorRT 10.0.1")
    print("4: Test the object detector")
    print("5: Force reinstall Torch (Nightly-GPU)")
    print("0: Exit")

def main():
    try:
        while True:
            print_menu()
            choice = input("Select an option: ")

            if choice == "1":
                update_yolov8_aimbot()
            elif choice == "2":
                install_cuda()
            elif choice == "3":
                install_tensorrt()
            elif choice == "4":
                test_detections()
            elif choice == "5":
                force_reinstall_torch()
            elif choice == "0":
                print("Exiting the program...")
                break
            else:
                print("Incorrect input, try again.")
    except:
        quit()

if __name__ == "__main__":
    try:
        from logic.config_watcher import cfg
    except:
        print('File config_watcher.py not found, reinstalling...')
        update_yolov8_aimbot()
    upgrade_pip()
    upgrade_ultralytics()
    main()