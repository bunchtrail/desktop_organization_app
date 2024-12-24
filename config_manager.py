import json
import os
from pathlib import Path

CONFIG_FILE = 'config.json'

def get_default_config():
    """Возвращает конфигурацию по умолчанию"""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(desktop_path):
        desktop_path = os.path.join(os.path.expanduser('~'), 'Рабочий стол')
    
    organized_path = os.path.join(desktop_path, 'Organized')
    
    return {
        "sorting_rules": [
            {"type": "extension", "extension": ".txt", "folder": "Documents"},
            {"type": "extension", "extension": ".pdf", "folder": "Documents"},
            {"type": "extension", "extension": ".doc", "folder": "Documents"},
            {"type": "extension", "extension": ".docx", "folder": "Documents"},
            {"type": "extension", "extension": ".jpg", "folder": "Images"},
            {"type": "extension", "extension": ".png", "folder": "Images"},
            {"type": "extension", "extension": ".jpeg", "folder": "Images"},
            {"type": "extension", "extension": ".mp3", "folder": "Music"},
            {"type": "extension", "extension": ".wav", "folder": "Music"},
            {"type": "extension", "extension": ".mp4", "folder": "Videos"},
            {"type": "extension", "extension": ".avi", "folder": "Videos"},
            {"type": "extension", "extension": ".zip", "folder": "Archives"},
            {"type": "extension", "extension": ".rar", "folder": "Archives"},
            {"type": "extension", "extension": ".7z", "folder": "Archives"}
        ],
        "organized_files_dir": organized_path,
        "check_interval": 300,
        "folder_shortcut_mode": "Others",
        "log_level": "INFO"
    }

def load_config():
    """Загружает конфигурацию из файла"""
    if not os.path.exists(CONFIG_FILE):
        default_config = get_default_config()
        save_config(default_config)
        return default_config
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Проверяем наличие всех необходимых параметров
            default_config = get_default_config()
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        return get_default_config()

def save_config(config):
    """Сохраняет конфигурацию в файл"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка при сохранении конфигурации: {e}")
