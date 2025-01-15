_Ah='WANDB_DISABLED'
_Ag='TRAIN_ai_model'
_Af='Select model'
_Ae='debug_window_screenshot_key'
_Ad='debug_window_scale_percent'
_Ac='spawn_window_pos_y'
_Ab='spawn_window_pos_x'
_Aa='debug_window_always_on_top'
_AZ='show_history_points'
_AY='show_bScope_box'
_AX='show_target_prediction_line'
_AW='show_target_line'
_AV='show_conf'
_AU='show_labels'
_AT='show_boxes'
_AS='show_window_fps'
_AR='show_detection_speed'
_AQ='overlay_show_conf'
_AP='overlay_show_labels'
_AO='overlay_show_target_prediction_line'
_AN='overlay_show_target_line'
_AM='overlay_show_boxes'
_AL='overlay_show_borders'
_AK='AI_mouse_net'
_AJ='AI_enable_AMD'
_AI='AI_device'
_AH='AI_model_image_size'
_AG='arduino_16_bit_mouse'
_AF='arduino_baudrate'
_AE='arduino_port'
_AD='arduino_shoot'
_AC='arduino_move'
_AB='bScope_multiplier'
_AA='force_click'
_A9='triggerbot'
_A8='auto_shoot'
_A7='mouse_rzr'
_A6='mouse_ghub'
_A5='mouse_auto_aim'
_A4='mouse_lock_target'
_A3='mouse_max_speed_multiplier'
_A2='mouse_min_speed_multiplier'
_A1='mouse_fov_height'
_A0='mouse_fov_width'
_z='mouse_sensitivity'
_y='mouse_dpi'
_x='hotkey_reload_config'
_w='hotkey_pause'
_v='hotkey_exit'
_u='third_person'
_t='prediction_interval'
_s='disable_prediction'
_r='disable_headshot'
_q='hideout_targets'
_p='body_y_offset'
_o='Obs_capture_fps'
_n='Obs_capture'
_m='Bettercam_capture'
_l='bettercam_gpu_id'
_k='bettercam_monitor_id'
_j='bettercam_capture_fps'
_i='Bettercam capture'
_h='detection_window_height'
_g='detection_window_width'
_f='CONFIG'
_e='EXPORT'
_d='config'
_c='./version'
_b='./requirements.txt'
_a='Default'
_Z='show_window'
_Y='show_overlay'
_X='auto'
_W='.pt'
_V='./models'
_U='config.ini'
_T='utf-8'
_S='False'
_R='True'
_Q='HELPER'
_P='Input file'
_O='%u'
_N='cpu'
_M='Detection window'
_L='Hotkeys'
_K='Shooting'
_J=None
_I='Arduino'
_H='AI'
_G='Aim'
_F='Capture Methods'
_E='overlay'
_D=False
_C='Mouse'
_B='Debug window'
_A=True
import os,subprocess,tempfile,time,re,sys,shutil,zipfile,ctypes,configparser,threading,signal,logging
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger()
def restart():os.system('streamlit run helper.py');quit()
import streamlit as st
st.set_page_config(page_title=_Q,page_icon=':wrench:',layout='wide',initial_sidebar_state='expanded')
try:import streamlit as st,requests,numpy,bettercam,win32api,win32con,win32gui,screeninfo,asyncio,serial,cuda,onnxruntime,keyboard;from packaging import version;import numpy as np,ultralytics;from ultralytics import YOLO
except(ModuleNotFoundError,ImportError):
        with st.spinner('Installing the needed components'):
                if os.path.exists(_b):os.system('pip install -r requirements.txt')
                else:logger.info('requirements.txt file not found. Please, redownload aimbot.')
        restart()
try:import cv2
except Exception as e:logger.info(f"OpenCV import error:\n{e}")
try:from logic.config_watcher import cfg;from logic.buttons import Buttons
except ModuleNotFoundError:st.error('Some modules not found. Please, reinstall Aimbot.')
def download_file(url,filename):
        D=filename
        if os.path.exists(D):B=os.path.getsize(D)
        else:B=0
        K={'Range':f"bytes={B}-"};G=requests.get(url,headers=K,stream=_A);C=int(G.headers.get('content-length',0))+B;L=st.progress(0);A=B;M=time.time();N=st.empty();O='ab'if B>0 else'wb'
        with open(D,O)as P:
                E=M;H=A
                for I in G.iter_content(8192):
                        A+=len(I);P.write(I)
                        if C>0:L.progress(A/C)
                        F=time.time()
                        if F-E>=1:J=F-E;Q=A-H;R=Q/J if J>0 else 0;N.text(f"Speed: {R/1024:.2f} KB/s");E=F;H=A
        if C!=0 and A!=C:st.error('Error with downloading file.')
        else:st.success('File downloaded successfully.')
