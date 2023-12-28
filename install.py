# This script is under active development and is not stable, run it at your own risk.
import re
import os
import sys, subprocess 
import requests
import shutil
try:
    from tqdm import tqdm
except:
    print('tqdm not found, installation is in progress')
    os.system('pip install tqdm')
    from tqdm import tqdm
try:
    from git import Repo
except:
    print('gitpython not found, installation is in progress')
    os.system('pip install gitpython')
    from git import Repo
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

def upgrade_ultralytics():
    ultralytics_current_version = ultralytics.__version__

    ultralytics_repo_version = requests.get('https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py').content.decode('utf-8')
    ultralytics_repo_version = re.search(r"__version__\s*=\s*'([^']+)'", ultralytics_repo_version).group(1)

    if ultralytics_current_version != ultralytics_repo_version:
        print('The versions of ultralytics do not match\nAn update is in progress...')
        os.system('pip install ultralytics --upgrade')

def upgrade_pip():
    ver = os.popen('pip -V').read().split(' ')[1]
    if ver != '23.3.2':
        print('The pip version does not match the required one.\nAn update is in progress...')
        os.system("python -m pip install --upgrade pip")

def get_aimbot_current_version():
    try:
        return open('version', 'r').read()
    except:
        print('The version file was not found, we will consider it an old version of the program.')
        return '0.0.0'

def get_aimbot_version():
    return requests.get('https://raw.githubusercontent.com/SunOner/yolov8_aimbot/main/version').content.decode('utf-8')

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
    delete_files_in_folder('./logic')
    delete_files_in_folder('./media')
    try:
        os.remove('./checks.py')
    except:
        print('File checks.py is not found, continued')
        pass
    try:
        os.remove('./config.ini') # TODO: add compare with old config
    except:
        print('File config.ini is not found, continued')
        pass
    try:
        os.remove('./install.py')
    except:
        print('File install.py is not found, continued')
        pass
    try:
        os.remove('./run.py')
    except:
        print('File run.py is not found, continued')
        pass
    try:
        os.remove('./version')
    except:
        print('File version is not found, continued')
        pass

    print("Cloning repo. Please wait...")
    try:
        Repo.clone_from('https://github.com/SunOner/yolov8_aimbot.git', './temp')
    except:
        print('Folder temp is existing, deleting...')
        delete_files_in_folder('./temp')
        os.system('RMDIR temp /S')
        Repo.clone_from('https://github.com/SunOner/yolov8_aimbot.git', './temp')

    print('Moving files from ./temp/')
    shutil.move('./temp/logic/arduino.py', './logic/arduino.py')
    shutil.move('./temp/logic/capture.py', './logic/capture.py')
    shutil.move('./temp/logic/config_watcher.py', './logic/config_watcher.py')
    shutil.move('./temp/logic/game.yaml', './logic/game.yaml')
    shutil.move('./temp/logic/ghub_mouse.dll', './logic/ghub_mouse.dll')
    shutil.move('./temp/logic/keyboard.py', './logic/keyboard.py')
    shutil.move('./temp/logic/mouse.py', './logic/mouse.py')
    
    os.makedirs('./media/tests')
    shutil.move('./temp/media/tests/test_det.mp4', './media/tests/test_det.mp4')

    shutil.move('./temp/checks.py', './checks.py')
    shutil.move('./temp/config.ini', './config.ini')
    shutil.move('./temp/run.py', './run.py')
    
    copy_file = 'install_copy.py'

    with open('./temp/install.py', 'r') as source, open(copy_file, 'w') as target:
        target.write(source.read())

    cleanup_script = r"""
import os
import time
import subprocess
time.sleep(1)
cwd = os.getcwd()
os.rename('{0}\install_copy.py'.format(cwd).replace('\\\\', '\\'), '{0}\install.py'.format(cwd).replace('\\\\', '\\'))
subprocess.Popen(['python', '{0}\install.py'.format(cwd).replace('\\\\', '\\')])
os.system('RMDIR {0}\temp /S'.format(cwd).replace('\\\\', '\\'))
    """
    with open('./cleanup.py', 'w') as file:
        file.write(cleanup_script)

    subprocess.Popen(['python', './cleanup.py'])
    sys.exit()

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

def print_menu():
    print('Installed version is: {0}, latest: {1}'.format(get_aimbot_current_version(), get_aimbot_version()))

    print("1: Update YOLOv8_aimbot")
    print("2: Download Cuda 12.1")
    print("3: Download and unpack TensorRT")
    print("0: Exit")

def main():
    while True:
        print_menu()
        choice = input("Select an option: ")

        if choice == "1":
            Update_yolov8_aimbot()
        
        elif choice == "2":
            print("The file will appear in the current folder\nDownloading Cuda 12.1...")
            download_file('https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_531.14_windows.exe', './cuda_12.1.0_531.14_windows.exe')
        
        elif choice == "3":
            print("A feature in development")
        
        elif choice == "0":
            print("Exiting the program...")
            break
        
        else:
            print("Incorrect input, try again.")

if __name__ == "__main__":
    if os.path.exists(r'./cleanup.py'):
        os.remove(r'./cleanup.py')
    upgrade_pip()
    upgrade_ultralytics()
    main()