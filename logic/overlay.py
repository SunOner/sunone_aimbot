from tkinter import Canvas
import tkinter as tk
import tkinter.font as tkFont
import threading
import queue

from logic.config_watcher import cfg

class Overlay:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = None
        self.square_id = None
        
        # Skip frames so that the figures do not interfere with the detector ¯\_(ツ)_/¯
        self.frame_skip_counter = 0

    def run(self, width, height):
        if cfg.show_overlay:
            self.root = tk.Tk()
            
            self.root.overrideredirect(True)
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.root.attributes('-topmost', True)
            self.root.attributes('-transparentcolor', 'black')

            self.canvas = Canvas(self.root, bg='black', highlightthickness=0, cursor="none")
            self.canvas.pack(fill=tk.BOTH, expand=True)

            self.root.bind("<Button-1>", lambda e: "break")
            self.root.bind("<Button-2>", lambda e: "break")
            self.root.bind("<Button-3>", lambda e: "break")
            self.root.bind("<Motion>", lambda e: "break")
            self.root.bind("<Key>", lambda e: "break")
            self.root.bind("<Enter>", lambda e: "break")
            self.root.bind("<Leave>", lambda e: "break")
            self.root.bind("<FocusIn>", lambda e: "break")
            self.root.bind("<FocusOut>", lambda e: "break")
            
            self.canvas.bind("<Button-1>", lambda e: "break")
            self.canvas.bind("<Button-2>", lambda e: "break")
            self.canvas.bind("<Button-3>", lambda e: "break")
            self.canvas.bind("<Motion>", lambda e: "break")
            self.canvas.bind("<Key>", lambda e: "break")
            self.canvas.bind("<Enter>", lambda e: "break")
            self.canvas.bind("<Leave>", lambda e: "break")
            self.canvas.bind("<FocusIn>", lambda e: "break")
            self.canvas.bind("<FocusOut>", lambda e: "break")

            if cfg.overlay_show_borders:
                if cfg.circle_capture:
                    self.square_id = self.canvas.create_oval(0, 0, width, height, outline='red', width=2)
                else:
                    self.square_id = self.canvas.create_rectangle(0, 0, width, height, outline='red', width=2)

            self.process_queue()
            self.root.mainloop()

    def process_queue(self):
        self.frame_skip_counter += 1
        if self.frame_skip_counter % 3 == 0:
            if not self.queue.empty():
                for item in self.canvas.find_all():
                    if item != self.square_id:
                        self.canvas.delete(item)
                while not self.queue.empty():
                    command, args = self.queue.get()
                    command(*args)
            else:
                for item in self.canvas.find_all():
                    if item != self.square_id:
                        self.canvas.delete(item)
        self.root.after(2, self.process_queue)

    def draw_square(self, x1, y1, x2, y2, color='white', size=1):
        self.queue.put((self._draw_square, (x1, y1, x2, y2, color, size)))

    def _draw_square(self, x1, y1, x2, y2, color='white', size=1):
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=size)

    def draw_oval(self, x1, y1, x2, y2, color='white', size=1):
        self.queue.put((self._draw_oval, (x1, y1, x2, y2, color, size)))

    def _draw_oval(self, x1, y1, x2, y2, color='white', size=1):
        self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=size)

    def draw_line(self, x1, y1, x2, y2, color='white', size=1):
        self.queue.put((self._draw_line, (x1, y1, x2, y2, color, size)))

    def _draw_line(self, x1, y1, x2, y2, color='white', size=1):
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=size)

    def draw_point(self, x, y, color='white', size=1):
        self.queue.put((self._draw_point, (x, y, color, size)))

    def _draw_point(self, x, y, color='white', size=1):
        self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline=color)

    def draw_text(self, x, y, text, size=12, color='white'):
        self.queue.put((self._draw_text, (x, y, text, size, color)))

    def _draw_text(self, x, y, text, size, color):
        self.canvas.create_text(x, y, text=text, font=('Arial', size), fill=color, state='')

    def show(self, width, height):
        if self.thread is None:
            self.thread = threading.Thread(target=self.run, args=(width, height), daemon=True, name="Overlay")
            self.thread.start()

overlay = Overlay()