def install_cuda():
        st.write('Cuda 12.4 is being downloaded, and installation will begin after downloading.');download_file('https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe','./cuda_12.4.0_551.61_windows.exe')
        try:subprocess.call(f"{os.path.join(os.path.dirname(os.path.abspath(__file__)),'cuda_12.4.0_551.61_windows.exe')}")
        except OSError:st.error('The Cuda file has been downloaded but cannot be executed because administrator permission is required, please install cuda manually, the file (cuda_12.4.0_551.61_windows.exe) is available in the project folder.')
def delete_files_in_folder(folder):
        B=folder
        for C in os.listdir(B):
                A=os.path.join(B,C)
                try:
                        if os.path.isfile(A)or os.path.islink(A):os.unlink(A)
                        elif os.path.isdir(A):shutil.rmtree(A)
                except:pass
def find_cuda_path():A=[A for(B,C)in os.environ.items()if B=='PATH'for A in C.split(';')if'CUDA'in A and'12.4'in A];return A if A else _J
def get_aimbot_offline_version():
        try:
                with open(_c,'r')as E:F=E.readlines()
                A,B=0,0
                for G in F:
                        C,D=G.strip().split('=')
                        if C=='app':A=D
                        if C==_d:B=D
                return A,B
        except FileNotFoundError:st.toast('The version file was not found, we will consider it an old version of the program.');return 0,0
def get_aimbot_online_version():
        E=requests.get('https://raw.githubusercontent.com/SunOner/sunone_aimbot/main/version').content.decode(_T).split('\n');A,B=0,0
        for F in E:
                C,D=F.strip().split('=')
                if C=='app':A=D
                if C==_d:B=D
        return A,B
def upgrade_pip():
        M='--upgrade';L='install';K='pip (\\d+(?:\\.\\d+)*)';J='--version';D='-m';B='pip'
        try:
                C=subprocess.run([sys.executable,D,B,J],capture_output=_A,text=_A,check=_A,timeout=5);F=re.search(K,C.stdout)
                if not F:st.toast('Unable to determine current pip version');return
                A=F.group(1);C=subprocess.run([sys.executable,D,B,L,M,B,'--dry-run'],capture_output=_A,text=_A,check=_A,timeout=30);G=re.search(K,C.stdout)
                if G:
                        H=G.group(1)
                        if version.parse(A)<version.parse(H):
                                st.info(f"Upgrading pip from {A} to {H}");subprocess.run([sys.executable,D,B,L,M,B],check=_A,timeout=60);C=subprocess.run([sys.executable,D,B,J],capture_output=_A,text=_A,check=_A,timeout=10);I=re.search('pip (\\d+\\.\\d+\\.\\d+)',C.stdout)
                                if I:N=I.group(1);return N
                                else:return A
                        else:return A
                else:return A
        except subprocess.TimeoutExpired:st.error('Pip upgrade process timed out');return A
        except subprocess.CalledProcessError as E:st.error(f"pip: An error occurred: {E}");return A
        except Exception as E:st.error(f"pip: An unexpected error occurred: {E}");return A
def upgrade_ultralytics():
        B=ultralytics.__version__;A=requests.get('https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/__init__.py').content.decode(_T);A=re.search('__version__\\s*=\\s*\\"([^\\"]+)',A).group(1)
        if B!='8.3.40':os.system('pip install ultralytics==8.3.40');return A
        return A
def update_config(new_config_path,current_config_path=_U):logger.info('Updating config...');shutil.copy(new_config_path,current_config_path);logger.info('Config updated successfully.');return _A
def reinstall_aimbot():
        H='./main.zip';C='./temp_extract';logger.info('Checking config versions...');D=int(get_aimbot_online_version()[1]);A=get_aimbot_offline_version()
        if A:A=int(A[1])
        logger.info(f"Config current version: {A}\nConfig online version {D}");E=D!=A
        if E:logger.info('Config needs update. Will replace with new version.')
        else:logger.info('Config is up to date. Will keep current version.')
        logger.info('Deleting old files...')
        for I in['./logic','./media']:
                try:delete_files_in_folder(I)
                except:pass
        J=['./.gitattributes','./.gitignore','./LICENSE','./README.md','./helper.py','run_helper.bat','./run.py','run_ai.bat',_b,'./launcher.py','window_names.txt',_c]
        for B in J:
                try:os.remove(B)
                except:logger.info(f"{B} not found, continued")
        logger.info('Downloading repo. Please wait...');download_file('https://github.com/SunOner/sunone_aimbot/archive/refs/heads/main.zip','main.zip');logger.info('Unpacking...')
        with zipfile.ZipFile(H,'r')as K:K.extractall(C)
        logger.info('Moving files...')
        for(L,N,M)in os.walk(C):
                for B in M:
                        F=os.path.join(L,B);G=os.path.join('.',os.path.relpath(F,'./temp_extract/sunone_aimbot-main'));os.makedirs(os.path.dirname(G),exist_ok=_A)
                        if B!=_U or E:shutil.move(F,G)
        logger.info('Cleaning up...');os.remove(H);shutil.rmtree(C);logger.info('Reinstallation complete. Restarting...');restart()
