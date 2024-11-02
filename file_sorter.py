import os
import shutil
import time
import pythoncom
import win32com.client
from config_manager import load_config
from logger import get_logger

logger = get_logger(__name__)

def create_shortcut(target_path, shortcut_path, description=""):
    """
    Создает ярлык в Windows для target_path по указанному пути shortcut_path.
    """
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WindowStyle = 1
    shortcut.Description = description
    shortcut.save()

def sort_desktop():
    config = load_config()
    sorting_rules = config.get("sorting_rules", [])
    destination_dir = config.get("destination_dir", "")
    if not destination_dir:
        # Если директория назначения не выбрана пользователем, используем домашнюю папку пользователя
        destination_dir = os.path.join(os.path.expanduser('~'), "desktop_organizer")

    # Путь к рабочему столу
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    # Путь к папке "desktop_organizer" в выбранной директории назначения
    organizer_path = os.path.join(destination_dir, "desktop_organizer")

    if not os.path.exists(organizer_path):
        os.makedirs(organizer_path, exist_ok=True)

    logger.info("Starting sorting process. Organizer directory: %s", organizer_path)
    files_moved = 0

    for filename in os.listdir(desktop_path):
        file_path = os.path.join(desktop_path, filename)

        # Пропускаем системные файлы ярлыков и папки
        if os.path.isfile(file_path) and not filename.lower().endswith(".lnk"):
            file_extension = os.path.splitext(filename)[1].lower()

            moved = False
            for rule in sorting_rules:
                if rule["type"] == "extension" and file_extension == rule["extension"].lower():
                    target_folder = os.path.join(organizer_path, rule["folder"])
                    os.makedirs(target_folder, exist_ok=True)
                    target_path = os.path.join(target_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s'", filename, target_folder)
                    files_moved += 1
                    moved = True
                    # Создаем ярлык на рабочем столе, если его нет
                    shortcut_name = f"{rule['folder']}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(target_folder, shortcut_path, description=f"Shortcut to {rule['folder']} folder")
                    break

            # Если файл не был перемещён ни по одному правилу, пропускаем его
            if not moved:
                pass

    if files_moved == 0:
        logger.info("No files were moved. Desktop is already organized.")
    else:
        logger.info("Finished sorting process. %d files moved.", files_moved)
