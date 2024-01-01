import re
import os, ctypes
import os.path
import sys, subprocess
import time 
import shutil
import zipfile
import winreg

try:
    import requests
except:
    os.system('pip install requests')
    os.system('pip install -r requirements.txt')
    os.system('pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121')
    os.system('py helper.py')
    quit()
try:
    from tqdm import tqdm
except:
    print('tqdm not found, installation is in progress')
    os.system('pip install tqdm')
    from tqdm import tqdm

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
        print("Error with downloading file.")
try:
    import cuda
except:
    print('cuda_python not found, installation is in progress')
    os.system('pip install cuda_python')
try:
    import bettercam
except:
    print('bettercam not found, installation is in progress')
    os.system('pip install bettercam')
try:
    import numpy
except:
    print('numpy not found, installation is in progress')
    os.system('pip install numpy')
try:
    import win32gui, win32ui, win32con
except:
    print('pywin32 not found, installation is in progress')
    os.system('pip install pywin32')
try:
    import ultralytics
except:
    print('ultralytics not found, installation is in progress')
    os.system('pip install ultralytics')
    import ultralytics
try:
    import screeninfo
except:
    print('screeninfo not found, installation is in progress')
    os.system('pip install screeninfo')
try:
    import asyncio
except:
    print('asyncio not found, installation is in progress')
    os.system('pip install asyncio')
try:
    import onnxruntime
except:
    print('onnxruntime not found, installation is in progress')
    os.system('pip install onnxruntime')
    os.system('pip install onnxruntime-gpu')
try:
    import serial
except:
    print('pyserial not found, installation is in progress')
    os.system('pip install pyserial')
try:
    import torch
except:
    print('torch not found, installation is in progress')
    os.system('pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121')

def get_system_path():
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_READ) as key:
        return winreg.QueryValueEx(key, 'Path')[0]

def set_system_path(new_path):
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
    from ctypes import windll
    windll.user32.SendMessageTimeoutA(0xFFFF, 0x001A, 0, None, 0x02, 1000, None)

def upgrade_ultralytics():
    print('Checks new ultralytics version...')
    ultralytics_current_version = ultralytics.__version__

    ultralytics_repo_version = requests.get('https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py').content.decode('utf-8')
    ultralytics_repo_version = re.search(r"__version__\s*=\s*'([^']+)'", ultralytics_repo_version).group(1)

    if ultralytics_current_version != ultralytics_repo_version:
        print('The versions of ultralytics do not match\nAn update is in progress...')
        os.system('pip install ultralytics --upgrade')
    else:
        os.system('cls')

def upgrade_pip():
    print('Checks new pip version...')
    ver = os.popen('pip -V').read().split(' ')[1]
    if ver != '23.3.2':
        print('The pip version does not match the required one.\nAn update is in progress...')
        os.system("python -m pip install --upgrade pip")
    else:
        os.system('cls')

def get_aimbot_current_version():
    try:
        app = 0
        config = 0
        with open('./version', 'r') as file:
            lines = file.readlines()
        for line in lines:
            key, value = line.strip().split('=')
            if key == "app":
                app = value
            if key == 'config':
                config = value
        return app, config
                
    except:
        print('The version file was not found, we will consider it an old version of the program.')
        return '0.0.0'

def get_aimbot_version():
    app = 0
    config = 0
    content = requests.get('https://raw.githubusercontent.com/SunOner/yolov8_aimbot/main/version').content.decode('utf-8').split('\n')
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
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def Update_yolov8_aimbot():
    print('Deleting old files..')
    
    try:
        delete_files_in_folder('./logic')
    except:
        pass
    try:
        delete_files_in_folder('./media')
    except:
        pass
    base_dir_files = ['./checks.py', './helper.py', './run.py', './version', './requirements.txt']
    for file in base_dir_files:
        try:
            os.remove(file)
        except:
            print(file, 'not found, continued')
    # Config
    try:
        replace_config = False
        config_online_version = int(get_aimbot_version()[1])
        config_current_version = int(get_aimbot_current_version()[1])
        
        if config_online_version > config_current_version:
            print('Removing config with old version and installing fresh.')
            os.remove('./config.ini')
            replace_config = True
        if config_online_version == config_current_version:
            print('Config has a fresh version. We don\'t touch him.')
    except:
        print('File config.ini is not found, continued')
        replace_config = True
        pass

    print("Downloading repo. Please wait...")
    
    download_file('https://github.com/SunOner/yolov8_aimbot/archive/refs/heads/main.zip', 'main.zip')
    print('Unpacking...')
    with zipfile.ZipFile(r'./main.zip', 'r') as zip_ref:
        zip_ref.extractall('./')
    print('Deleting downloaded zip...')
    os.remove(r'./main.zip')
    
    if os.path.isdir('./logic') == False:
        os.makedirs('./logic')
        
    if os.path.isdir('./media') == False:
        os.makedirs('./media')
        
    if os.path.isdir('./media/tests') == False:
        os.makedirs('./media/tests')
        
    if os.path.isdir('./docs/en') == False:
        os.makedirs('./docs/en')
    if os.path.isdir('./docs/ru') == False:
        os.makedirs('./docs/ru')
    
    if os.path.isdir('./models') == False:
        os.makedirs('./models')

    temp_aimbot_files = [
        './checks.py', './config.ini', './helper.py', './run.py', './requirements.txt', './version', 
        './logic/arduino.py', './logic/capture.py', './logic/config_watcher.py', './logic/game.yaml', './logic/ghub_mouse.dll', './logic/keyboard.py', './logic/mouse.py', 
        './media/aimbot.png', './media/cmd_admin_en.png', './media/cmd_admin_ru.png', './media/cmd_cd_path.png',
        './media/copy_explorer_path.png', './media/python_add_to_path.png', './media/cuda.png', './media/environment_variables.png',
        './media/environment_variables_path.png', './media/one.gif', './media/python.png',
        './media/tests/test_det.mp4'
        './docs/en/helper_en.md', './docs/en/install_guide_en.md', './docs/en/questions_en.md',
        './docs/ru/helper_ru.md', './docs/ru/install_guide_ru.md', './docs/ru/questions_ru.md',
        './models/sunxds_0.2.9.6.pt' ]

    print('Moving files from ./temp/')
    for temp_file in temp_aimbot_files:
        print(temp_file)
        try:
            if temp_file == './yolov8_aimbot-main/config.ini' and replace_config == False:
                pass
            else:
                shutil.move('yolov8_aimbot-main/{0}'.format(temp_file), temp_file)
        except:
            pass
    try:
        delete_files_in_folder('./yolov8_aimbot-main')
        os.rmdir('./yolov8_aimbot-main')
    except Exception as s:
        print(s)
        pass
    os.system('py helper.py')
    quit()

