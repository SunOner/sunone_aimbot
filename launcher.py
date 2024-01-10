import subprocess
import sys

# Run gui.py without showing the PowerShell window
subprocess.Popen(['python', 'GUI.py'], creationflags=subprocess.CREATE_NO_WINDOW)

# Exit the launcher script
sys.exit()