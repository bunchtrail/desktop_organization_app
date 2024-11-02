import os
import shutil
import time
from config_manager import load_config
from logger import get_logger

logger = get_logger(__name__)

def sort_desktop():
    config = load_config()
    sorting_rules = config.get("sorting_rules", [])
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')  # путь к рабочему столу пользователя

    logger.info("Starting sorting process on desktop: %s", desktop_path)
    files_moved = 0

    for filename in os.listdir(desktop_path):
        file_path = os.path.join(desktop_path, filename)

        if os.path.isfile(file_path):
            file_extension = os.path.splitext(filename)[1].lower()

            # Перебираем правила сортировки
            for rule in sorting_rules:
                if rule["type"] == "extension" and file_extension == rule["extension"].lower():
                    target_folder = os.path.join(desktop_path, rule["folder"])
                    os.makedirs(target_folder, exist_ok=True)
                    target_path = os.path.join(target_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s'", filename, target_folder)
                    files_moved += 1
                    break

    if files_moved == 0:
        logger.info("No files were moved. Desktop is already organized.")
    else:
        logger.info("Finished sorting process. %d files moved.", files_moved)
