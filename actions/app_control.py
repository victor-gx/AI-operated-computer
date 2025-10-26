import subprocess
import platform

def open_app(app_name):
    sys_name = platform.system().lower()
    try:
        if "windows" in sys_name:
            subprocess.Popen(["start", "", app_name], shell=True)
        elif "darwin" in sys_name:
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
    except Exception as e:
        print(f"打开应用失败: {e}")
