import yaml
import os

# 读取配置文件
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 导出配置项
LINGXI_API_KEY = config.get('LINGXI_API_KEY', '')
TTS_VOICE = config.get('TTS_VOICE', 'zh')
TTS_RATE = config.get('TTS_RATE', 150)
WAKE_WORD = config.get('WAKE_WORD', '灵汐')
CONTINUOUS_MODE = config.get('CONTINUOUS_MODE', True)
CONTINUOUS_LISTEN_DURATION = config.get('CONTINUOUS_LISTEN_DURATION', 10)