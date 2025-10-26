import os
import platform

def execute_system_action(action):
    sys_name = platform.system().lower()
    if action == "shutdown":
        if "windows" in sys_name:
            os.system("shutdown /s /t 1")
        else:
            os.system("shutdown now")
    elif action == "reboot":
        if "windows" in sys_name:
            os.system("shutdown /r /t 1")
        else:
            os.system("reboot")
    elif action == "lock":
        if "windows" in sys_name:
            os.system("rundll32.exe user32.dll,LockWorkStation")
        else:
            os.system("pmset displaysleepnow")
