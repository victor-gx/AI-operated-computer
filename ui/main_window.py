import os
import sys
import threading
import time
import traceback

# ---- 关键：在任何 PyQt5 导入前设置 Qt platform 插件路径 ----
# os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r"C:\envs\Anaconda3\Lib\site-packages\menuinst\platforms"

# --------------------- 现在导入 PyQt5 ---------------------
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QComboBox, QLineEdit, QMessageBox, QSplitter, QGroupBox,
    QFontDialog, QColorDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QTextCharFormat

# --------------------- 项目模块 ---------------------
from ai.tts import speak
from ai.intent_parser import analyze_intent
from actions.web_control import open_website, navigate_to
from actions.system_control import execute_system_action
from actions.app_control import open_app
import speech_recognition as sr



WAKE_WORD = "灵汐"  # 默认，如果你使用 config.yaml 管理，可读入配置


class VoiceWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, device_index=None, wake_word=WAKE_WORD):
        super().__init__()
        self.device_index = device_index
        self.running = False
        self.wake_word = wake_word
        self._recognizer = sr.Recognizer()

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        self.log_signal.emit("语音识别线程已启动。")
        mic = None
        try:
            mic = sr.Microphone(device_index=self.device_index) if self.device_index is not None else sr.Microphone()
        except Exception as e:
            self.log_signal.emit(f"打开麦克风失败：{e}")
            self.finished_signal.emit()
            return

        with mic as source:
            # 调整环境噪声
            try:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                self.log_signal.emit(f"调节环境噪声失败：{e}")

        # 长轮询：先等待唤醒词，再执行命令
        while self.running:
            try:
                with mic as source:
                    self.log_signal.emit("等待唤醒词（请说唤醒词）...")
                    audio = self._recognizer.listen(source, phrase_time_limit=6)
                try:
                    text = self._recognizer.recognize_google(audio, language='zh-CN')
                except sr.UnknownValueError:
                    self.log_signal.emit("未识别到有效语音（请再试一次）。")
                    continue
                except sr.RequestError as e:
                    self.log_signal.emit(f"语音识别请求失败：{e}")
                    time.sleep(1)
                    continue

                self.log_signal.emit(f"识别到语音：{text}")

                if self.wake_word and self.wake_word not in text:
                    # 如果没有唤醒词，则继续等待
                    self.log_signal.emit("唤醒词未命中，继续监听...")
                    continue

                self.log_signal.emit("唤醒词命中，正在监听指令...")
                # 直接再次录音捕获命令
                with mic as source:
                    audio_cmd = self._recognizer.listen(source, phrase_time_limit=6)

                try:
                    cmd_text = self._recognizer.recognize_google(audio_cmd, language='zh-CN')
                except sr.UnknownValueError:
                    self.log_signal.emit("未识别到指令文本，跳过一次。")
                    continue
                except sr.RequestError as e:
                    self.log_signal.emit(f"语音识别请求失败：{e}")
                    continue

                self.log_signal.emit(f"用户命令：{cmd_text}")
                # 调用AI解析意图（网络），返回 JSON 结构
                intent = analyze_intent(cmd_text)
                self.log_signal.emit(f"AI 返回：{intent}")

                # 解析并执行
                action = intent.get("action")
                target = intent.get("target", "")
                detail = intent.get("detail", "")

                if action == "open_website":
                    open_website(target)
                    self.log_signal.emit(f"已打开网站：{target}")
                    speak(f"已为您打开{target}")
                elif action == "open_map":
                    navigate_to(target)
                    self.log_signal.emit(f"已打开地图并查询：{target}")
                    speak(f"正在为您导航到{target}")
                elif action == "system":
                    execute_system_action(target)
                    self.log_signal.emit(f"已执行系统命令：{target}")
                    speak("系统命令已执行")
                elif action == "open_app":
                    open_app(target)
                    self.log_signal.emit(f"已打开应用：{target}")
                    speak(f"已为您打开{target}")
                else:
                    self.log_signal.emit("未识别到可执行意图，AI 返回为 none 或未知。")
                    speak("抱歉，我没理解您的指令。")

            except Exception as e:
                self.log_signal.emit("语音线程异常：" + str(e))
                self.log_signal.emit(traceback.format_exc())
                time.sleep(1)

        self.log_signal.emit("语音识别线程退出。")
        self.finished_signal.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 语音助手（高级版）")
        self.setGeometry(200, 200, 800, 600)
        
        # 设置全局样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 6px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: #e6e6e6;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox, QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QLabel {
                font-size: 14px;
            }
            QLabel#statusLabel {
                font-weight: bold;
            }
            QSplitter::handle:horizontal {
                background-color: #cccccc;
                width: 4px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #999999;
            }
        """)

        self.worker = None
        
        # 初始化日志格式
        self.log_formats = {}
        self.init_log_formats()
        
        # 记录初始状态颜色
        self.normal_status_style = "color: black;"

        # UI 元素
        self.status_label = QLabel("状态：未启动")
        self.status_label.setObjectName("statusLabel")
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # 设置文本编辑框的换行模式
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # 设置日志字体
        log_font = QFont("Consolas", 10)
        self.log_text.setFont(log_font)

        self.start_button = QPushButton("开始识别")
        self.stop_button = QPushButton("停止识别")
        self.stop_button.setEnabled(False)

        self.mic_combo = QComboBox()
        self.mic_combo.setMinimumWidth(200)
        self.refresh_mics_button = QPushButton("刷新麦克风列表")

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("在此输入要执行的文字指令（例如：导航到北京天安门）")
        self.manual_exec_button = QPushButton("执行文本指令")
        
        # 新增功能按钮
        self.clear_log_button = QPushButton("清空日志")
        self.show_config_button = QPushButton("配置")

        # 布局改进
        # 麦克风设置组
        mic_group = QGroupBox("麦克风设置")
        mic_layout = QHBoxLayout()
        mic_layout.addWidget(QLabel("选择麦克风："))
        mic_layout.addWidget(self.mic_combo)
        mic_layout.addWidget(self.refresh_mics_button)
        mic_layout.addStretch()
        mic_group.setLayout(mic_layout)
        
        # 控制按钮组
        control_group = QGroupBox("语音控制")
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.show_config_button)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        control_group.setLayout(control_layout)
        
        # 手动输入组
        manual_group = QGroupBox("手动指令输入")
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(self.manual_input, 1)
        manual_layout.addWidget(self.manual_exec_button)
        manual_group.setLayout(manual_layout)
        
        # 日志显示组
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        log_buttons_layout = QHBoxLayout()
        log_buttons_layout.addStretch()
        log_buttons_layout.addWidget(self.clear_log_button)
        log_layout.addLayout(log_buttons_layout)
        log_layout.addWidget(self.log_text, 1)
        log_group.setLayout(log_layout)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(mic_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(manual_group)
        main_layout.addWidget(log_group, 1)
        
        # 添加边距
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 事件绑定
        self.start_button.clicked.connect(self.start_listening)
        self.stop_button.clicked.connect(self.stop_listening)
        self.refresh_mics_button.clicked.connect(self.refresh_mics)
        self.manual_exec_button.clicked.connect(self.exec_manual_command)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.show_config_button.clicked.connect(self.show_config_dialog)
        
        # 添加回车键执行文本指令
        self.manual_input.returnPressed.connect(self.exec_manual_command)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.show_config_button.clicked.connect(self.show_config_dialog)
        
        # 添加回车键执行文本指令
        self.manual_input.returnPressed.connect(self.exec_manual_command)

        # 初始化麦克风列表
        self.refresh_mics()

    def refresh_mics(self):
        self.mic_combo.clear()
        try:
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                self.mic_combo.addItem("未检测到麦克风")
            else:
                for name in mics:
                    self.mic_combo.addItem(name)
            self.log("已刷新麦克风设备列表。", 'info')
        except Exception as e:
            self.log(f"刷新麦克风失败：{e}")

    def get_selected_mic_index(self):
        idx = self.mic_combo.currentIndex()
        # 如果未检测到麦克风，返回 None
        try:
            names = sr.Microphone.list_microphone_names()
            if not names:
                return None
            # 有的时候 combobox 的 index 需要映射到实际设备列表
            if idx < 0 or idx >= len(names):
                return None
            return idx
        except Exception:
            return None

    def start_listening(self):
        mic_idx = self.get_selected_mic_index()
        if mic_idx is None:
            QMessageBox.warning(self, "麦克风错误", "未检测到可用麦克风，请连接并刷新设备列表。")
            return
        self.worker = VoiceWorker(device_index=mic_idx)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()
        self.log("已启动识别线程。", 'success')
        
        # 改变状态标签颜色为绿色，表示运行中
        self.status_label.setText("状态：运行中")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_listening(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)  # 等待工作线程结束，最多3秒（使用位置参数，不是关键字参数）
            self.worker = None
            self.log("手动停止识别线程。", 'info')
        
        # 恢复状态标签颜色
        self.status_label.setText("状态：已停止")
        self.status_label.setStyleSheet(self.normal_status_style)
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        speak("语音助手已停止")

    def on_worker_finished(self):
        self.log("识别线程已结束。", 'info')
        
        # 恢复状态标签颜色
        self.status_label.setText("状态：已停止")
        self.status_label.setStyleSheet(self.normal_status_style)
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def exec_manual_command(self):
        text = self.manual_input.text().strip()
        if not text:
            return
        self.log(f"手动输入：{text}", 'info')
        # 直接调用 AI 解析并执行（在新线程执行网络请求，避免阻塞 UI）
        threading.Thread(target=self._exec_command_thread, args=(text,), daemon=True).start()
        # 清空输入框
        self.manual_input.clear()
    
    def init_log_formats(self):
        """
        初始化日志格式，设置不同类型日志的颜色和样式
        """
        # 默认信息日志格式
        info_format = QTextCharFormat()
        
        # 成功日志格式
        success_format = QTextCharFormat()
        success_format.setForeground(QColor("#008000"))  # 绿色
        success_format.setFontWeight(QFont.Bold)
        
        # 警告日志格式
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor("#FF8C00"))  # 橙色
        warning_format.setFontWeight(QFont.Bold)
        
        # 错误日志格式
        error_format = QTextCharFormat()
        error_format.setForeground(QColor("#FF0000"))  # 红色
        error_format.setFontWeight(QFont.Bold)
        
        # 保存所有格式
        self.log_formats = {
            'info': info_format,
            'success': success_format,
            'warning': warning_format,
            'error': error_format
        }
    
    def clear_log(self):
        """
        清空日志窗口
        """
        self.log_text.clear()
        self.log("日志已清空。", 'info')
    
    def show_config_dialog(self):
        """
        显示配置对话框
        """
        # 简单的配置对话框
        config_msg = """
        AI语音助手配置选项：
        
        1. 唤醒词：{}
        2. 当前API服务：灵夕AI
        3. 语音识别服务：Google语音识别
        4. 语音合成服务：系统TTS
        
        更多配置请修改 config.yaml 文件。
        """.format(WAKE_WORD)
        
        QMessageBox.information(self, "配置信息", config_msg)

    def _exec_command_thread(self, text):
        try:
            self.log("调用 AI 解析中...", 'info')
            intent = analyze_intent(text)
            self.log(f"AI 返回：{intent}", 'info')
            action = intent.get("action")
            target = intent.get("target", "")
            if action == "open_website":
                open_website(target)
                self.log(f"已打开网站：{target}", 'success')
                speak(f"已为您打开{target}")
            elif action == "open_map":
                navigate_to(target)
                self.log(f"已打开地图：{target}", 'success')
                speak(f"正在为您导航到{target}")
            elif action == "system":
                execute_system_action(target)
                self.log(f"已执行系统命令：{target}", 'success')
                speak("系统命令已执行")
            elif action == "open_app":
                open_app(target)
                self.log(f"已打开应用：{target}", 'success')
                speak(f"已为您打开{target}")
            else:
                self.log("未识别到有效意图。", 'warning')
                speak("抱歉，我没理解您的指令。")
        except Exception as e:
            self.log(f"执行命令异常：{e}", 'error')

    def log(self, text, log_type='info'):
        """
        记录日志，支持不同类型的日志颜色区分
        :param text: 日志文本
        :param log_type: 日志类型 ('info', 'warning', 'error', 'success')
        """
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        timestamp = f"[{ts}] "
        
        # 确保日志类型有效
        if log_type not in self.log_formats:
            log_type = 'info'
        
        # 获取当前光标位置
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 插入时间戳（默认格式）
        cursor.insertText(timestamp)
        
        # 插入日志内容（根据类型设置不同颜色）
        cursor.setCharFormat(self.log_formats[log_type])
        cursor.insertText(text)
        
        # 插入换行
        cursor.insertText("\n")
        
        # 确保最新日志可见
        self.log_text.moveCursor(QTextCursor.End)
        
    def clear_log(self):
        """
        清空日志窗口
        """
        self.log_text.clear()
        self.log("日志已清空。", 'info')
        
    def show_config_dialog(self):
        """
        显示配置对话框
        """
        # 简单的配置对话框，可以根据需要扩展
        config_msg = """
        AI语音助手配置选项：
        
        1. 唤醒词：{}
        2. 当前API服务：灵夕AI
        3. 语音识别服务：Google语音识别
        4. 语音合成服务：系统TTS
        
        更多配置请修改 config.yaml 文件。
        """.format(WAKE_WORD)
        
        QMessageBox.information(self, "配置信息", config_msg)


def run_ui():
    """
    运行UI应用
    """
    # 设置应用样式
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 显示欢迎信息
    window.log("AI语音助手已启动，欢迎使用！", 'success')
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_ui()

