import speech_recognition as sr

def select_mic():
    names = sr.Microphone.list_microphone_names()
    if not names:
        print("未检测到麦克风设备。")
        return None
    print("检测到以下麦克风：")
    for i, name in enumerate(names):
        print(f"[{i}] {name}")
    return 0

def listen(device_index=None):
    r = sr.Recognizer()
    with sr.Microphone(device_index=device_index) as source:
        print("请讲话...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source, phrase_time_limit=5)
    try:
        return r.recognize_google(audio, language='zh-CN')
    except:
        print("语音识别失败")
        return ""
