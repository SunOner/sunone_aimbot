import torch
from logic.hotkeys_watcher import hotkeys_watcher
from logic.config_watcher import cfg
from logic.capture import capture
from logic.visual import visuals
from logic.mouse import mouse
from logic.shooting import shooting
class Target:
        def __init__(A,x,y,w,h,cls):A.x=x;A.y=y if cls==7 else y-cfg.body_y_offset*h;A.w=w;A.h=h;A.cls=cls
class FrameParser:
        def __init__(A):A.arch=A.get_arch()
        def parse(D,result):
                C=False
                for B in result:
                        if B.boxes:
                                A=D.sort_targets(B)
                                if A:
                                        if hotkeys_watcher.clss is None:hotkeys_watcher.active_classes()
                                        if A.cls in hotkeys_watcher.clss:mouse.process_data((A.x,A.y,A.w,A.h,A.cls))
                        if cfg.show_window or cfg.show_overlay:
                                if cfg.show_boxes or cfg.overlay_show_boxes:visuals.draw_helpers(B.boxes)
                        else:
                                if cfg.auto_shoot or cfg.triggerbot:shooting.shoot(C,C)
                                if cfg.show_window or cfg.show_overlay:visuals.clear()
                        if cfg.show_window and cfg.show_detection_speed:visuals.draw_speed(B.speed['preprocess'],B.speed['inference'],B.speed['postprocess'])
        def sort_targets(E,frame):
                I=frame;D=I.boxes.xywh.to(E.arch);B=I.boxes.cls.to(E.arch)
                if not B.numel():return
                K=torch.tensor([capture.screen_x_center,capture.screen_y_center],device=E.arch);A=torch.sum((D[:,:2]-K)**2,dim=1);F=torch.ones_like(A)
                if cfg.disable_headshot:
                        G=B!=7;F=torch.ones_like(B);F[B==7]*=.5;J=D[:,2]*D[:,3];A=A/J;A=F*A/J
                        if G.any():L=A[G];C=torch.argmin(L);C=torch.nonzero(G)[C].item()
                        else:return
                else:
                        H=B==7
                        if H.any():M=A[H];N=torch.argmin(M);C=torch.nonzero(H)[N].item()
                        else:C=torch.argmin(A)
                if not B.numel():return
                O=D[C,:4].cpu().numpy();P=B[C].item();return Target(*O,P)
        def get_arch(C):
                B='cpu'
                if cfg.AI_enable_AMD:A=f"hip:{cfg.AI_device}"
                else:A=f"cuda:{cfg.AI_device}"
                if B in cfg.AI_device:A=B
                return A
frameParser=FrameParser()