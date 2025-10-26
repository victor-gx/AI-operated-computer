import os
import sys
import threading
import time
import traceback

# ---- 关键：在任何 PyQt5 导入前设置 Qt platform 插件路径 ----
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r"C:\envs\Anaconda3\Lib\site-packages\menuinst\platforms"

# --------------------- 现在导入 PyQt5 ---------------------
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QComboBox, QLineEdit, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal

# --------------------- 项目模块 ---------------------
from ai.tts import speak
from ai.intent_parser import analyze_intent
from actions.web_control import open_website, navigate_to
from actions.system_control import execute_system_action
from actions.app_control import open_app
import speech_recognition as sr


# 如果你把 recognizer 放在 voice/recognizer.py 内并导出 select_mic/listen，可替换为：
# from voice.recognizer import select_mic, listen
# 但这里我们直接使用 speech_recognition 的接口以便 UI 控制设备索引和监听

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
        self.setWindowTitle("AI 语音助手（带UI）")
        self.setGeometry(200, 200, 700, 520)

        self.worker = None

        # UI 元素
        self.status_label = QLabel("状态：未启动")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        self.start_button = QPushButton("开始识别")
        self.stop_button = QPushButton("停止识别")
        self.stop_button.setEnabled(False)

        self.mic_combo = QComboBox()
        self.refresh_mics_button = QPushButton("刷新麦克风列表")

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("在此输入要执行的文字指令（例如：导航到北京天安门）")
        self.manual_exec_button = QPushButton("执行文本指令")

        # 布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("麦克风："))
        top_layout.addWidget(self.mic_combo)
        top_layout.addWidget(self.refresh_mics_button)
        top_layout.addStretch()
        top_layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.stop_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.manual_input)
        btn_layout.addWidget(self.manual_exec_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.log_text)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 事件绑定
        self.start_button.clicked.connect(self.start_listening)
        self.stop_button.clicked.connect(self.stop_listening)
        self.refresh_mics_button.clicked.connect(self.refresh_mics)
        self.manual_exec_button.clicked.connect(self.exec_manual_command)

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
            self.log("已刷新麦克风设备列表。")
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
        self.log("已启动识别线程。")
        self.status_label.setText("状态：运行中")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_listening(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(timeout=3000)
            self.worker = None
            self.log("手动停止识别线程。")
        self.status_label.setText("状态：已停止")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        speak("语音助手已停止")

    def on_worker_finished(self):
        self.log("识别线程已结束。")
        self.status_label.setText("状态：已停止")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def exec_manual_command(self):
        text = self.manual_input.text().strip()
        if not text:
            return
        self.log(f"手动输入：{text}")
        # 直接调用 AI 解析并执行（在新线程执行网络请求，避免阻塞 UI）
        threading.Thread(target=self._exec_command_thread, args=(text,), daemon=True).start()

    def _exec_command_thread(self, text):
        try:
            self.log("调用 AI 解析中...")
            intent = analyze_intent(text)
            self.log(f"AI 返回：{intent}")
            action = intent.get("action")
            target = intent.get("target", "")
            if action == "open_website":
                open_website(target)
                self.log(f"已打开网站：{target}")
                speak(f"已为您打开{target}")
            elif action == "open_map":
                navigate_to(target)
                self.log(f"已打开地图：{target}")
                speak(f"正在为您导航到{target}")
            elif action == "system":
                execute_system_action(target)
                self.log(f"已执行系统命令：{target}")
                speak("系统命令已执行")
            elif action == "open_app":
                open_app(target)
                self.log(f"已打开应用：{target}")
                speak(f"已为您打开{target}")
            else:
                self.log("未识别到有效意图。")
                speak("抱歉，我没理解您的指令。")
        except Exception as e:
            self.log(f"执行命令异常：{e}")

    def log(self, text):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text.append(f"[{ts}] {text}")


def run_ui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_ui()