def find_cuda_path():
    cuda_paths = []
    for key, value in os.environ.items():
        if key == 'PATH':
            for path_string in value.split(';'):
                if r'CUDA' in path_string and r'12.1' in path_string:
                    cuda_paths.append(path_string)

    if len(cuda_paths):
        return cuda_paths
    else:
        return None

def find_tensorrt_path():
    path = None
    for key, value in os.environ.items():
        if key == 'PATH':
            for path_string in value.split(';'):
                if r'TensorRT' in path_string and r'lib' in path_string:
                    path = path_string
    
    if path is not None:
        return path
    else:
        return None

def Install_TensorRT():
    cuda = find_cuda_path()
    if cuda is not None:
        if not os.path.isfile('TensorRT-8.6.1.6.Windows10.x86_64.cuda-12.0.zip') and os.path.isdir('TensorRT-8.6.1.6') == False:
            print('TensorRT in not downloaded\nDownloading TensorRT 8.6.1.6...')
            download_file('https://developer.nvidia.com/downloads/compute/machine-learning/tensorrt/secure/8.6.1/zip/TensorRT-8.6.1.6.Windows10.x86_64.cuda-12.0.zip', 'TensorRT-8.6.1.6.Windows10.x86_64.cuda-12.0.zip')
        
        if not os.path.isdir('TensorRT-8.6.1.6'):
            print('Unpacking the TensorRT archive, please wait...')
            with zipfile.ZipFile(r'./TensorRT-8.6.1.6.Windows10.x86_64.cuda-12.0.zip', 'r') as zip_ref:
                zip_ref.extractall('./')
        
        os.system('pip install ./TensorRT-8.6.1.6/python/tensorrt-8.6.1-cp311-none-win_amd64.whl')

        current_path = get_system_path()
        tensorrt_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TensorRT-8.6.1.6\\lib')

        if tensorrt_lib_path not in current_path:
            new_path = current_path + ';' + tensorrt_lib_path
            set_system_path(new_path)
            print(f'New path added: {tensorrt_lib_path}')
        else:
            print(f'Env path already exists: {tensorrt_lib_path}')

        tensorrt_lib_files = ['nvinfer.dll', 'nvinfer.lib', 'nvinfer_builder_resource.dll', 'nvinfer_dispatch.dll', 'nvinfer_dispatch.lib', 'nvinfer_lean.dll',
                            'nvinfer_lean.lib', 'nvinfer_plugin.dll', 'nvinfer_plugin.lib', 'nvinfer_vc_plugin.dll', 'nvinfer_vc_plugin.lib',
                            'nvonnxparser.dll', 'nvonnxparser.lib', 'nvparsers.dll', 'nvparsers.lib']
        
        for cuda_path in cuda:
            if 'bin' in cuda_path:
                for lib in tensorrt_lib_files:
                    shutil.copy2('{0}\TensorRT-8.6.1.6\lib\\{1}'.format(os.path.join(os.path.dirname(os.path.abspath(__file__))), lib), cuda_path)
    else:
        print('First install cuda 12.1.')
        
def install_cuda():
    os.system('cls')
    print('Cuda 12.1 is being downloaded, and installation will begin after downloading.')
    download_file('https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_531.14_windows.exe', './cuda_12.1.0_531.14_windows.exe')
    subprocess.call('{}/cuda_12.1.0_531.14_windows.exe'.format(os.path.join(os.path.dirname(os.path.abspath(__file__)))))
    
def print_menu():
    os.system('cls')
    print('Run this script as an administrator to work correctly.')
    # TODO: print last error
    print('Installed version is: {0}, latest: {1}\n'.format(get_aimbot_current_version()[0], get_aimbot_version()[0]))

    print("1: Update/Reinstall YOLOv8_aimbot")
    print("2: Download Cuda 12.1")
    print("3: Install TensorRT")
    print("0: Exit")

def main():
    try:
        while True:
            print_menu()
            choice = input("Select an option: ")

            if choice == "1":
                Update_yolov8_aimbot()
            
            elif choice == "2":
                install_cuda()
            
            elif choice == "3":
                Install_TensorRT()
                
            elif choice == "0":
                print("Exiting the program...")
                break
            
            else:
                print("Incorrect input, try again.")
    except: # ctrl + z
        quit()

if __name__ == "__main__":
    upgrade_pip()
    upgrade_ultralytics()
    main()