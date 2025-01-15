_A=None
import queue,threading,time,cv2,torch,win32gui,win32con,win32api,os
from logic.config_watcher import cfg
from logic.capture import capture
from logic.overlay import overlay
from logic.buttons import Buttons
class Visuals(threading.Thread):
        def __init__(A):
                overlay.show(cfg.detection_window_width,cfg.detection_window_height)
                if cfg.show_window or cfg.show_overlay:
                        super(Visuals,A).__init__();A.queue=queue.Queue(maxsize=1);A.daemon=True;A.name='Visuals';A.image=_A;A.screenshot_taken=False
                        if cfg.show_window:A.interpolation=cv2.INTER_NEAREST
                        A.draw_line_data=_A;A.draw_predicted_position_data=_A;A.draw_boxes_data=_A;A.draw_speed_data=_A;A.draw_bScope_data=_A;A.draw_history_point_data=[];A.cls_model_data={0:'player',1:'bot',2:'weapon',3:'outline',4:'dead_body',5:'hideout_target_human',6:'hideout_target_balls',7:'head',8:'smoke',9:'fire',10:'third_person'};A.disabled_line_classes=[2,3,4,8,9,10];A.start()
        def run(A):
                Q='screenshots';K='green'
                if cfg.show_window:A.spawn_debug_window();L,G=0,0 if cfg.show_window_fps else _A
                while True:
                        A.image=A.queue.get()
                        if A.image is _A:A.destroy();break
                        R=win32api.GetAsyncKeyState(Buttons.KEY_CODES.get(cfg.debug_window_screenshot_key))
                        if R==-32768:
                                if not A.screenshot_taken:
                                        if not os.path.isdir(Q):os.makedirs(Q)
                                        cv2.imwrite(f"./screenshots/{time.time()}.jpg",A.image);A.screenshot_taken=True
                        else:A.screenshot_taken=False
                        if A.draw_line_data:
                                if cfg.show_window and cfg.show_target_line:cv2.line(A.image,(capture.screen_x_center,capture.screen_y_center),(int(A.draw_line_data[0]),int(A.draw_line_data[1])),(0,255,255),2)
                                if cfg.show_overlay and cfg.overlay_show_target_line:overlay.draw_line(capture.screen_x_center,capture.screen_y_center,int(A.draw_line_data[0]),int(A.draw_line_data[1]),K,2)
                        if A.draw_boxes_data:
                                for E in A.draw_boxes_data:
                                        if E:
                                                for(S,T,U)in zip(E.xyxy,E.cls,E.conf):
                                                        B,C,M,N=map(int,map(torch.Tensor.item,S))
                                                        if cfg.show_window and cfg.show_boxes:cv2.rectangle(A.image,(B,C),(M,N),(0,200,0),2)
                                                        if cfg.show_overlay and cfg.overlay_show_boxes:overlay.draw_square(B,C,M,N,K,2)
                                                        H=A.cls_model_data.get(T.item(),'')
                                                        if cfg.show_window and cfg.show_labels and not cfg.show_conf:cv2.putText(A.image,H,(B,C-5),cv2.FONT_HERSHEY_SIMPLEX,1,(0,200,0),1,cv2.LINE_AA)
                                                        if cfg.show_window or cfg.show_overlay:O='{} {:.2f}'.format(H,U.item())
                                                        if cfg.show_window and cfg.show_conf:cv2.putText(A.image,O,(B,C-5),cv2.FONT_HERSHEY_SIMPLEX,1,(0,200,0),1,cv2.LINE_AA)
                                                        if cfg.show_overlay and cfg.overlay_show_conf or cfg.show_overlay and cfg.overlay_show_labels:
                                                                D=0;F=0
                                                                if C<=15:D=B-45;F=C+15
                                                                else:D=B+45;F=C-15
                                                                if B<=40:D=B+40
                                                                if B>=cfg.detection_window_width-80:D=B-40
                                                                if cfg.overlay_show_conf:overlay.draw_text(D,F,O)
                                                                if cfg.overlay_show_labels and not cfg.overlay_show_conf:overlay.draw_text(D,F,H)
                        if A.draw_speed_data:
                                if cfg.show_window:cv2.putText(A.image,'preprocess: {:.2f}'.format(A.draw_speed_data[0]),(10,20),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),1,cv2.LINE_AA);cv2.putText(A.image,'inference: {:.2f}'.format(A.draw_speed_data[1]),(10,40),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),1,cv2.LINE_AA);cv2.putText(A.image,'postprocess: {:.2f}'.format(A.draw_speed_data[2]),(10,60),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),1,cv2.LINE_AA)
                        if cfg.show_window_fps:
                                G=time.time();V=1/(G-L);L=G
                                if cfg.show_window:cv2.putText(A.image,f"FPS: {str(int(V))}",(10,80)if cfg.show_detection_speed else(10,20),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),1,cv2.LINE_AA)
                        if A.draw_bScope_data:
                                I,W,J,X,Y=A.draw_bScope_data
                                if Y:
                                        if cfg.show_window:cv2.putText(A.image,'True',(int(I),int(J)-5),cv2.FONT_HERSHEY_SIMPLEX,1,(200,0,0),2,cv2.LINE_AA)
                                elif cfg.show_window:cv2.putText(A.image,'False',(int(I),int(J)-5),cv2.FONT_HERSHEY_SIMPLEX,1,(200,0,0),2,cv2.LINE_AA)
                                if cfg.show_window:cv2.rectangle(A.image,(int(I),int(J)),(int(W),int(X)),(200,0,0),2)
                        if A.draw_predicted_position_data:
                                if cfg.show_window and cfg.show_target_prediction_line:cv2.line(A.image,(capture.screen_x_center,capture.screen_y_center),(int(A.draw_predicted_position_data[0]),int(A.draw_predicted_position_data[1])),(255,0,255),2)
                                if cfg.show_overlay and cfg.overlay_show_target_prediction_line:overlay.draw_line(capture.screen_x_center,capture.screen_y_center,int(A.draw_predicted_position_data[0]),int(A.draw_predicted_position_data[1]),K,2)
                        if A.draw_history_point_data:
                                if len(A.draw_history_point_data)>=30:A.draw_history_point_data.pop(0)
                                for(Z,a)in A.draw_history_point_data:
                                        if cfg.show_window:cv2.circle(A.image,(Z+capture.screen_x_center,a+capture.screen_y_center),radius=1,color=(0,0,255),thickness=2)
                        if cfg.show_window:
                                try:
                                        if cfg.debug_window_scale_percent!=100:b=int(cfg.detection_window_height*cfg.debug_window_scale_percent/100);c=int(cfg.detection_window_width*cfg.debug_window_scale_percent/100);P=c,b;cv2.resizeWindow(cfg.debug_window_name,P);d=cv2.resize(A.image,P,A.interpolation);cv2.imshow(cfg.debug_window_name,d)
                                        else:cv2.imshow(cfg.debug_window_name,A.image)
                                except:exit(0)
                                if cv2.waitKey(1)&255==ord('q'):break
        def spawn_debug_window(E):
                cv2.namedWindow(cfg.debug_window_name)
                if cfg.debug_window_always_on_top:
                        try:
                                A=cfg.spawn_window_pos_x;B=cfg.spawn_window_pos_y
                                if A<=-1:A=0
                                if B<=-1:B=0
                                C=win32gui.FindWindow(_A,cfg.debug_window_name);win32gui.SetWindowPos(C,win32con.HWND_TOPMOST,A,B,cfg.detection_window_width,cfg.detection_window_height,0)
                        except Exception as D:print(f"Error with on top window, skipping this option `debug_window_always_on_top`: {D}")
        def draw_target_line(A,target_x,target_y,target_cls):
                if target_cls not in A.disabled_line_classes:A.draw_line_data=target_x,target_y
        def draw_predicted_position(A,target_x,target_y,target_cls):
                if target_cls not in A.disabled_line_classes:A.draw_predicted_position_data=target_x,target_y
        def draw_speed(A,speed_preprocess,speed_inference,speed_postprocess):A.draw_speed_data=speed_preprocess,speed_inference,speed_postprocess
        def draw_helpers(A,boxes):A.draw_boxes_data=boxes
        def draw_bScope(A,x1,x2,y1,y2,bScope):A.draw_bScope_data=x1,x2,y1,y2,bScope
        def draw_history_point_add_point(A,x,y):A.draw_history_point_data.append([int(x),int(y)])
        def clear(A):A.draw_boxes_data=_A;A.draw_line_data=_A;A.draw_speed_data=_A;A.draw_predicted_position_data=_A;A.draw_bScope_data=_A
        def destroy(A):cv2.destroyAllWindows()
visuals=Visuals()