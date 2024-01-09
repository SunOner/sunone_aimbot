import tkinter as tk
from tkinter import ttk
import configparser
import subprocess
import threading

class SettingsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Config Settings")
        self.config = configparser.ConfigParser()
        self.load_config()
        self.create_widgets()

    def load_config(self):
        config_file_path = "config.ini"
        self.config.read(config_file_path)

    def update_config(self):
        for section in self.config.sections():
            for option in self.config.options(section):
                if isinstance(self.widgets[section][option], ttk.Entry):
                    self.config.set(section, option, self.widgets[section][option].get())
                elif isinstance(self.widgets[section][option], ttk.Combobox):
                    self.config.set(section, option, self.widgets[section][option].get())
                elif isinstance(self.widgets[section][option], tk.BooleanVar):
                    self.config.set(section, option, str(self.widgets[section][option].get()))

    def save_config(self):
        self.update_config()

        config_file_path = "config.ini"

        try:
            with open(config_file_path, 'w') as configfile:
                self.config.write(configfile)
            print("Config saved successfully!")
        except Exception as e:
            print(f"Error writing to config file: {e}")

    def run_script(self):
        threading.Thread(target=self.run_script_in_thread).start()

    def run_script_in_thread(self):
        try:
            subprocess.run(["python", "run.py"])
        except Exception as e:
            print(f"Error running 'run.py': {e}")

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self.widgets = {}

        for section in self.config.sections():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=section)

            row_index = 0
            for option in self.config.options(section):
                ttk.Label(tab, text=f"{option.replace('_', ' ').capitalize()}:").grid(row=row_index, column=0, padx=10, pady=5)

                if option.startswith('hotkey_'):
                    hotkey_options = [
                        'LeftMouseButton', 'RightMouseButton', 'ControlBreak',
                        'MiddleMouseButton', 'X1MouseButton', 'X2MouseButton',
                        'Backspace', 'Tab', 'Clear', 'Enter', 'Pause',
                        'CapsLock', 'Escape', 'Space', 'PageUp',
                        'PageDown', 'End', 'Home', 'LeftArrow',
                        'UpArrow', 'RightArrow', 'DownArrow', 'Select',
                        'Print', 'Execute', 'PrintScreen', 'Ins',
                        'Delete', 'Help', 'Key0', 'Key1', 'Key2',
                        'Key3', 'Key4', 'Key5', 'Key6', 'Key7',
                        'Key8', 'Key9', 'A', 'B', 'C', 'D',
                        'E', 'F', 'G', 'H', 'I', 'J',
                        'K', 'L', 'M', 'N', 'O', 'P',
                        'Q', 'R', 'S', 'T', 'U', 'V',
                        'W', 'X', 'Y', 'LeftWindowsKey',
                        'RightWindowsKey', 'Application', 'Sleep',
                        'NumpadKey0', 'NumpadKey1', 'NumpadKey2',
                        'NumpadKey3', 'NumpadKey4', 'NumpadKey5',
                        'NumpadKey6', 'NumpadKey7', 'NumpadKey8',
                        'NumpadKey9', 'Multiply', 'Add', 'Separator',
                        'Subtract', 'Decimal', 'Divide', 'F1',
                        'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8',
                        'F9', 'F10', 'F11', 'F12', 'NumLock',
                        'ScrollLock', 'LeftShift', 'RightShift',
                        'LeftControl', 'RightControl', 'LeftMenu',
                        'RightMenu', 'BrowserBack', 'BrowserRefresh',
                        'BrowserStop', 'BrowserSearch', 'BrowserFavorites',
                        'BrowserHome', 'VolumeMute', 'VolumeDown', 'VolumeUp',
                        'NextTrack', 'PreviousTrack', 'StopMedia', 'PlayMedia',
                        'StartMailKey', 'SelectMedia', 'StartApplication1',
                        'StartApplication2'
                    ]

                    var = ttk.Combobox(tab, values=hotkey_options, state="readonly")
                    var.set(self.config.get(section, option))
                elif self.config.get(section, option).lower() in ['true', 'false']:
                    var = tk.BooleanVar(value=self.config.getboolean(section, option))
                    widget = ttk.Checkbutton(tab, variable=var)
                else:
                    var = ttk.Entry(tab)
                    var.insert(0, self.config.get(section, option))
                    widget = var

                if not option.startswith('hotkey_'):
                    widget.grid(row=row_index, column=1, padx=10, pady=5)
                else:
                    var.grid(row=row_index, column=1, padx=10, pady=5)

                self.widgets.setdefault(section, {})[option] = var
                row_index += 1

        save_button = ttk.Button(self.root, text="Save Config", command=self.save_config)
        save_button.pack(pady=10)

        run_button = ttk.Button(self.root, text="Run", command=self.run_script)
        run_button.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsGUI(root)
    root.mainloop()