def torch_check():
        try:import torch;return torch.cuda.is_available()
        except ModuleNotFoundError:return
def tensorrt_version_check():
        try:import tensorrt as A;return _A,A.__version__
        except ModuleNotFoundError:return _D,0
if'ultralytics_version'not in st.session_state:
        with st.spinner('Checking for ultralytics updates...'):st.session_state.ultralytics_version=upgrade_ultralytics()
if'pip_version'not in st.session_state:
        with st.spinner('Checking for pip updates...'):st.session_state.pip_version=upgrade_pip()
if'aimbot_versions'not in st.session_state:
        with st.spinner('Checking Aimbot versions...'):st.session_state.aimbot_versions=get_aimbot_offline_version(),get_aimbot_online_version()
if'cuda'not in st.session_state:
        with st.spinner('Searching CUDA...'):st.session_state.cuda=find_cuda_path()
if'python_version'not in st.session_state:
        with st.spinner('Checking Python version...'):st.session_state.python_version=sys.version_info
if'torch_gpu'not in st.session_state:
        with st.spinner('Checking Torch GPU support...'):st.session_state.torch_gpu_support=torch_check()
if'tensorrt_version'not in st.session_state:
        with st.spinner('Checking Tensorrt...'):st.session_state.tensorrt_version=tensorrt_version_check()
if'current_tab'not in st.session_state:st.session_state.current_tab=_Q
with st.sidebar:
        tabs=[_Q,_e,_f,'TRAIN','TESTS'];st.session_state.current_tab=st.radio(label='**Select tab**',options=tabs,horizontal=_D,label_visibility='visible',key='radio_global_tabs')
        if st.button(label='Run Aimbot',key='sidebar_run_aimbot_button'):os.system('python run.py')
        exit_button_col,send_buttons_col=st.columns(2);send_c_w=_D
        with send_buttons_col:send_c_w=st.toggle(label='Send ctrl+w',value=_A,key='sidebar_send_c_w_toggle',help="Use the automatic keyboard shortcut 'ctrl+w' to close the tab.")
        with exit_button_col:
                if st.button(label='Exit'):
                        if send_c_w==_A:keyboard.press_and_release('ctrl+w')
                        os.kill(os.getpid(),signal.SIGTERM)
if st.session_state.current_tab==_Q:
        st.title('Helper')
        if not st.session_state.python_version.major==3 and st.session_state.python_version.minor==11 and st.session_state.python_version.micro==6:st.error(f"❌ Running not from Python 3.11.6!")
        st.subheader('Aimbot',divider=_A);aimbot_version_col,aimbot_reinstall_button=st.columns(2)
        with aimbot_version_col:st.markdown(f"Installed Aimbot version: {st.session_state.aimbot_versions[0][0]}  \\\n Github version: {st.session_state.aimbot_versions[1][0]}")
        if'show_confirm'not in st.session_state:st.session_state.show_confirm=_D
        with aimbot_reinstall_button:
                if not st.session_state.show_confirm:
                        if st.button(label='Update/Install Sunone Aimbot',key='reinstall_aimbot_button'):st.session_state.show_confirm=_A;st.rerun()
                else:
                        st.write('Are you sure you want to reinstall?');col1,col2=st.columns(2)
                        with col1:
                                if st.button('Yes',key='confirm_yes'):reinstall_aimbot();st.session_state.show_confirm=_D
                        with col2:
                                if st.button('No',key='confirm_no'):st.session_state.show_confirm=_D;st.rerun()
        st.subheader('CUDA',divider=_A);cuda_version_col,cuda_install_button=st.columns(2)
        with cuda_version_col:
                if st.session_state.cuda is not _J:st.markdown('✅ CUDA 12.4 FOUND')
                else:st.markdown('❌ CUDA 12.4 NOT FOUND')
        with cuda_install_button:
                if st.button(label='Download CUDA 12.4',key='Download_cuda_button'):install_cuda()
        st.subheader('Torch',divider=_A);torch_support_col,torch_reinstall_button=st.columns(2)
        with torch_support_col:
                if st.session_state.torch_gpu_support is not _J:
                        if st.session_state.torch_gpu_support==_A:st.markdown('✅ Torch is installed with GPU support')
                        else:st.markdown('❌ Torch is installed without GPU support, reinstall Torch.')
                else:st.markdown('❌ Torch is not installed, install Torch.')
        with torch_reinstall_button:
                if st.button(label='Reinstall Torch',key='install_torch_button'):
                        if not find_cuda_path():st.error('Please, download and install CUDA first.')
                        else:
                                with st.spinner('Reinstalling Torch. After installation, the application will restart and a new window will open.'):os.system('pip uninstall torch torchvision torchaudio -y ');os.system('pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124');restart()
        st.subheader('TensorRT',divider=_A);tensorrt_ver_col,tensorrt_reinstall_col=st.columns(2)
        with tensorrt_ver_col:
                if st.session_state.tensorrt_version[0]==_A:st.markdown(f"✅ TensorRT version: {st.session_state.tensorrt_version[1]}")
                else:st.markdown('❌ TensorRT not installed')
        with tensorrt_reinstall_col:
                if st.button(label='Reinstall TensorRT',key='install_tensorrt_button'):
                        if find_cuda_path():
                                with st.spinner('Installing TensorRT. After installation, the application will restart and a new window will open.'):os.system('pip uninstall tensorrt tensorrt-bindings tensorrt-cu12 tensorrt-cu12_bindings tensorrt-cu12_libs tensorrt-libs -y');os.system('pip install tensorrt');restart()
                        else:st.error('❌ Please, download and install CUDA first.')
