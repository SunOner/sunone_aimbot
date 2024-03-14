import logic.buttons
import tkinter as tk
from tkinter import ttk
import configparser
import subprocess
import threading
import sys
import ctypes

class SettingsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Config Settings")
        self.config = configparser.ConfigParser()
        self.load_config()
        self.create_widgets()

    def load_config(self):
        config_file_path = "./config.ini"
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

        config_file_path = 'config.ini'
        
        try:
            with open(config_file_path, 'r') as configfile:
                lines = configfile.readlines()

            with open(config_file_path, 'w') as configfile:
                current_section = None
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('[') and stripped_line.endswith(']'):
                        current_section = stripped_line[1:-1]
                        configfile.write(line)
                    elif '=' in line and not stripped_line.startswith('#') and current_section:
                        key, _ = map(str.strip, line.split('=', 1))
                        if self.config.has_option(current_section, key):
                            value = self.config.get(current_section, key)
                            configfile.write(f'{key} = {value}\n')
                        else:
                            configfile.write(line)
                    else:
                        configfile.write(line)

            print('Config saved successfully!')
        except Exception as e:
            print(f'Error writing to config file: {e}')

    def run_script(self, script_name):
        threading.Thread(target=self.run_script_in_thread, args=(script_name,)).start()

    def run_script_in_thread(self, script_name):
        try:
            if sys.platform.startswith('win'):
                if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_name, None, 1)
                    sys.exit(0)
                else:
                    subprocess.run(['python', script_name], check=True)
            else:
                subprocess.run(['sudo', 'python', script_name], check=True)
        except Exception as e:
            print(f"Error running '{script_name}': {e}")

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
                    hotkey_options = []
                    for i in logic.buttons.Buttons.KEY_CODES:
                        hotkey_options.append(i)
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

        save_button = ttk.Button(self.root, text='Save Config', command=self.save_config)
        save_button.pack(pady=10)

        run_button_script = ttk.Button(self.root, text="Run Aimbot", command=lambda: self.run_script('run.py'))
        run_button_script.pack(pady=10)

        run_button_helper = ttk.Button(self.root, text="Run Helper", command=lambda: self.run_script('helper.py'))
        run_button_helper.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsGUI(root)
    root.mainloop()
