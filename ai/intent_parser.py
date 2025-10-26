import json
import requests
import yaml

def load_key():
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["LINGXI_API_KEY"]

def analyze_intent(user_text):
    """
    使用七牛灵夕AI分析语义
    返回 JSON: {action, target, detail}
    """
    url = "https://api.lingxi.qiniuapi.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {load_key()}"
    }
    payload = {
        "model": "qwen-plus",
        "messages": [{
            "role": "user",
            "content": f"""
用户说：“{user_text}”
请分析用户意图，返回JSON格式：
{{
  "action": "open_app | open_website | open_map | system | none",
  "target": "目标程序或网址或地点",
  "detail": "附加说明"
}}
"""
        }]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        return json.loads(reply)
    except Exception as e:
        print(f"[错误] 调用灵夕AI失败: {e}")
        return {"action": "none"}
