from ai.intent_parser import analyze_intent
from actions.system_control import execute_system_action
from actions.web_control import open_website, navigate_to
from actions.app_control import open_app
from ai.tts import speak
from voice.recognizer import select_mic, listen
from config import WAKE_WORD

def main():
    speak("语音助手启动，正在检测麦克风。")
    device_index = select_mic()
    if device_index is None:
        speak("未检测到麦克风，请检查设备连接或系统权限。")
        return
    speak("麦克风检测通过，请说出唤醒词。")

    while True:
        text = listen(device_index=device_index)
        if not text:
            continue
        if WAKE_WORD not in text:
            continue
        speak("我在，请说出指令。")
        text = listen(device_index=device_index)
        if not text:
            continue
        intent = analyze_intent(text)
        action = intent.get("action")
        target = intent.get("target", "")

        if action == "open_website":
            open_website(target)
            speak(f"已为您打开 {target}")
        elif action == "open_map":
            navigate_to(target)
            speak(f"正在为您打开地图，导航到 {target}")
        elif action == "system":
            execute_system_action(target)
        elif action == "open_app":
            open_app(target)
            speak(f"已为您打开应用 {target}")
        else:
            speak("我还不太理解您的意思。")

if __name__ == "__main__":
    main()
