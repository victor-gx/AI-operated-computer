import os, sys, PyQt5

# 设置 Qt 插件路径
qt_plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt", "plugins")
os.environ["QT_PLUGIN_PATH"] = qt_plugin_path
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(qt_plugin_path, "platforms")
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

print("✅ Qt 插件路径修复成功：", os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"])

# 启动主界面
from ui import main_window
