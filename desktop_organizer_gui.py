import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config_manager import load_config, save_config
from file_sorter import sort_desktop
from logger import get_logger
from history_manager import load_history, save_history
import threading
import datetime
import shutil

logger = get_logger(__name__)

class DesktopOrganizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Организатор Рабочего Стола")
        self.configure(bg="#f0f0f0")
        self.geometry("600x550")
        self.resizable(True, True)  # позволяем изменение размеров окна
        
        self.config_data = load_config()
        self.monitor_thread = None
        self.monitoring = False
        
        # Стили
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', foreground='#333333', font=('Helvetica', 10))
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), foreground='#333333')
        style.configure('TButton', font=('Helvetica', 10), background='#007AFF', foreground='white', borderwidth=0)
        style.map('TButton', 
                  foreground=[('active', 'white'), ('disabled', '#ccc')], 
                  background=[('active', '#005BBB'), ('disabled', '#ccc')])

        # Создаём UI на основе вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Создание вкладок
        self.create_rules_tab()
        self.create_settings_tab()
        self.create_history_tab()
        self.create_control_tab()

        # Загружаем текущие настройки и обновляем UI
        self.load_current_config()
        
    def create_rules_tab(self):
        self.rules_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.rules_tab, text="Правила сортировки")

        header_frame = ttk.Frame(self.rules_tab)
        header_frame.pack(fill=tk.X)

        header_label = ttk.Label(header_frame, text="Правила сортировки", style='Header.TLabel')
        header_label.pack(pady=10)

        # Интерфейс правил сортировки
        rules_frame = ttk.Frame(self.rules_tab, padding="10")
        rules_frame.pack(fill=tk.BOTH, expand=True)

        self.rules_tree = ttk.Treeview(rules_frame, columns=("type", "extension", "folder"), show="headings")
        self.rules_tree.heading("type", text="Тип")
        self.rules_tree.heading("extension", text="Расширение/Папка")
        self.rules_tree.heading("folder", text="Папка назначения")
        self.rules_tree.column("type", width=80, anchor=tk.CENTER)
        self.rules_tree.column("extension", width=100, anchor=tk.CENTER)
        self.rules_tree.column("folder", width=200, anchor=tk.W)
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        rules_buttons_frame = ttk.Frame(self.rules_tab)
        rules_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.add_rule_button = ttk.Button(rules_buttons_frame, text="Добавить правило", command=self.add_rule_popup, style='TButton')
        self.add_rule_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_rule_button = ttk.Button(rules_buttons_frame, text="Удалить правило", command=self.remove_selected_rule, style='TButton')
        self.remove_rule_button.pack(side=tk.LEFT, padx=5)

    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="Настройки")

        header_frame = ttk.Frame(self.settings_tab)
        header_frame.pack(fill=tk.X)

        header_label = ttk.Label(header_frame, text="Настройки", style='Header.TLabel')
        header_label.pack(pady=10)

        # Настройки
        settings_frame = ttk.Frame(self.settings_tab, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        interval_label = ttk.Label(settings_frame, text="Интервал проверки (сек):")
        interval_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.interval_var = tk.IntVar()
        self.interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        destination_label = ttk.Label(settings_frame, text="Директория для организованных файлов:")
        destination_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.destination_var = tk.StringVar()
        self.destination_entry = ttk.Entry(settings_frame, textvariable=self.destination_var, width=50)
        self.destination_entry.grid(row=1, column=1, sticky=tk.W, pady=5, columnspan=2)

        # Настройка для обработки папок
        folder_shortcut_label = ttk.Label(settings_frame, text="Обработка папок без правил:")
        folder_shortcut_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.folder_shortcut_mode = tk.StringVar(value=self.config_data.get("folder_shortcut_mode", "others"))
        folder_mode_frame = ttk.Frame(settings_frame)
        folder_mode_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)

        folder_mode_others_rb = ttk.Radiobutton(folder_mode_frame, text="Создавать ярлык 'Others'", variable=self.folder_shortcut_mode, value="others")
        folder_mode_per_folder_rb = ttk.Radiobutton(folder_mode_frame, text="Создавать ярлык для каждой папки", variable=self.folder_shortcut_mode, value="per_folder")

        folder_mode_others_rb.pack(anchor=tk.W, pady=2)
        folder_mode_per_folder_rb.pack(anchor=tk.W, pady=2)

        # Buttons Frame
        buttons_frame = ttk.Frame(self.settings_tab, padding="10")
        buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_interval_button = ttk.Button(buttons_frame, text="Сохранить интервал", command=self.save_interval, style='TButton')
        save_interval_button.pack(side=tk.LEFT, padx=5, pady=10)

        save_folder_mode_button = ttk.Button(buttons_frame, text="Сохранить настройку папок", command=self.save_folder_mode, style='TButton')
        save_folder_mode_button.pack(side=tk.LEFT, padx=5, pady=10)

        choose_dir_button = ttk.Button(buttons_frame, text="Выбрать директорию", command=self.choose_destination_dir, style='TButton')
        choose_dir_button.pack(side=tk.LEFT, padx=5, pady=10)

    def create_history_tab(self):
        self.history_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.history_tab, text="История")

        header_frame = ttk.Frame(self.history_tab)
        header_frame.pack(fill=tk.X)

        header_label = ttk.Label(header_frame, text="История перемещений файлов", style='Header.TLabel')
        header_label.pack(pady=10)

        # История
        history_frame = ttk.Frame(self.history_tab)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_tree = ttk.Treeview(history_frame, columns=("timestamp", "details"), show="headings")
        self.history_tree.heading("timestamp", text="Время/Категория/Файл")
        self.history_tree.heading("details", text="Перемещённые файлы")
        self.history_tree.column("timestamp", width=250, anchor=tk.W)
        self.history_tree.column("details", width=350, anchor=tk.W)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Горизонтальная прокрутка
        h_scroll = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.history_tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.history_tree.configure(xscrollcommand=h_scroll.set)

        # Вертикальная прокрутка
        v_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=v_scroll.set)

        # Кнопки для управления историей
        history_buttons_frame = ttk.Frame(self.history_tab)
        history_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.refresh_history_button = ttk.Button(history_buttons_frame, text="Обновить", command=self.refresh_history, style='TButton')
        self.refresh_history_button.pack(side=tk.LEFT, padx=5)

        self.revert_history_button = ttk.Button(history_buttons_frame, text="Откатить выбранное", command=self.revert_selected_history, style='TButton')
        self.revert_history_button.pack(side=tk.LEFT, padx=5)

    def create_control_tab(self):
        self.control_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.control_tab, text="Управление")

        header_frame = ttk.Frame(self.control_tab)
        header_frame.pack(fill=tk.X)

        header_label = ttk.Label(header_frame, text="Управление сортировкой", style='Header.TLabel')
        header_label.pack(pady=10)

        # Контроль
        control_frame = ttk.Frame(self.control_tab, padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.sort_button = ttk.Button(control_frame, text="Отсортировать сейчас", command=self.sort_desktop_now, style='TButton')
        self.sort_button.pack(side=tk.LEFT, padx=5)
        
        self.monitor_button = ttk.Button(control_frame, text="Начать мониторинг", command=self.toggle_monitoring, style='TButton')
        self.monitor_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Статус: Ожидание...", foreground="#333333")
        self.status_label.pack(side=tk.RIGHT)

    def load_current_config(self):
        # Очистить список правил
        for row in self.rules_tree.get_children():
            self.rules_tree.delete(row)
        
        # Добавить правила из конфигурации
        for rule in self.config_data.get("sorting_rules", []):
            self.rules_tree.insert("", tk.END, values=(rule["type"], rule["extension"], rule["folder"]))
        
        self.interval_var.set(self.config_data.get("check_interval", 300))
        self.destination_var.set(self.config_data.get("destination_dir", ""))
        self.folder_shortcut_mode.set(self.config_data.get("folder_shortcut_mode", "others"))

        # Обновляем вкладку "История"
        self.refresh_history()
        
    def add_rule_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Добавить правило")
        popup.geometry("300x250")
        popup.resizable(False, False)
        
        rule_type_label = ttk.Label(popup, text="Тип правила:")
        rule_type_label.pack(pady=5)
        
        rule_type_var = tk.StringVar(value="extension")
        rule_type_combo = ttk.Combobox(popup, textvariable=rule_type_var, values=["extension", "folder"], state="readonly")
        rule_type_combo.pack(pady=5)
        
        extension_label = ttk.Label(popup, text="Расширение файла/название папки:")
        extension_label.pack(pady=5)
        
        extension_var = tk.StringVar(value="")
        extension_entry = ttk.Entry(popup, textvariable=extension_var)
        extension_entry.pack(pady=5)
        
        folder_label = ttk.Label(popup, text="Папка назначения:")
        folder_label.pack(pady=5)
        
        folder_var = tk.StringVar(value="")
        folder_entry = ttk.Entry(popup, textvariable=folder_var)
        folder_entry.pack(pady=5)
        
        def add_rule():
            rule_type = rule_type_var.get()
            extension = extension_var.get().strip()
            folder = folder_var.get().strip()

            if rule_type == "extension" and not extension.startswith("."):
                messagebox.showerror("Ошибка", "Расширение должно начинаться с точки, например: .txt")
                return

            if not extension or not folder:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
                return

            new_rule = {
                "type": rule_type,
                "extension": extension.lower(),
                "folder": folder
            }
            self.config_data["sorting_rules"].append(new_rule)
            save_config(self.config_data)
            self.load_current_config()
            popup.destroy()

        add_button = ttk.Button(popup, text="Добавить", command=add_rule, style='TButton')
        add_button.pack(pady=10)
        
    def remove_selected_rule(self):
        selected_item = self.rules_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите правило для удаления.")
            return
        item_values = self.rules_tree.item(selected_item, "values")
        extension_to_remove = item_values[1]  # Расширение файла/название папки

        new_rules = [r for r in self.config_data.get('sorting_rules', []) if r['extension'].lower() != extension_to_remove.lower()]
        self.config_data['sorting_rules'] = new_rules
        save_config(self.config_data)
        self.load_current_config()
        messagebox.showinfo("Успех", f"Правило для {extension_to_remove} удалено.")
        
    def save_interval(self):
        interval_value = self.interval_var.get()
        if interval_value <= 0:
            messagebox.showerror("Ошибка", "Интервал должен быть больше 0.")
            return
        self.config_data['check_interval'] = interval_value
        save_config(self.config_data)
        messagebox.showinfo("Успех", f"Интервал проверки установлен на {interval_value} секунд.")

    def choose_destination_dir(self):
        chosen_dir = filedialog.askdirectory()
        if chosen_dir:
            self.destination_var.set(chosen_dir)
            self.config_data['destination_dir'] = chosen_dir
            save_config(self.config_data)
            messagebox.showinfo("Успех", f"Директория для организованных файлов установлена: {chosen_dir}")

    def save_folder_mode(self):
        mode_value = self.folder_shortcut_mode.get()
        self.config_data['folder_shortcut_mode'] = mode_value
        save_config(self.config_data)
        if mode_value == 'others':
            message = 'Создавать ярлык "Others"'
        else:
            message = 'Создавать ярлык для каждой папки'
        messagebox.showinfo(
            "Успех",
            f"Настройка обработки папок установлена: {message}"
        )
        
    def sort_desktop_now(self):
        if not self.destination_var.get():
            messagebox.showwarning("Внимание", "Пожалуйста, выберите директорию для организованных файлов.")
            return
        sort_desktop()
        messagebox.showinfo("Успех", "Рабочий стол отсортирован.")
        self.refresh_history()
        
    def toggle_monitoring(self):
        if not self.monitoring:
            if not self.destination_var.get():
                messagebox.showwarning("Внимание", "Пожалуйста, выберите директорию для организованных файлов.")
                return
            self.monitoring = True
            self.monitor_button.configure(text="Остановить мониторинг")
            self.status_label.configure(text="Статус: Мониторинг включён", foreground="#007AFF")
            self.monitor_thread = threading.Thread(target=self.monitor_desktop_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.monitor_button.configure(text="Начать мониторинг")
            self.status_label.configure(text="Статус: Мониторинг остановлен", foreground="#d32f2f")
            
    def monitor_desktop_loop(self):
        interval = self.config_data.get("check_interval", 300)
        while self.monitoring:
            sort_desktop()
            self.refresh_history()
            time.sleep(interval)

    def refresh_history(self):
        # Обновляет историю в UI, сохраняя текущее состояние раскрытия дерева
        expanded_nodes = self.get_expanded_nodes(self.history_tree)
        
        history = load_history()
        self.history_tree.delete(*self.history_tree.get_children())
        
        for i, entry in enumerate(history):
            timestamp = entry["timestamp"]
            moved_files = entry["moved_files"]
            
            # Группируем файлы по папке назначения
            grouped_files = {}
            for old_path, new_path in moved_files:
                folder_name = os.path.basename(os.path.dirname(new_path))
                if folder_name not in grouped_files:
                    grouped_files[folder_name] = []
                grouped_files[folder_name].append((old_path, new_path))
            
            # Добавляем корневой элемент для каждой записи истории (по времени)
            entry_id = self.history_tree.insert("", tk.END, iid=f"entry_{i}", values=(f"Операция {i+1} - {timestamp}", ""))
            
            for category, files in grouped_files.items():
                # Добавляем узел категории
                category_node_id = self.history_tree.insert(entry_id, tk.END, values=(f"Категория: {category}", f"Перемещено объектов: {len(files)}"))
                for file_info in files:
                    old_path, new_path = file_info
                    self.history_tree.insert(category_node_id, tk.END, values=(os.path.basename(new_path), f"{old_path} -> {new_path}"))

        # Восстановление состояния раскрытия дерева
        self.restore_expanded_nodes(self.history_tree, expanded_nodes)

    def revert_selected_history(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите операцию или файл для отката.")
            return
        
        history = load_history()
        
        # Идентификатор выбранного элемента
        selected_id = selected_item[0]
        
        # Определяем тип узла (entry_*, категория, файл)
        if selected_id.startswith("entry_"):
            # Откат всей операции
            entry_index = int(selected_id.replace("entry_", ""))
            if entry_index < len(history):
                entry = history[entry_index]
                self.revert_entry(entry)
                # Удаляем операцию из истории только если все файлы откатаны
                if not entry["moved_files"]:
                    history.pop(entry_index)
                save_history(history)
                self.refresh_history()
                messagebox.showinfo("Успех", "Операция успешно откатана и файлы возвращены.")
            else:
                messagebox.showerror("Ошибка", "Не удалось найти выбранную операцию в истории.")
        else:
            # Узел категории или файл
            parent_id = self.history_tree.parent(selected_id)
            if not parent_id:
                # Если нет родителя, это корневой элемент - откатываем всю операцию
                entry_index = self.get_entry_index_from_node(selected_id)
                if entry_index < len(history):
                    entry = history[entry_index]
                    self.revert_entry(entry)
                    # Удаляем операцию из истории только если все файлы откатаны
                    if not entry["moved_files"]:
                        history.pop(entry_index)
                    save_history(history)
                    self.refresh_history()
                    messagebox.showinfo("Успех", "Операция успешно откатана и файлы возвращены.")
                else:
                    messagebox.showerror("Ошибка", "Не удалось найти операцию в истории.")
                return

            if parent_id.startswith("entry_"):
                # Это категория
                entry_index = int(parent_id.replace("entry_", ""))
                if entry_index < len(history):
                    entry = history[entry_index]
                    category_name = self.history_tree.item(selected_id, "values")[0].replace("Категория: ", "")
                    # Откат только файлов этой категории
                    self.revert_category(entry, category_name)
                    # Удаляем операцию из истории только если все файлы откатаны
                    if not entry["moved_files"]:
                        history.pop(entry_index)
                    save_history(history)
                    self.refresh_history()
                    messagebox.showinfo("Успех", f"Откатаны все объекты из категории {category_name}.")
                else:
                    messagebox.showerror("Ошибка", "Не удалось найти операцию в истории.")
            else:
                # Файл
                grand_parent_id = self.history_tree.parent(parent_id)
                if not grand_parent_id.startswith("entry_"):
                    messagebox.showerror("Ошибка", "Не удалось определить операцию в истории.")
                    return
                entry_index = int(grand_parent_id.replace("entry_", ""))
                if entry_index < len(history):
                    entry = history[entry_index]
                    file_values = self.history_tree.item(selected_id, "values")
                    if file_values:
                        # file_values[0] - имя файла/папки, file_values[1] - старый->новый путь
                        paths = file_values[1].split(" -> ")
                        if len(paths) == 2:
                            old_path, new_path = paths
                            # Откат отдельного файла
                            self.revert_file(entry, old_path, new_path)
                            # Удаляем операцию из истории только если все файлы откатаны
                            if not entry["moved_files"]:
                                history.pop(entry_index)
                            save_history(history)
                            self.refresh_history()
                            messagebox.showinfo("Успех", f"Объект {os.path.basename(new_path)} откатан.")
                else:
                    messagebox.showerror("Ошибка", "Не удалось найти операцию в истории.")

    def revert_entry(self, entry):
        # Откатывает всю операцию
        files_to_remove = []
        for file_info in entry["moved_files"]:
            old_path, new_path = file_info
            if self.revert_file_movement(old_path, new_path):
                files_to_remove.append(file_info)
        for f in files_to_remove:
            entry["moved_files"].remove(f)

    def revert_category(self, entry, category_name):
        # Откатывает все файлы в категории
        moved_files = entry["moved_files"]
        files_to_remove = []
        for file_info in moved_files:
            old_path, new_path = file_info
            folder_name = os.path.basename(os.path.dirname(new_path))
            if folder_name == category_name:
                if self.revert_file_movement(old_path, new_path):
                    files_to_remove.append(file_info)
        
        # Удаляем откатанные файлы из списка
        for f in files_to_remove:
            moved_files.remove(f)

    def revert_file(self, entry, old_path, new_path):
        # Откатывает отдельный файл
        moved_files = entry["moved_files"]
        for file_info in moved_files:
            if file_info[0] == old_path and file_info[1] == new_path:
                if self.revert_file_movement(old_path, new_path):
                    moved_files.remove(file_info)
                    break

    def revert_file_movement(self, old_path, new_path):
        # Возвращает True, если откат успешно выполнен
        if os.path.exists(new_path):
            os.makedirs(os.path.dirname(old_path), exist_ok=True)
            shutil.move(new_path, old_path)
            logger.info(f"Объект откатан: {new_path} -> {old_path}")
            return True
        else:
            logger.warning(f"Объект для отката не найден: {new_path}")
            return False

    def get_expanded_nodes(self, tree):
        # Возвращает список ID раскрытых узлов дерева
        expanded = []
        def _get_open_nodes(item):
            if tree.item(item, 'open'):
                expanded.append(item)
            children = tree.get_children(item)
            for child in children:
                _get_open_nodes(child)
        roots = tree.get_children('')
        for root in roots:
            _get_open_nodes(root)
        return expanded

    def restore_expanded_nodes(self, tree, expanded_nodes):
        # Восстанавливает состояние раскрытия узлов дерева
        for node in expanded_nodes:
            if tree.exists(node):
                tree.item(node, open=True)

    def get_entry_index_from_node(self, node_id):
        # Возвращает индекс операции из ID узла (формат 'entry_...')
        if node_id.startswith("entry_"):
            return int(node_id.replace("entry_", ""))
        return -1

if __name__ == "__main__":
    gui = DesktopOrganizerGUI()
    gui.mainloop()
