import json
import os

CONFIG_FILE = 'config.json'

default_config = {
    "sorting_rules": [
        {"type": "extension", "extension": ".png", "folder": "Images"},
        {"type": "extension", "extension": ".jpg", "folder": "Images"},
        {"type": "extension", "extension": ".docx", "folder": "Documents"},
        {"type": "extension", "extension": ".pdf", "folder": "Documents"}
    ],
    "check_interval": 300,  # интервал проверки в секундах
    "log_level": "INFO"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
