import sys
import os

# 确保中文显示正常
import os
os.environ["QT_FONT_DPI"] = "96"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# 尝试导入PyQt5并运行简单的窗口
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
    print("PyQt5导入成功")
    
    # 创建一个简单的窗口
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("测试窗口")
    window.setGeometry(100, 100, 300, 200)
    
    label = QLabel("PyQt5窗口测试", window)
    label.setGeometry(50, 50, 200, 100)
    
    window.show()
    sys.exit(app.exec_())
except ImportError as e:
    print(f"PyQt5导入失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()