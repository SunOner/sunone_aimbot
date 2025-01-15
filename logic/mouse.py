_B=False
_A=None
import torch,win32con,win32api,torch.nn as nn,time,math,os
from logic.config_watcher import cfg
from logic.visual import visuals
from logic.shooting import shooting
from logic.buttons import Buttons
if cfg.mouse_rzr:from logic.rzctl import RZCONTROL
if cfg.arduino_move or cfg.arduino_shoot:from logic.arduino import arduino
class Mouse_net(nn.Module):
        def __init__(A,arch):B=arch;super(Mouse_net,A).__init__();A.fc1=nn.Linear(10,128,B);A.fc2=nn.Linear(128,128,B);A.fc3=nn.Linear(128,64,B);A.fc4=nn.Linear(64,2,B)
        def forward(A,x):x=torch.relu(A.fc1(x));x=torch.relu(A.fc2(x));x=torch.relu(A.fc3(x));x=A.fc4(x);return x
class MouseThread:
        def __init__(A):
                A.dpi=cfg.mouse_dpi;A.mouse_sensitivity=cfg.mouse_sensitivity;A.fov_x=cfg.mouse_fov_width;A.fov_y=cfg.mouse_fov_height;A.disable_prediction=cfg.disable_prediction;A.prediction_interval=cfg.prediction_interval;A.bScope_multiplier=cfg.bScope_multiplier;A.screen_width=cfg.detection_window_width;A.screen_height=cfg.detection_window_height;A.center_x=A.screen_width/2;A.center_y=A.screen_height/2;A.prev_x=0;A.prev_y=0;A.prev_time=_A;A.max_distance=math.sqrt(A.screen_width**2+A.screen_height**2)/2;A.min_speed_multiplier=cfg.mouse_min_speed_multiplier;A.max_speed_multiplier=cfg.mouse_max_speed_multiplier;A.prev_distance=_A;A.speed_correction_factor=.1;A.bScope=_B;A.arch=A.get_arch()
                if cfg.mouse_ghub:from logic.ghub import gHub;A.ghub=gHub
                if cfg.mouse_rzr:
                        B='rzctl.dll';C=os.path.dirname(os.path.abspath(__file__));D=os.path.join(C,B);A.rzr=RZCONTROL(D)
                        if not A.rzr.init():print('Failed to initialize rzctl')
                if cfg.AI_mouse_net:
                        A.device=torch.device(A.arch);A.model=Mouse_net(arch=A.arch).to(A.device)
                        try:A.model.load_state_dict(torch.load('mouse_net.pth',map_location=A.device))
                        except Exception as E:print(E);print('Please train mouse_net model, or download latest trained mouse_net.pth model from repository and place in base folder. Instruction here: https://github.com/SunOner/mouse_net');exit()
                        A.model.eval()
        def get_arch(B):
                A='cpu'
                if cfg.AI_enable_AMD:return f"hip:{cfg.AI_device}"
                if A in cfg.AI_device:return A
                return f"cuda:{cfg.AI_device}"
        def process_data(A,data):
                B,C,E,F,D=data
                if cfg.AI_mouse_net==_B:
                        if cfg.show_window and cfg.show_target_line or cfg.show_overlay and cfg.show_target_line:visuals.draw_target_line(B,C,D)
                A.bScope=A.check_target_in_scope(B,C,E,F,A.bScope_multiplier)if cfg.auto_shoot or cfg.triggerbot else _B;A.bScope=cfg.force_click or A.bScope
                if not A.disable_prediction:
                        G=time.time();B,C=A.predict_target_position(B,C,G)
                        if cfg.AI_mouse_net==_B:
                                if cfg.show_window and cfg.show_target_prediction_line or cfg.show_overlay and cfg.show_target_prediction_line:visuals.draw_predicted_position(B,C,D)
                B,C=A.calc_movement(B,C,D)
                if cfg.show_window and cfg.show_history_points or cfg.show_overlay and cfg.show_history_points:visuals.draw_history_point_add_point(B,C)
                shooting.queue.put((A.bScope,A.get_shooting_key_state()));A.move_mouse(B,C)
        def predict_target_position(A,target_x,target_y,current_time):
                H=current_time;C=target_y;B=target_x
                if A.prev_time is _A:A.prev_time=H;A.prev_x=B;A.prev_y=C;A.prev_velocity_x=0;A.prev_velocity_y=0;return B,C
                D=H-A.prev_time;I=(B-A.prev_x)/D;J=(C-A.prev_y)/D;L=(I-A.prev_velocity_x)/D;M=(J-A.prev_velocity_y)/D;F=D*A.prediction_interval;K=math.sqrt((B-A.prev_x)**2+(C-A.prev_y)**2);G=max(.1,min(1,1/(K+1)))
                if A.prev_distance is not _A:N=abs(K-A.prev_distance);E=1+N/A.max_distance*A.speed_correction_factor
                else:E=1.
                O=B+I*F*G*E+.5*L*F**2*G*E;P=C+J*F*G*E+.5*M*F**2*G*E;A.prev_x,A.prev_y=B,C;A.prev_velocity_x,A.prev_velocity_y=I,J;A.prev_time=H;A.prev_distance=K;return O,P
        def calculate_speed_multiplier(A,distance):
                B=distance;D=min(B/A.max_distance,1);C=A.min_speed_multiplier+(A.max_speed_multiplier-A.min_speed_multiplier)*(1-D)
                if A.prev_distance is not _A:E=abs(B-A.prev_distance);F=1+E/A.max_distance*A.speed_correction_factor;return C*F
                return C
        def calc_movement(A,target_x,target_y,target_cls):
                G=target_y;F=target_x
                if not cfg.AI_mouse_net:
                        H=F-A.center_x;I=G-A.center_y;K=math.sqrt(H**2+I**2);J=A.calculate_speed_multiplier(K);L=A.fov_x/A.screen_width;M=A.fov_y/A.screen_height;N=H*L;O=I*M;B=.8
                        if not hasattr(A,'last_move_x'):A.last_move_x,A.last_move_y=0,0
                        C=B*N+(1-B)*A.last_move_x;D=B*O+(1-B)*A.last_move_y;A.last_move_x,A.last_move_y=C,D;C=C/360*(A.dpi*(1/A.mouse_sensitivity))*J;D=D/360*(A.dpi*(1/A.mouse_sensitivity))*J;return C,D
                else:
                        P=[A.screen_width,A.screen_height,A.center_x,A.center_y,A.dpi,A.mouse_sensitivity,A.fov_x,A.fov_y,F,G];Q=torch.tensor(P,dtype=torch.float32).to(A.device)
                        with torch.no_grad():E=A.model(Q).cpu().numpy()
                        if cfg.show_window and cfg.show_target_prediction_line or cfg.show_overlay and cfg.show_target_prediction_line:visuals.draw_predicted_position(E[0]+A.center_x,E[1]+A.center_y,target_cls)
                        return E[0],E[1]
        def move_mouse(A,x,y):
                x=x if x is not _A else 0;y=y if y is not _A else 0
                if x!=0 and y!=0:
                        C=A.get_shooting_key_state();B=cfg.mouse_auto_aim;D=cfg.triggerbot
                        if C and not B and not D or B:
                                x,y=int(x),int(y)
                                if not cfg.mouse_ghub and not cfg.arduino_move and not cfg.mouse_rzr:win32api.mouse_event(win32con.MOUSEEVENTF_MOVE,x,y,0,0)
                                elif cfg.mouse_ghub and not cfg.arduino_move and not cfg.mouse_rzr:A.ghub.mouse_xy(x,y)
                                elif cfg.arduino_move and not cfg.mouse_rzr:arduino.move(x,y)
                                elif cfg.mouse_rzr:A.rzr.mouse_move(x,y,True)
        def get_shooting_key_state(D):
                for C in cfg.hotkey_targeting_list:
                        A=Buttons.KEY_CODES.get(C.strip())
                        if A is not _A:
                                B=win32api.GetKeyState(A)if cfg.mouse_lock_target else win32api.GetAsyncKeyState(A)
                                if B<0 or B==1:return True
                return _B
        def check_target_in_scope(A,target_x,target_y,target_w,target_h,reduction_factor):
                D=reduction_factor;C=target_y;B=target_x;E=target_w*D/2;F=target_h*D/2;G=B-E;H=B+E;I=C-F;J=C+F;K=A.center_x>G and A.center_x<H and A.center_y>I and A.center_y<J
                if cfg.show_window and cfg.show_bScope_box:visuals.draw_bScope(G,H,I,J,K)
                return K
        def update_settings(A):A.dpi=cfg.mouse_dpi;A.mouse_sensitivity=cfg.mouse_sensitivity;A.fov_x=cfg.mouse_fov_width;A.fov_y=cfg.mouse_fov_height;A.disable_prediction=cfg.disable_prediction;A.prediction_interval=cfg.prediction_interval;A.bScope_multiplier=cfg.bScope_multiplier;A.screen_width=cfg.detection_window_width;A.screen_height=cfg.detection_window_height;A.center_x=A.screen_width/2;A.center_y=A.screen_height/2
mouse=MouseThread()