import json
import os
import datetime
import shutil
from logger import get_logger

logger = get_logger(__name__)

HISTORY_FILE = 'history.json'

def initialize_history():
    """Инициализирует файл истории с пустым списком"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        logger.info("Создан новый файл истории")
    except Exception as e:
        logger.error(f"Ошибка при инициализации файла истории: {e}")

def load_history():
    """Загружает историю из файла"""
    try:
        if not os.path.exists(HISTORY_FILE):
            initialize_history()
            return []
            
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:  # Если файл пустой
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении файла истории: {e}")
        initialize_history()
        return []
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при загрузке истории: {e}")
        return []

def save_history(history):
    """Сохраняет историю в файл"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        logger.info("История успешно сохранена")
    except Exception as e:
        logger.error(f"Ошибка при сохранении истории: {e}")

def add_history_entry(moved_files):
    """
    Добавляет запись об операции сортировки в историю.
    moved_files - список кортежей (old_path, new_path)
    """
    try:
        history = load_history()
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "moved_files": moved_files
        }
        history.insert(0, entry)  # Добавляем запись в начало списка
        save_history(history)
        logger.info(f"Добавлена новая запись в историю")
        logger.debug(f"Детали записи: {entry}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении записи в историю: {e}")

def revert_history_entry(entry):
    """
    Откатывает изменения для конкретной записи, перемещая файлы обратно.
    """
    try:
        for file_info in entry["moved_files"]:
            old_path, new_path = file_info
            logger.debug(f"Откат файла: {new_path} -> {old_path}")
            if os.path.exists(new_path):
                # Создаём папку, если её нет
                os.makedirs(os.path.dirname(old_path), exist_ok=True)
                shutil.move(new_path, old_path)
                logger.info(f"Файл успешно откатан: {new_path} -> {old_path}")
            else:
                logger.warning(f"Файл для отката не найден: {new_path}")
    except Exception as e:
        logger.error(f"Ошибка при откате изменений: {e}")
    # Запись из истории удалится после отката в DesktopOrganizerGUI
