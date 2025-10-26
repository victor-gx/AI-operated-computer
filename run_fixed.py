import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 确保中文显示正常
os.environ["QT_FONT_DPI"] = "96"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# 直接导入并运行main_window模块
if __name__ == "__main__":
    try:
        # 直接导入main_window模块并运行
        from ui.main_window import QApplication, MainWindow
        
        # 创建应用程序实例
        app = QApplication(sys.argv)
        
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
    except Exception as e:
        # 尝试将错误信息写入文件
        try:
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(f"错误: {str(e)}\n")
                import traceback
                f.write("堆栈跟踪:\n")
                f.write(traceback.format_exc())
        except:
            pass
        
        # 重新抛出异常以便看到错误
        raise