elif st.session_state.current_tab==_e:
        st.title(body='Model exporter');models=[]
        for(root,dirs,files)in os.walk(_V):
                for file in files:
                        if file.endswith(_W):models.append(file)
        selected_model=st.selectbox(label='**Select model to export.**',options=models,key='export_selected_model_selectbox');image_size=st.radio(label='**Select model size**',options=(320,480,640),help='The size of the model image must be correct.',key='export_image_size_radio')
        if st.button(label='Export model',key='export_export_model_button'):
                yolo_model=YOLO(f"./models/{selected_model}")
                with st.spinner(text=f"Model {selected_model} exporting..."):yolo_model.export(format='engine',imgsz=image_size,half=_A,device=0);st.success('Model exported!',icon='✅')
elif st.session_state.current_tab==_f:
        st.title(body='Config Editor')
        def load_config():A=configparser.ConfigParser();A.read('./config.ini');return A
        def save_config(config):
                F=config;G=_U
                try:
                        with open(G,'r')as A:H=A.readlines()
                        with open(G,'w')as A:
                                C=_J
                                for B in H:
                                        D=B.strip()
                                        if D.startswith('[')and D.endswith(']'):C=D[1:-1];A.write(B)
                                        elif'='in B and not D.startswith('#')and C:
                                                E,K=map(str.strip,B.split('=',1))
                                                if F.has_option(C,E):I=F.get(C,E);A.write(f"{E} = {I}\n")
                                                else:A.write(B)
                                        else:A.write(B)
                        st.success('Config saved successfully!')
                except Exception as J:st.error(f"Error writing to config file: {J}")
        config=load_config();st.subheader(body=_M,divider=_A);detection_window_width=st.number_input(label='Detection window width',value=config.getint(_M,_g),key='config_detection_window_width');detection_window_height=st.number_input(label='Detection window height',value=config.getint(_M,_h),key='config_detection_window_height');config.set(_M,_g,str(detection_window_width));config.set(_M,_h,str(detection_window_height));st.subheader(_F,divider=_A);selected_capture_method=st.radio(label='Capture Method',options=[_i,'OBS'],key='config_selected_capture_method')
        if selected_capture_method==_i:bettercam_capture_fps=st.number_input(label='Bettercam capture FPS',value=config.getint(_F,_j),key='config_bettercam_capture_fps');bettercam_monitor_id=st.number_input(label='Bettercam monitor ID',value=config.getint(_F,_k),key='config_bettercam_monitor_id');bettercam_gpu_id=st.number_input(label='Bettercam GPU ID',value=config.getint(_F,_l),key='config_bettercam_gpu_id');config.set(_F,_m,_R);config.set(_F,_n,_S);config.set(_F,_j,str(bettercam_capture_fps));config.set(_F,_k,str(bettercam_monitor_id));config.set(_F,_l,str(bettercam_gpu_id))
        else:obs_camera_id=st.selectbox(label='Obs camera ID',options=[_X,'0','1','2','3','4','5','6','7','8','9','10'],index=0,key='config_obs_camera_id');obs_capture_fps=st.number_input(label='Obs capture FPS',value=config.getint(_F,_o),key='config_obs_capture_fps');config.set(_F,_m,_S);config.set(_F,_n,_R);config.set(_F,'Obs_camera_id',obs_camera_id);config.set(_F,_o,str(obs_capture_fps))
        st.subheader(_G,divider=_A);body_y_offset=st.slider(label='Body Y offset',min_value=-.99,max_value=.99,value=config.getfloat(_G,_p),key='config_body_y_offset');hideout_targets=st.checkbox(label='Hideout targets',value=config.getboolean(_G,_q),key='config_hideout_targets');disable_headshot=st.checkbox(label='Disable headshot',value=config.getboolean(_G,_r),key='config_disable_headshot');disable_prediction=st.checkbox(label='Disable prediction',value=config.getboolean(_G,_s),key='config_disable_prediction')
        if not disable_prediction:prediction_interval=st.number_input(label='Prediction interval',value=config.getfloat(_G,_t),format='%.1f',min_value=.1,max_value=5.,step=.1,key='config_prediction_interval');config.set(_G,_s,str(disable_prediction));config.set(_G,_t,str(prediction_interval))
        third_person=st.checkbox(label='Third person mode',value=config.getboolean(_G,_u),key='config_third_person');config.set(_G,_p,str(body_y_offset));config.set(_G,_q,str(hideout_targets));config.set(_G,_r,str(disable_headshot));config.set(_G,_u,str(third_person));st.subheader(_L,divider=_A);hotkey_options=[]
        for i in Buttons.KEY_CODES:hotkey_options.append(str(i))
        hotkey_targeting=st.multiselect(label='Hotkey targeting',options=hotkey_options,default=cfg.hotkey_targeting_list,key='config_hotkey_targeting');hotkey_exit=st.selectbox(label='Hotkey exit',options=hotkey_options,index=hotkey_options.index(config.get(_L,_v)),key='config_hotkey_exit');hotkey_pause=st.selectbox(label='Hotkey pause',options=hotkey_options,index=hotkey_options.index(config.get(_L,_w)),key='config_hotkey_pause');hotkey_reload_config=st.selectbox(label='Hotkey reload config',options=hotkey_options,index=hotkey_options.index(config.get(_L,_x)),key='config_hotkey_reload_config');targeting_hotkeys_list=','.join(hotkey_targeting);config.set(_L,'hotkey_targeting',targeting_hotkeys_list);config.set(_L,_v,hotkey_exit);config.set(_L,_w,hotkey_pause);config.set(_L,_x,hotkey_reload_config);st.subheader(_C,divider=_A);mouse_dpi=st.number_input(label='Mouse DPI',min_value=100,step=100,value=config.getint(_C,_y),key='config_mouse_dpi');mouse_sensitivity=st.number_input(label='Mouse sensitivity',min_value=.1,value=config.getfloat(_C,_z),key='config_mouse_sensitivity');mouse_fov_width=st.number_input(label='Mouse FOV width',value=config.getint(_C,_A0),key='config_mouse_fov_width');mouse_fov_height=st.number_input(label='Mouse FOV height',value=config.getint(_C,_A1),key='config_mouse_fov_height');mouse_min_speed_multiplier=st.number_input(label='Mouse minimum speed multiplier',value=config.getfloat(_C,_A2),key='config_mouse_min_speed_multiplier');mouse_max_speed_multiplier=st.number_input(label='Mouse maximum speed multiplier',value=config.getfloat(_C,_A3),key='config_mouse_max_speed_multiplier');mouse_lock_target=st.checkbox(label='Mouse lock target',value=config.getboolean(_C,_A4),key='config_mouse_lock_target');mouse_auto_aim=st.checkbox(label='Mouse auto aim',value=config.getboolean(_C,_A5),key='config_mouse_auto_aim');mouse_ghub=st.checkbox(label='Mouse GHUB',value=config.getboolean(_C,_A6),key='config_mouse_ghub');mouse_rzr=st.checkbox(label='Mouse Razer',value=config.getboolean(_C,_A7),key='config_mouse_rzr');config.set(_C,_y,str(mouse_dpi));config.set(_C,_z,str(mouse_sensitivity));config.set(_C,_A0,str(mouse_fov_width));config.set(_C,_A1,str(mouse_fov_height));config.set(_C,_A2,str(mouse_min_speed_multiplier));config.set(_C,_A3,str(mouse_max_speed_multiplier));config.set(_C,_A4,str(mouse_lock_target));config.set(_C,_A5,str(mouse_auto_aim));config.set(_C,_A6,str(mouse_ghub));config.set(_C,_A7,str(mouse_rzr));st.subheader(_K,divider=_A);auto_shoot=st.checkbox(label='Auto shoot',value=config.getboolean(_K,_A8),key='config_auto_shoot');triggerbot=st.checkbox(label='Triggerbot',value=config.getboolean(_K,_A9),key='config_triggerbot');force_click=st.checkbox(label='Force click',value=config.getboolean(_K,_AA),key='config_force_click');bScope_multiplier=st.number_input(label='bScope multiplier',step=.1,value=config.getfloat(_K,_AB),key='config_bScope_multiplier');config.set(_K,_A8,str(auto_shoot));config.set(_K,_A9,str(triggerbot));config.set(_K,_AA,str(force_click));config.set(_K,_AB,str(bScope_multiplier));st.subheader(_I,divider=_A);arduino_move=st.checkbox(label='Arduino move',value=config.getboolean(_I,_AC),key='config_arduino_move');arduino_shoot=st.checkbox(label='Arduino shoot',value=config.getboolean(_I,_AD),key='config_arduino_shoot')
        if arduino_move or arduino_shoot:arduino_port=st.text_input(label='Arduino port',value=config.get(_I,_AE),key='config_arduino_port');baudrates=[2400,4800,9600,19200,31250,38400,57600,74880,115200];arduino_baudrate=st.selectbox(label='Arduino baudrate',options=baudrates,index=baudrates.index(config.getint(_I,_AF)),key='config_arduino_baudrate');arduino_16_bit_mouse=st.checkbox(label='Arduino 16 bit mouse',value=config.getboolean(_I,_AG),key='config_arduino_16_bit_mouse');config.set(_I,_AC,str(arduino_move));config.set(_I,_AD,str(arduino_shoot));config.set(_I,_AE,arduino_port);config.set(_I,_AF,str(arduino_baudrate));config.set(_I,_AG,str(arduino_16_bit_mouse))
        st.subheader(_H,divider=_A);models=[]
        for(root,dirs,files)in os.walk(_V):
                for file in files:
                        if file.endswith(_W)or file.endswith('.engine'):models.append(file)
        AI_model_name=st.selectbox(label='AI model',options=models,key='config_AI_model_name');imgsz=[320,480,640];AI_model_image_size=st.selectbox(label='AI model image size',options=imgsz,index=imgsz.index(config.getint(_H,_AH)),key='config_AI_model_image_size');AI_conf=st.slider(label='AI confidence',min_value=.01,max_value=.99,value=config.getfloat(_H,'AI_conf'),key='config_AI_conf');devices=[_N,'0','1','2','3','4','5'];AI_device=st.selectbox(label='AI device',options=devices,index=devices.index(config.get(_H,_AI)),key='config_AI_device');AI_enable_AMD=st.checkbox(label='AI enable AMD',value=config.getboolean(_H,_AJ),key='config_AI_enable_AMD');AI_mouse_net=st.checkbox(label='AI mouse net',value=config.getboolean(_H,_AK),key='config_AI_mouse_net');config.set(_H,'AI_model_name',AI_model_name);config.set(_H,_AH,str(AI_model_image_size));config.set(_H,'AI_conf',str(AI_conf));config.set(_H,_AI,AI_device);config.set(_H,_AJ,str(AI_enable_AMD));config.set(_H,_AK,str(AI_mouse_net));st.subheader('Overlay',divider=_A);show_overlay=st.toggle(label='Show overlay',value=config.getboolean(_E,_Y),key='config_show_overlay')
        if show_overlay:overlay_show_borders=st.checkbox(label='Overlay show borders',value=config.getboolean(_E,_AL),key='config_overlay_show_borders');overlay_show_boxes=st.checkbox(label='Overlay show boxes',value=config.getboolean(_E,_AM),key='config_overlay_show_boxes');overlay_show_target_line=st.checkbox(label='Overlay show target line',value=config.getboolean(_E,_AN),key='config_overlay_show_target_line');overlay_show_target_prediction_line=st.checkbox(label='Overlay show target prediction line',value=config.getboolean(_E,_AO),key='config_overlay_show_target_prediction_line');overlay_show_labels=st.checkbox(label='Overlay show labels',value=config.getboolean(_E,_AP),key='config_overlay_show_labels');overlay_show_conf=st.checkbox(label='Overlay show confidence',value=config.getboolean(_E,_AQ),key='config_overlay_show_conf');config.set(_E,_Y,_R);config.set(_E,_AL,str(overlay_show_borders));config.set(_E,_AM,str(overlay_show_boxes));config.set(_E,_AN,str(overlay_show_target_line));config.set(_E,_AO,str(overlay_show_target_prediction_line));config.set(_E,_AP,str(overlay_show_labels));config.set(_E,_AQ,str(overlay_show_conf))
        else:config.set(_E,_Y,_S)
        st.subheader(_B,divider=_A);show_window=st.toggle(label='Show debug window',value=config.getboolean(_B,_Z),key='config_show_window')
        if show_window:show_detection_speed=st.checkbox(label='Show detection speed',value=config.getboolean(_B,_AR),key='config_show_detection_speed');show_window_fps=st.checkbox(label='Show window FPS',value=config.getboolean(_B,_AS),key='config_show_window_fps');show_boxes=st.checkbox(label='Show boxes',value=config.getboolean(_B,_AT),key='config_show_boxes');show_labels=st.checkbox(label='Show labels',value=config.getboolean(_B,_AU),key='config_show_labels');show_conf=st.checkbox(label='Show confidence',value=config.getboolean(_B,_AV),key='config_show_conf');show_target_line=st.checkbox(label='Show target line',value=config.getboolean(_B,_AW),key='config_show_target_line');show_target_prediction_line=st.checkbox(label='Show target prediction line',value=config.getboolean(_B,_AX),key='config_show_target_prediction_line');show_bScope_box=st.checkbox(label='Show bScope box',value=config.getboolean(_B,_AY),key='config_show_bScope_box');show_history_points=st.checkbox(label='Show history points',value=config.getboolean(_B,_AZ),key='config_show_history_points');debug_window_always_on_top=st.checkbox(label='Debug window always on top',value=config.getboolean(_B,_Aa),key='config_debug_window_always_on_top');spawn_window_pos_x=st.number_input(label='Spawn window position X',value=config.getint(_B,_Ab),key='config_spawn_window_pos_x');spawn_window_pos_y=st.number_input(label='Spawn window position Y',value=config.getint(_B,_Ac),key='config_spawn_window_pos_y');debug_window_scale_percent=st.number_input(label='Debug window scale percent:',value=config.getint(_B,_Ad),key='config_debug_window_scale_percent');debug_window_screenshot_key=st.selectbox(label='Screenshot key',options=hotkey_options,index=hotkey_options.index(config.get(_B,_Ae)),key='config_debug_window_screenshot_key');config.set(_B,_Z,_R);config.set(_B,_AR,str(show_detection_speed));config.set(_B,_AS,str(show_window_fps));config.set(_B,_AT,str(show_boxes));config.set(_B,_AU,str(show_labels));config.set(_B,_AV,str(show_conf));config.set(_B,_AW,str(show_target_line));config.set(_B,_AX,str(show_target_prediction_line));config.set(_B,_AY,str(show_bScope_box));config.set(_B,_AZ,str(show_history_points));config.set(_B,_Aa,str(debug_window_always_on_top));config.set(_B,_Ab,str(spawn_window_pos_x));config.set(_B,_Ac,str(spawn_window_pos_y));config.set(_B,_Ad,str(debug_window_scale_percent));config.set(_B,_Ae,str(debug_window_screenshot_key))
        else:config.set(_B,_Z,_S)
        with st.sidebar:
                if st.button('Save Config',key='sidebar_config_save_button'):save_config(config)
