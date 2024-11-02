import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config_manager import load_config, save_config
from monitor import start_monitoring
from file_sorter import sort_desktop
from logger import get_logger
import threading

logger = get_logger(__name__)

class DesktopOrganizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Организатор Рабочего Стола")
        self.configure(bg="#f0f0f0")
        self.geometry("600x500")
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

        # Создаём UI
        self.create_widgets()
        
        # Загружаем текущие настройки в UI
        self.load_current_config()
        
    def create_widgets(self):
        header_frame = ttk.Frame(self, padding="10")
        header_frame.pack(fill=tk.X)
        
        header_label = ttk.Label(header_frame, text="Организатор Рабочего Стола", style='Header.TLabel')
        header_label.pack(pady=10)
        
        # Интерфейс правил сортировки
        rules_frame = ttk.LabelFrame(self, text="Правила сортировки", padding="10")
        rules_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.rules_tree = ttk.Treeview(rules_frame, columns=("type", "extension", "folder"), show="headings")
        self.rules_tree.heading("type", text="Тип")
        self.rules_tree.heading("extension", text="Расширение")
        self.rules_tree.heading("folder", text="Папка назначения")
        self.rules_tree.column("type", width=80, anchor=tk.CENTER)
        self.rules_tree.column("extension", width=100, anchor=tk.CENTER)
        self.rules_tree.column("folder", width=200, anchor=tk.W)
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        
        rules_buttons_frame = ttk.Frame(rules_frame)
        rules_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.add_rule_button = ttk.Button(rules_buttons_frame, text="Добавить правило", command=self.add_rule_popup, style='TButton')
        self.add_rule_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_rule_button = ttk.Button(rules_buttons_frame, text="Удалить правило", command=self.remove_selected_rule, style='TButton')
        self.remove_rule_button.pack(side=tk.LEFT, padx=5)
        
        # Настройки
        settings_frame = ttk.LabelFrame(self, text="Настройки", padding="10")
        settings_frame.pack(fill=tk.X, expand=True, padx=10, pady=5)
        
        interval_label = ttk.Label(settings_frame, text="Интервал проверки (сек):")
        interval_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.interval_var = tk.IntVar()
        self.interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        save_interval_button = ttk.Button(settings_frame, text="Сохранить интервал", command=self.save_interval, style='TButton')
        save_interval_button.grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)

        destination_label = ttk.Label(settings_frame, text="Директория для организованных файлов:")
        destination_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.destination_var = tk.StringVar()
        self.destination_entry = ttk.Entry(settings_frame, textvariable=self.destination_var, width=50)
        self.destination_entry.grid(row=1, column=1, sticky=tk.W, pady=5, columnspan=2)

        choose_dir_button = ttk.Button(settings_frame, text="Выбрать...", command=self.choose_destination_dir, style='TButton')
        choose_dir_button.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Кнопки управления
        control_frame = ttk.Frame(self, padding="10")
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
        
    def add_rule_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Добавить правило")
        popup.geometry("300x200")
        popup.resizable(False, False)
        
        rule_type_label = ttk.Label(popup, text="Тип правила:")
        rule_type_label.pack(pady=5)
        
        rule_type_var = tk.StringVar(value="extension")
        rule_type_combo = ttk.Combobox(popup, textvariable=rule_type_var, values=["extension"], state="readonly")
        rule_type_combo.pack(pady=5)
        
        extension_label = ttk.Label(popup, text="Расширение файла:")
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

            if not extension.startswith("."):
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
        extension_to_remove = item_values[1]  # Расширение файла

        new_rules = [r for r in self.config_data.get('sorting_rules', []) if r['extension'].lower() != extension_to_remove.lower()]
        self.config_data['sorting_rules'] = new_rules
        save_config(self.config_data)
        self.load_current_config()
        messagebox.showinfo("Успех", f"Правило для расширения {extension_to_remove} удалено.")
        
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
        
    def sort_desktop_now(self):
        if not self.destination_var.get():
            messagebox.showwarning("Внимание", "Пожалуйста, выберите директорию для организованных файлов.")
            return
        sort_desktop()
        messagebox.showinfo("Успех", "Рабочий стол отсортирован.")
        
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
            time.sleep(interval)

if __name__ == "__main__":
    gui = DesktopOrganizerGUI()
    gui.mainloop()
