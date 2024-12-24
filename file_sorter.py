import os
import shutil
import win32com.client
from win32com.shell import shell, shellcon
import pythoncom
from config_manager import load_config
from logger import get_logger
from history_manager import load_history, save_history
import datetime

logger = get_logger(__name__)

def get_desktop_path():
    """Получает путь к рабочему столу через WinAPI"""
    try:
        # Пробуем получить путь через WinAPI
        desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        if os.path.exists(desktop_path):
            logger.info(f"Найден путь к рабочему столу через WinAPI: {desktop_path}")
            return desktop_path
    except Exception as e:
        logger.warning(f"Не удалось получить путь к рабочему столу через WinAPI: {e}")
    
    # Пробуем стандартные пути
    possible_paths = [
        os.path.join(os.path.expanduser('~'), 'Desktop'),
        os.path.join(os.path.expanduser('~'), 'Рабочий стол'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Рабочий стол')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Найден путь к рабочему столу: {path}")
            return path
            
    raise FileNotFoundError("Не удалось найти путь к рабочему столу")

def create_shortcut(target_path, shortcut_path):
    """Создает ярлык для файла или папки"""
    try:
        pythoncom.CoInitialize()  # Инициализация COM
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.save()
        logger.info(f"Создан ярлык: {shortcut_path} -> {target_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании ярлыка {shortcut_path}: {e}")
        return False
    finally:
        pythoncom.CoUninitialize()  # Освобождение COM

def sort_desktop():
    """Сортирует файлы на рабочем столе согласно правилам"""
    logger.info("Начало процесса сортировки...")
    
    config = load_config()
    logger.info(f"Загружена конфигурация: {config}")
    
    desktop_path = get_desktop_path()
    logger.info(f"Путь к рабочему столу: {desktop_path}")
    
    organized_dir = config.get("organized_files_dir")
    logger.info(f"Директория для организованных файлов: {organized_dir}")
    
    if not organized_dir:
        logger.error("Не указана директория для организованных файлов")
        return
    
    if not os.path.exists(organized_dir):
        os.makedirs(organized_dir)
        logger.info(f"Создана директория для организованных файлов: {organized_dir}")
    
    # Загружаем историю
    history = load_history()
    current_operation = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "moved_files": []
    }
    
    try:
        items_on_desktop = os.listdir(desktop_path)
        logger.info(f"Найдено файлов на рабочем столе: {len(items_on_desktop)}")
        logger.info(f"Файлы на рабочем столе: {items_on_desktop}")
    except Exception as e:
        logger.error(f"Ошибка при чтении содержимого рабочего стола: {e}")
        return
    
    rules = config.get("sorting_rules", [])
    folder_mode = config.get("folder_shortcut_mode", "others")
    logger.info(f"Загружено правил сортировки: {len(rules)}")
    logger.info(f"Режим обработки папок: {folder_mode}")
    
    for item in items_on_desktop:
        item_path = os.path.join(desktop_path, item)
        logger.info(f"Обработка элемента: {item}")
        
        # Пропускаем ярлыки и специальные файлы
        if item.endswith('.lnk') or item.startswith('~$'):
            logger.info(f"Пропущен файл {item} (ярлык или специальный файл)")
            continue

        # Определяем правило для файла/папки
        matched_rule = None
        for rule in rules:
            if rule["type"] == "extension" and os.path.isfile(item_path):
                if item.lower().endswith(rule["extension"].lower()):
                    matched_rule = rule
                    logger.info(f"Найдено правило для файла {item}: {rule}")
                    break
            elif rule["type"] == "folder" and os.path.isdir(item_path):
                if item.lower() == rule["extension"].lower():
                    matched_rule = rule
                    logger.info(f"Найдено правило для папки {item}: {rule}")
                    break

        if matched_rule:
            # Создаем папку назначения если её нет
            target_folder = os.path.join(organized_dir, matched_rule["folder"])
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
                logger.info(f"Создана папка назначения: {target_folder}")
            
            # Перемещаем файл/папку
            target_path = os.path.join(target_folder, item)
            try:
                shutil.move(item_path, target_path)
                logger.info(f"Перемещен файл/папка: {item_path} -> {target_path}")
                
                # Создаем ярлык
                shortcut_path = os.path.join(desktop_path, f"{item}.lnk")
                if create_shortcut(target_path, shortcut_path):
                    current_operation["moved_files"].append((item_path, target_path))
                    logger.info(f"Операция успешно записана в историю")
            except Exception as e:
                logger.error(f"Ошибка при перемещении {item}: {e}")
        else:
            logger.info(f"Не найдено правило для {item}")
        
        # Обработка папок без правил
        if not matched_rule and os.path.isdir(item_path) and folder_mode:
            logger.info(f"Обработка папки без правила: {item}")
            others_folder = os.path.join(organized_dir, "Others")
            if folder_mode == "others":
                if not os.path.exists(others_folder):
                    os.makedirs(others_folder)
                    logger.info(f"Создана папка Others: {others_folder}")
                target_path = os.path.join(others_folder, item)
            else:  # per_folder
                target_path = os.path.join(organized_dir, item)
                
            try:
                if not os.path.exists(target_path):
                    shutil.move(item_path, target_path)
                    logger.info(f"Перемещена папка без правила: {item_path} -> {target_path}")
                    # Создаем ярлык
                    shortcut_path = os.path.join(desktop_path, f"{item}.lnk")
                    if create_shortcut(target_path, shortcut_path):
                        current_operation["moved_files"].append((item_path, target_path))
                        logger.info(f"Операция с папкой успешно записана в историю")
            except Exception as e:
                logger.error(f"Ошибка при перемещении папки {item}: {e}")
    
    # Сохраняем историю только если были перемещения
    if current_operation["moved_files"]:
        history.append(current_operation)
        save_history(history)
        logger.info(f"История обновлена. Добавлено {len(current_operation['moved_files'])} операций")
    else:
        logger.info("Нет файлов для перемещения или все файлы уже организованы")