elif st.session_state.current_tab=='TRAIN':
        st.title('Train model');resume=_D;pretrained_models=['yolov8n.pt','yolov8s.pt','yolov8m.pt','yolov10n.pt','yolov10s.pt','yolov10m.pt','yolo11n.pt','yolo11s.pt','yolo11m.pt'];user_trained_models=st.checkbox(label='Use user pretrained models',value=_D,key='TRAIN_user_trained_models')
        if user_trained_models:
                last_pt_files=[];root_folder='runs\\detect'
                for(root,dirs,files)in os.walk(root_folder):
                        for file in files:
                                if file=='last.pt':last_pt_files.append(os.path.join(root,file))
                selected_model_path=st.selectbox(label=_Af,options=last_pt_files,key=_Ag);resume=st.checkbox(label='Resume training',value=_D,key='TRAIN_resume')
        else:selected_model_path=st.selectbox(label=_Af,options=pretrained_models,index=4,key=_Ag)
        if not resume:
                data_yaml=st.text_input(label='Path to the dataset configuration file',value='logic/game.yaml',key='TRAIN_data_yaml');epochs=st.number_input(label='Epochs',value=80,format=_O,min_value=10,step=10,key='TRAIN_epochs');img_size=st.number_input(label='Image size',value=640,format=_O,min_value=120,max_value=1280,step=10,key='TRAIN_img_size');use_cache=st.checkbox(label='Enables caching of dataset images in memory',value=_D,key='TRAIN_use_cache');augment=st.checkbox(label='Use augmentation',value=_A)
                if augment:augment_degrees=st.number_input(label='Degrees',format=_O,value=5,min_value=-180,max_value=180,step=5,key='TRAIN_augment_degrees');augment_flipud=st.number_input(label='Flipud',format='%.1f',value=.2,min_value=.0,max_value=1.,step=.1,key='TRAIN_augment_flipud')
        input_devices=[_N,'0','1','2','3','4','5'];train_device=st.selectbox(label='Specifies the computational device for training',options=input_devices,index=1,help='cpu - Train on processor, 0-5 GPU ID for training.',key='TRAIN_train_device')
        if train_device!=_N:train_device=int(train_device)
        batch_size_options=[_X,'4','8','16','32','64','128','256'];batch_size=st.selectbox(label='Batch size',options=batch_size_options,index=0,key='TRAIN_batch_size')
        if batch_size==_X:batch_size='-1'
        batch_size=int(batch_size);wandb=st.checkbox(label='Force disable WANDB logger',value=_A,key='TRAIN_wandb')
        if wandb:os.environ[_Ah]='true'
        else:os.environ[_Ah]='false'
        if st.button(label='Start',key='TRAIN_start_train_button'):
                with st.spinner('Train in process, check terminal window.'):
                        with tempfile.NamedTemporaryFile(delete=_D,suffix='.py')as temp_script:
                                script_content=f"""
if __name__ == '__main__':
    from ultralytics import YOLO
    yolo_model = YOLO(r'{selected_model_path}')
    yolo_model.train(
                    device={train_device},
                    batch={batch_size},
                    resume={resume}
                """
                                if not resume:script_content+=f""",
                    data='{data_yaml}',
                    epochs={epochs},
                    imgsz={img_size},
                    cache={use_cache},
                    augment={augment},
                    degrees={augment_degrees},
                    flipud={augment_flipud}
                    """
                                script_content+='\n    )';temp_script.write(script_content.encode(_T));temp_script_path=temp_script.name
                        if os.name=='nt':os.system(f"start cmd /k python {temp_script_path}")
                        else:os.system(f"xterm -e python {temp_script_path}")
                        st.success('Training started in a new terminal window.')
