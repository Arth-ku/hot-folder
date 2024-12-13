import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import win32print
from PIL import Image, ImageTk
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
from datetime import datetime
import threading
import pystray
from pystray import MenuItem as item
import io
import base64
import json
import psutil

LOCK_FILE = "app.lock"

class Watcher:
    DIRECTORY_TO_WATCH = r"C:\DatexLabels"  

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
# Sorting
class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None
        else:
            filepath = event.src_path
            if filepath.lower().endswith(('.pdf', '.zpl')):
                if wait_for_file(filepath):
                    print_file(filepath)
                    archive_file(filepath)

def wait_for_file(filepath, timeout=10, check_interval=0.5):
    start_time = time.time()
    initial_size = os.path.getsize(filepath)

    while time.time() - start_time < timeout:
        time.sleep(check_interval)
        current_size = os.path.getsize(filepath)
        if current_size == initial_size:
            return True
        initial_size = current_size

    return False

def load_config():
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {
            "zpl_printer": "",
            "sumatra_path": "",
            "prefix_printer_map": {}
        }
    return config

def save_config(config):
    with open('config.json', 'w') as file:
        json.dump(config, file)

def get_printer_for_file(filename, prefix_printer_map):
    prefix = filename[:3].upper()
    printer = prefix_printer_map.get(prefix)
    return printer

def print_file(filepath):
    config = load_config()
    zpl_printer = config['zpl_printer']
    sumatra_path = config['sumatra_path']
    prefix_printer_map = config['prefix_printer_map']
    filename = os.path.basename(filepath)
    
    try:
        if filepath.lower().endswith('.zpl'):
            with open(filepath, 'rb') as file:
                raw_data = file.read()
            hPrinter = win32print.OpenPrinter(zpl_printer)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("ZPL Print Job", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, raw_data)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hJob)
            finally:
                win32print.ClosePrinter(hPrinter)
        elif filepath.lower().endswith('.pdf'):
            printer = get_printer_for_file(filename, prefix_printer_map)
            if not printer:
                return
            subprocess.run([sumatra_path, '-print-to', printer, os.path.abspath(filepath)], check=True)
    except Exception as e:
        pass

