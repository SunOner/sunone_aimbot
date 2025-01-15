_B=True
_A='white'
from tkinter import Canvas
import tkinter as tk,tkinter.font as tkFont,threading,queue
from logic.config_watcher import cfg
class Overlay:
        def __init__(A):A.queue=queue.Queue();A.thread=None;A.square_id=None;A.frame_skip_counter=0
        def run(A,width,height):
                O='red';N='<FocusOut>';M='<FocusIn>';L='<Leave>';K='<Enter>';J='<Key>';I='<Motion>';H='<Button-3>';G='<Button-2>';F='<Button-1>';E='black';D=height;C=width;B='break'
                if cfg.show_overlay:
                        A.root=tk.Tk();A.root.overrideredirect(_B);P=A.root.winfo_screenwidth();Q=A.root.winfo_screenheight();R=(P-C)//2;S=(Q-D)//2;A.root.geometry(f"{C}x{D}+{R}+{S}");A.root.attributes('-topmost',_B);A.root.attributes('-transparentcolor',E);A.canvas=Canvas(A.root,bg=E,highlightthickness=0,cursor='none');A.canvas.pack(fill=tk.BOTH,expand=_B);A.root.bind(F,lambda e:B);A.root.bind(G,lambda e:B);A.root.bind(H,lambda e:B);A.root.bind(I,lambda e:B);A.root.bind(J,lambda e:B);A.root.bind(K,lambda e:B);A.root.bind(L,lambda e:B);A.root.bind(M,lambda e:B);A.root.bind(N,lambda e:B);A.canvas.bind(F,lambda e:B);A.canvas.bind(G,lambda e:B);A.canvas.bind(H,lambda e:B);A.canvas.bind(I,lambda e:B);A.canvas.bind(J,lambda e:B);A.canvas.bind(K,lambda e:B);A.canvas.bind(L,lambda e:B);A.canvas.bind(M,lambda e:B);A.canvas.bind(N,lambda e:B)
                        if cfg.overlay_show_borders:
                                if cfg.circle_capture:A.square_id=A.canvas.create_oval(0,0,C,D,outline=O,width=2)
                                else:A.square_id=A.canvas.create_rectangle(0,0,C,D,outline=O,width=2)
                        A.process_queue();A.root.mainloop()
        def process_queue(A):
                A.frame_skip_counter+=1
                if A.frame_skip_counter%3==0:
                        if not A.queue.empty():
                                for B in A.canvas.find_all():
                                        if B!=A.square_id:A.canvas.delete(B)
                                while not A.queue.empty():C,D=A.queue.get();C(*D)
                        else:
                                for B in A.canvas.find_all():
                                        if B!=A.square_id:A.canvas.delete(B)
                A.root.after(2,A.process_queue)
        def draw_square(A,x1,y1,x2,y2,color=_A,size=1):A.queue.put((A._draw_square,(x1,y1,x2,y2,color,size)))
        def _draw_square(A,x1,y1,x2,y2,color=_A,size=1):A.canvas.create_rectangle(x1,y1,x2,y2,outline=color,width=size)
        def draw_oval(A,x1,y1,x2,y2,color=_A,size=1):A.queue.put((A._draw_oval,(x1,y1,x2,y2,color,size)))
        def _draw_oval(A,x1,y1,x2,y2,color=_A,size=1):A.canvas.create_oval(x1,y1,x2,y2,outline=color,width=size)
        def draw_line(A,x1,y1,x2,y2,color=_A,size=1):A.queue.put((A._draw_line,(x1,y1,x2,y2,color,size)))
        def _draw_line(A,x1,y1,x2,y2,color=_A,size=1):A.canvas.create_line(x1,y1,x2,y2,fill=color,width=size)
        def draw_point(A,x,y,color=_A,size=1):A.queue.put((A._draw_point,(x,y,color,size)))
        def _draw_point(C,x,y,color=_A,size=1):B=color;A=size;C.canvas.create_oval(x-A,y-A,x+A,y+A,fill=B,outline=B)
        def draw_text(A,x,y,text,size=12,color=_A):A.queue.put((A._draw_text,(x,y,text,size,color)))
        def _draw_text(A,x,y,text,size,color):A.canvas.create_text(x,y,text=text,font=('Arial',size),fill=color,state='')
        def show(A,width,height):
                if A.thread is None:A.thread=threading.Thread(target=A.run,args=(width,height),daemon=_B,name='Overlay');A.thread.start()
overlay=Overlay()