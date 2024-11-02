import json
import os
import datetime
import shutil
from logger import get_logger

logger = get_logger(__name__)

HISTORY_FILE = 'history.json'

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def add_history_entry(moved_files):
    """
    Добавляет запись об операции сортировки в историю.
    moved_files - список кортежей (old_path, new_path)
    """
    history = load_history()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "moved_files": moved_files
    }
    history.insert(0, entry)  # Добавляем запись в начало списка
    save_history(history)
    logger.debug(f"Добавлена запись в историю: {entry}")

def revert_history_entry(entry):
    """
    Откатывает изменения для конкретной записи, перемещая файлы обратно.
    """
    for file_info in entry["moved_files"]:
        old_path, new_path = file_info
        logger.debug(f"Откат файла: new_path='{new_path}' -> old_path='{old_path}'")
        if os.path.exists(new_path):
            # Создаём папку, если её нет
            os.makedirs(os.path.dirname(old_path), exist_ok=True)
            shutil.move(new_path, old_path)
            logger.info(f"Файл откатан: {new_path} -> {old_path}")
        else:
            logger.warning(f"Файл для отката не найден: {new_path}")
    # Запись из истории удалится после отката в DesktopOrganizerGUI.