def archive_file(filepath):
    archive_folder = r"C:\DatexLabels\archive"  
    today_folder = os.path.join(archive_folder, datetime.now().strftime('%Y-%m-%d'))

    try:
        if not os.path.exists(archive_folder):
            raise FileNotFoundError(f"Archive folder does not exist: {archive_folder}")
        
        if not os.path.exists(today_folder):
            os.makedirs(today_folder)
        shutil.move(filepath, os.path.join(today_folder, os.path.basename(filepath)))
    except Exception as e:
        error_message = f"Failed to archive file {filepath}. Error: {e}"
        app.display_error(error_message)

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hot Folder Monitor")
        self.root.geometry("800x600")
        self.warning_shown = False

        self.config = load_config()

        self.create_widgets()
        self.update_config_display()
        # UI and pswd (without _images loop)
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text='Configuration')

        self.config_text = tk.Text(self.config_frame, wrap='word', state='disabled')
        self.config_text.pack(expand=True, fill='both', padx=10, pady=10)

        self.printers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.printers_frame, text='Printers')

        self.printer_labels = []
        self.printer_dropdowns = []
        self.prefix_entries = []

        self.password_prompted = False
        self.password_correct = False

        self.password_frame = ttk.Frame(self.printers_frame)
        self.password_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.password_label = ttk.Label(self.password_frame, text="Enter Password:")
        self.password_label.grid(row=0, column=0, padx=5, pady=5)

        self.password_entry = ttk.Entry(self.password_frame, show='*')
        self.password_entry.grid(row=0, column=1, padx=5, pady=5)

        self.password_button = ttk.Button(self.password_frame, text="Submit", command=self.check_password)
        self.password_button.grid(row=0, column=2, padx=5, pady=5)

        self.zpl_printer_label = ttk.Label(self.printers_frame, text="ZPL Printer:")
        self.zpl_printer_label.grid(row=1, column=0, padx=10, pady=5)

        self.zpl_printer_dropdown = ttk.Combobox(self.printers_frame, values=self.get_printers(), state='readonly')
        self.zpl_printer_dropdown.grid(row=1, column=1, padx=10, pady=5)
        self.zpl_printer_dropdown.set(self.config['zpl_printer'])

        self.sumatra_path_label = ttk.Label(self.printers_frame, text="Sumatra Path:")
        self.sumatra_path_label.grid(row=2, column=0, padx=10, pady=5)

        self.sumatra_path_entry = ttk.Entry(self.printers_frame)
        self.sumatra_path_entry.grid(row=2, column=1, padx=10, pady=5)
        self.sumatra_path_entry.insert(0, self.config['sumatra_path'])

        self.sumatra_browse_button = ttk.Button(self.printers_frame, text="Browse", command=self.browse_sumatra)
        self.sumatra_browse_button.grid(row=2, column=2, padx=10, pady=5)

        for i in range(5):
            prefix_label = ttk.Label(self.printers_frame, text=f"Prefix {i+1}:")
            prefix_label.grid(row=3+i, column=0, padx=10, pady=5)
            self.printer_labels.append(prefix_label)

            prefix_entry = ttk.Entry(self.printers_frame)
            prefix_entry.grid(row=3+i, column=1, padx=10, pady=5)
            self.prefix_entries.append(prefix_entry)

            dropdown = ttk.Combobox(self.printers_frame, values=self.get_printers(), state='readonly')
            dropdown.grid(row=3+i, column=2, padx=10, pady=5)
            self.printer_dropdowns.append(dropdown)

            if i < len(self.config['prefix_printer_map']):
                prefix_entry.insert(0, list(self.config['prefix_printer_map'].keys())[i])
                dropdown.set(list(self.config['prefix_printer_map'].values())[i])

        self.save_button = ttk.Button(self.printers_frame, text="Save", command=self.save_config)
        self.save_button.grid(row=8, column=0, columnspan=3, pady=10)
        self.save_button.config(state='disabled')

        self.error_frame = ttk.Frame(self.root)
        self.error_frame.pack(fill='x')

        self.error_label = ttk.Label(self.error_frame, text="", foreground='red')
        self.error_label.pack(padx=10, pady=10)

    def check_password(self):
        if self.password_entry.get() == '1234':
            self.password_correct = True
            self.enable_editing()
        else:
            messagebox.showerror("Error", "Incorrect password.")
            self.password_entry.delete(0, tk.END)

    def enable_editing(self):
        self.zpl_printer_dropdown.config(state='normal')
        self.sumatra_path_entry.config(state='normal')
        for dropdown in self.printer_dropdowns:
            dropdown.config(state='normal')
        self.save_button.config(state='normal')

    def browse_sumatra(self):
        file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file_path:
            self.sumatra_path_entry.delete(0, tk.END)
            self.sumatra_path_entry.insert(0, file_path)

    def save_config(self):
        self.config['zpl_printer'] = self.zpl_printer_dropdown.get()
        self.config['sumatra_path'] = self.sumatra_path_entry.get()
        self.config['prefix_printer_map'] = {}
        for i in range(len(self.prefix_entries)):
            prefix = self.prefix_entries[i].get()
            printer = self.printer_dropdowns[i].get()
            if prefix:
                self.config['prefix_printer_map'][prefix] = printer
        save_config(self.config)
        self.update_config_display()

    def update_config_display(self):
        self.config_text.config(state='normal')
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(tk.END, json.dumps(self.config, indent=4))
        self.config_text.config(state='disabled')

    def get_printers(self):
        return [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]

    def on_close(self):
        remove_lock_file()
        self.root.destroy()

    def display_error(self, message):
        self.error_label.config(text=message)

    def hide_window(self):
        self.root.withdraw()
        self.create_tray_icon()
# funct. for image from base64 wolf wwith yellow moon
    def create_tray_icon(self):
        try:
            icon_data = """
            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
            """
            image = Image.open(io.BytesIO(base64.b64decode(icon_data)))
            menu = (item('Quit', self.on_quit), item('Show', self.show_window))
            self.tray_icon = pystray.Icon("HotFolderMonitor", image, "Hot Folder Monitor", menu)
            self.tray_icon.run()
        except Exception as e:
            print(f"Error creating tray icon: {e}")

    def show_window(self):
        self.root.deiconify()
        self.tray_icon.stop()

    def on_quit(self):
        self.tray_icon.stop()
        self.root.quit()

def is_already_running():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == "python.exe" and proc.pid != os.getpid():
            for arg in proc.cmdline():
                if "Split_Print_v2.py" in arg:
                    return True
    return False

def remove_lock_file():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception as e:
        pass
# tpl. lock 
if __name__ == '__main__':
    if is_already_running():
        messagebox.showerror("Error", "Another instance of this application is already running.")
    else:
        try:
            root = tk.Tk()
            app = ConfigApp(root)

            watcher = Watcher()
            watcher_thread = threading.Thread(target=watcher.run)
            watcher_thread.daemon = True
            watcher_thread.start()

            root.protocol("WM_DELETE_WINDOW", app.hide_window)

            root.mainloop()
        finally:
            remove_lock_file()