elif st.session_state.current_tab=='TESTS':
        def test_detections(input_model,source_method=_a,video_source=_J,TOPMOST=_A,model_image_size=_J,input_device=0,input_delay=30,resize_factor=100,ai_conf=.2):
                L='uploaded_video.mp4';K='error';F=resize_factor;E=input_model;D=source_method;A=video_source
                if E is _J:return K,'Model not selected'
                M=st.session_state.torch_gpu_support
                if not M:return K,'Cuda is not supported'
                if D==_a:A='media/tests/test_det.mp4'
                elif D==_P:
                        A=A.getvalue()
                        with open(L,'wb')as N:N.write(A)
                        A=L
                B=cv2.VideoCapture(A)
                if not B.isOpened():st.error('Error: Could not open video.');return
                C='Detections test';cv2.namedWindow(C)
                if TOPMOST:O=win32gui.FindWindow(_J,C);win32gui.SetWindowPos(O,win32con.HWND_TOPMOST,100,100,200,200,0)
                G=YOLO(f"models/{E}",task='detect')
                while B.isOpened():
                        P,H=B.read()
                        if P:
                                Q=G(H,stream=_D,show=_D,imgsz=model_image_size,device=input_device,verbose=_D,conf=ai_conf);I=Q[0].plot();cv2.putText(I,"When life gives you lemons, don't make lemonade.",(10,40),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),1,cv2.LINE_AA);R,S=H.shape[:2];T=int(R*F/100);U=int(S*F/100);J=U,T;cv2.resizeWindow(C,J);V=cv2.resize(I,J,cv2.INTER_NEAREST);cv2.imshow(C,V)
                                if cv2.waitKey(input_delay)&255==ord('q'):break
                        else:break
                B.release();cv2.destroyAllWindows()
                if D==_P:
                        try:os.remove('./uploaded_video.mp4')
                        except:pass
                del G
        st.title('Tests');models=[]
        for(root,dirs,files)in os.walk(_V):
                for file in files:
                        if file.endswith(_W)or file.endswith('.engine'):models.append(file)
        ai_model=st.selectbox(label='AI Model',options=models,key='TESTS_ai_model_selectbox',help="Put model to './models' path.");model_image_sizes=[320,480,640];model_size=st.selectbox(label='AI Model image size',options=model_image_sizes,key='TESTS_model_size_selectbox',index=2);methods=[_a,_P];video_source_method=st.selectbox(label='Select video input method',options=methods,index=0,key='TESTS_video_source_method_selectbox');TOPMOST=st.toggle(label='Test window on top',value=_A,key='tests_topmost');test_devices=[_N,'0','1','2','3','4','5'];device=st.selectbox(label='Device',options=test_devices,index=1,key='tests_test_devices')
        if device!=_N:device=int(device)
        cv2_delay=st.number_input(label='CV2 frame wait delay',min_value=1,max_value=120,step=1,format=_O,value=30,key='TESTS_cv2_delay_number_input');cv2_resize=st.number_input(label='Resize test window',min_value=10,max_value=100,value=80,step=1,format=_O,key='ESTS_cv2_resize_number_input');ai_conf=st.number_input(label='Minimum confidence threshold',min_value=.01,max_value=.99,step=.01,format='%.2f',value=.2,key='tests_ai_conf');input_video=_J
        if video_source_method==_P:video_source_input_file=st.file_uploader(label='Import video file',accept_multiple_files=_D,type=['mp4'],key='TESTS_input_file_video_source_input_file');input_video=video_source_input_file
        if st.button(label='Test detections',key='TESTS_text_detections_button'):
                if video_source_method in methods:
                        if input_video==_J and video_source_method==_P:st.error('Video source not found.')
                        else:test_detections(input_model=ai_model,source_method=video_source_method,video_source=input_video,model_image_size=model_size,TOPMOST=TOPMOST,input_delay=cv2_delay,input_device=device,resize_factor=cv2_resize,ai_conf=ai_conf)
                else:st.error('Select correct video input method.')