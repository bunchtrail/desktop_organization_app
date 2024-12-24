import os
import sys
import json
import shutil
from pathlib import Path

def create_default_config():
    """Создает конфигурацию по умолчанию"""
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(desktop_path):
        desktop_path = os.path.join(os.path.expanduser('~'), 'Рабочий стол')
    
    organized_path = os.path.join(desktop_path, 'Organized')
    
    default_config = {
        "check_interval": 300,
        "organized_files_dir": organized_path,
        "folder_shortcut_mode": "Others",
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
            {"type": "extension", "extension": ".7z", "folder": "Archives"},
        ]
    }
    return default_config

def setup_portable_environment():
    """Подготавливает окружение для портативного запуска"""
    # Создаем необходимые директории и файлы
    if not os.path.exists('config.json'):
        config = create_default_config()
        # Создаем директорию для организованных файлов
        if not os.path.exists(config["organized_files_dir"]):
            os.makedirs(config["organized_files_dir"], exist_ok=True)
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    if not os.path.exists('history.json'):
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

def main():
    """Основная функция запуска"""
    print("Подготовка к запуску Desktop Organizer...")
    setup_portable_environment()
    
    try:
        import desktop_organizer_gui
        desktop_organizer_gui.main()
    except ImportError as e:
        print(f"Ошибка при запуске приложения: {e}")
        print("Убедитесь, что установлены все необходимые зависимости:")
        print("pip install -r requirements.txt")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main() 