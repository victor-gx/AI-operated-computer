import pyttsx3
import yaml

with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", cfg.get("TTS_RATE", 150))
    engine.say(text)
    engine.runAndWait()
