_A=None
import cv2,bettercam
from screeninfo import get_monitors
import threading,queue,ctypes,numpy as np
from logic.config_watcher import cfg
class Capture(threading.Thread):
        def __init__(A):
                super().__init__();A.daemon=True;A.name='Capture';A.print_startup_messages();A._custom_region=[];A._offset_x=_A;A._offset_y=_A;A.screen_x_center=int(cfg.detection_window_width/2);A.screen_y_center=int(cfg.detection_window_height/2);A.prev_detection_window_width=cfg.detection_window_width;A.prev_detection_window_height=cfg.detection_window_height;A.prev_bettercam_capture_fps=cfg.bettercam_capture_fps;A.frame_queue=queue.Queue(maxsize=1);A.running=True
                if cfg.Bettercam_capture:A.setup_bettercam()
                elif cfg.Obs_capture:A.setup_obs()
        def setup_bettercam(A):
                A.bc=bettercam.create(device_idx=cfg.bettercam_monitor_id,output_idx=cfg.bettercam_gpu_id,output_color='BGR',max_buffer_len=16,region=A.Calculate_screen_offset())
                if not A.bc.is_capturing:A.bc.start(region=A.Calculate_screen_offset(custom_region=[]if len(A._custom_region)<=0 else A._custom_region,x_offset=_A if A._offset_x==_A else A._offset_x,y_offset=_A if A._offset_y==_A else A._offset_y),target_fps=cfg.bettercam_capture_fps)
        def setup_obs(A):
                if cfg.Obs_camera_id=='auto':
                        B=A.find_obs_virtual_camera()
                        if B==-1:print('OBS Virtual Camera not found');exit(0)
                elif cfg.Obs_camera_id.isdigit:B=int(cfg.Obs_camera_id)
                A.obs_camera=cv2.VideoCapture(B);A.obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH,cfg.detection_window_width);A.obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT,cfg.detection_window_height);A.obs_camera.set(cv2.CAP_PROP_FPS,cfg.Obs_capture_fps)
        def run(A):
                while A.running:
                        B=A.capture_frame()
                        if B is not _A:
                                if A.frame_queue.full():A.frame_queue.get()
                                A.frame_queue.put(B)
        def capture_frame(A):
                if cfg.Bettercam_capture:return A.bc.get_latest_frame()
                elif cfg.Obs_capture:
                        B,C=A.obs_camera.read()
                        if B:return C
                        else:print('Failed to capture frame from OBS Virtual Camera');return
        def get_new_frame(A):
                try:return A.frame_queue.get(timeout=1)
                except queue.Empty:return
        def restart(A):
                if cfg.Bettercam_capture and(A.prev_detection_window_height!=cfg.detection_window_height or A.prev_detection_window_width!=cfg.detection_window_width or A.prev_bettercam_capture_fps!=cfg.bettercam_capture_fps):A.bc.stop();del A.bc;A.setup_bettercam();A.screen_x_center=cfg.detection_window_width/2;A.screen_y_center=cfg.detection_window_height/2;A.prev_detection_window_width=cfg.detection_window_width;A.prev_detection_window_height=cfg.detection_window_height;print('Capture reloaded')
        def Calculate_screen_offset(F,custom_region=[],x_offset=_A,y_offset=_A):
                E=custom_region;D=y_offset;C=x_offset
                if C is _A:C=0
                if D is _A:D=0
                if len(E)<=0:A,B=F.get_primary_display_resolution()
                else:A,B=E
                A=A/2-cfg.detection_window_width/2+C;B=B/2-cfg.detection_window_height/2-D;G=A+cfg.detection_window_width;H=B+cfg.detection_window_height;return int(A),int(B),int(G),int(H)
        def get_primary_display_resolution(C):
                B=get_monitors()
                for A in B:
                        if A.is_primary:return A.width,A.height
        def find_obs_virtual_camera(F):
                C=20;D='DSHOW'
                for B in range(C):
                        A=cv2.VideoCapture(B,cv2.CAP_DSHOW)
                        if not A.isOpened():continue
                        E=A.getBackendName()
                        if E==D:print(f"OBS Virtual Camera found at index {B}");A.release();return B
                        A.release()
                return-1
        def print_startup_messages(D):
                A=0
                try:
                        with open('./version','r')as B:C=B.read().split('\n');A=C[0].split('=')[1]
                except:print('(version file is not found)')
                print(f"Sunone Aimbot is started! (Version {A})\n\n",'Hotkeys:\n',f"[{cfg.hotkey_targeting}] - Aiming at the target\n",f"[{cfg.hotkey_exit}] - EXIT\n",f"[{cfg.hotkey_pause}] - PAUSE AIM\n",f"[{cfg.hotkey_reload_config}] - Reload config\n")
        def convert_to_circle(H,image):D=image;B,C=D.shape[:2];A=np.zeros((B,C),dtype=np.uint8);E=C//2,B//2;F=C//2,B//2;cv2.ellipse(A,E,F,angle=0,startAngle=0,endAngle=360,color=255,thickness=-1);G=cv2.merge([A,A,A]);return cv2.bitwise_and(D,G)
        def Quit(A):
                A.running=False
                if cfg.Bettercam_capture and A.bc.is_capturing:A.bc.stop()
                if cfg.Obs_capture:A.obs_camera.release()
                A.join()
capture=Capture()
capture.start()