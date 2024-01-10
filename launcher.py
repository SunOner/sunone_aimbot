import subprocess
import sys

subprocess.Popen(['python', './logic/GUI.py'], creationflags=subprocess.CREATE_NO_WINDOW)
sys.exit()