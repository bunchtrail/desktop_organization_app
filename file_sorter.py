import os
import shutil
import pythoncom
import win32com.client
from config_manager import load_config
from logger import get_logger
from history_manager import add_history_entry

logger = get_logger(__name__)

def create_shortcut(target_path, shortcut_path, description=""):
    """
    Создает ярлык в Windows, который открывает target_path (папку) с помощью проводника и параметра /e.
    """
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    # Устанавливаем полный путь к explorer.exe
    shortcut.TargetPath = r"C:\Windows\explorer.exe"
    # Нормализуем путь, чтобы использовать обратные слеши
    normalized_target = os.path.normpath(target_path)
    # Устанавливаем аргументы с нужным форматом
    shortcut.Arguments = f'/e,"{normalized_target}"'
    shortcut.Description = description
    shortcut.IconLocation = "shell32.dll,3"  # Иконка для папки
    shortcut.Save()

def sort_desktop():
    config = load_config()
    sorting_rules = config.get("sorting_rules", [])
    destination_dir = config.get("destination_dir", "")
    folder_shortcut_mode = config.get("folder_shortcut_mode", "others")  # "others" или "per_folder"

    if not destination_dir:
        # Если директория назначения не выбрана пользователем, используем папку desktop_organizer в домашней папке
        destination_dir = os.path.join(os.path.expanduser('~'), "desktop_organizer")

    # Путь к рабочему столу
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    # Путь к папке "desktop_organizer" в выбранной директории назначения
    organizer_path = os.path.join(destination_dir, "desktop_organizer")

    if not os.path.exists(organizer_path):
        os.makedirs(organizer_path, exist_ok=True)

    logger.info("Starting sorting process. Organizer directory: %s", organizer_path)
    moved_files_records = []

    items_on_desktop = os.listdir(desktop_path)
    for filename in items_on_desktop:
        file_path = os.path.join(desktop_path, filename)
        
        # Пропускаем системные файлы ярлыков (с расширением .lnk) и саму папку organizer
        if filename.lower().endswith(".lnk") or os.path.normpath(file_path) == os.path.normpath(organizer_path):
            continue

        if os.path.isfile(file_path):
            # Обработка файла
            file_extension = os.path.splitext(filename)[1].lower()

            moved = False
            for rule in sorting_rules:
                if rule["type"] == "extension" and file_extension == rule["extension"].lower():
                    target_folder = os.path.join(organizer_path, rule["folder"])
                    os.makedirs(target_folder, exist_ok=True)
                    target_path = os.path.join(target_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s'", filename, target_folder)
                    moved = True
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе, если его нет
                    shortcut_name = f"{rule['folder']}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(target_folder, shortcut_path, description=f"Shortcut to {rule['folder']} folder")
                    break
                elif rule["type"] == "folder" and file_extension == "" and rule["extension"].lower() in filename.lower():
                    # Если это правило для папки, а мы обрабатываем файл без расширения, чье имя содержит правило
                    target_folder = os.path.join(organizer_path, rule["folder"])
                    os.makedirs(target_folder, exist_ok=True)
                    target_path = os.path.join(target_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s'", filename, target_folder)
                    moved = True
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе, если его нет
                    shortcut_name = f"{rule['folder']}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(target_folder, shortcut_path, description=f"Shortcut to {rule['folder']} folder")
                    break

            if not moved:
                # Если для файла нет подходящего правила
                if folder_shortcut_mode == "others":
                    # Перемещаем его в общую папку "Others"
                    other_folder = os.path.join(organizer_path, "Others")
                    os.makedirs(other_folder, exist_ok=True)
                    target_path = os.path.join(other_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s' (Others)", filename, other_folder)
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе, если его нет (только для Others)
                    shortcut_name = "Others.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(other_folder, shortcut_path, description="Shortcut to Others folder")
                else:  # folder_shortcut_mode == "per_folder"
                    # Создаем отдельную папку для файла
                    individual_folder = os.path.join(organizer_path, f"Folder_{filename}")
                    os.makedirs(individual_folder, exist_ok=True)
                    target_path = os.path.join(individual_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved file '%s' to '%s'", filename, individual_folder)
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе для этой папки
                    shortcut_name = f"{filename}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(individual_folder, shortcut_path, description=f"Shortcut to folder of {filename}")

        elif os.path.isdir(file_path):
            # Обработка папки
            moved = False
            for rule in sorting_rules:
                # Если правило типа 'folder' и имя папки соответствует правилу
                if rule["type"] == "folder" and rule["extension"].lower() in filename.lower():
                    target_folder = os.path.join(organizer_path, rule["folder"])
                    os.makedirs(target_folder, exist_ok=True)
                    target_path = os.path.join(target_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved folder '%s' to '%s'", filename, target_folder)
                    moved = True
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе, если его нет
                    shortcut_name = f"{rule['folder']}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(target_folder, shortcut_path, description=f"Shortcut to {rule['folder']} folder")
                    break

            if not moved:
                # Если для папки нет подходящего правила
                if folder_shortcut_mode == "others":
                    # Перемещаем её в папку "Others"
                    other_folder = os.path.join(organizer_path, "Others")
                    os.makedirs(other_folder, exist_ok=True)
                    target_path = os.path.join(other_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved folder '%s' to '%s' (Others)", filename, other_folder)
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе, если его нет (только для Others)
                    shortcut_name = "Others.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(other_folder, shortcut_path, description="Shortcut to Others folder")
                else:  # folder_shortcut_mode == "per_folder"
                    # Создаем папку для этой конкретной папки, называем её по имени папки
                    individual_folder = os.path.join(organizer_path, f"Folder_{filename}")
                    os.makedirs(individual_folder, exist_ok=True)
                    target_path = os.path.join(individual_folder, filename)
                    shutil.move(file_path, target_path)
                    logger.info("Moved folder '%s' to '%s'", filename, individual_folder)
                    moved_files_records.append((file_path, target_path))
                    # Создаем ярлык на рабочем столе для этой папки
                    shortcut_name = f"{filename}.lnk"
                    shortcut_path = os.path.join(desktop_path, shortcut_name)
                    if not os.path.exists(shortcut_path):
                        create_shortcut(individual_folder, shortcut_path, description=f"Shortcut to {filename} folder")

    if not moved_files_records:
        logger.info("No files or folders were moved. Desktop is already organized.")
    else:
        logger.info("Finished sorting process. Moved %d item(s).", len(moved_files_records))
        # Записываем перемещения в историю
        add_history_entry(moved_files_records)
