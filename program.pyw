import os
import sys
import zipfile
import subprocess
import json
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

# Ścieżka do folderu Dokumenty użytkownika
DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "project_manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "mod_manager_config.json")

# Automatyczne tworzenie folderu w Dokumentach, jeśli nie istnieje
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Ikona zakodowana w Base64 (Integralna część kodu)
ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
    "jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAGuSURBVGhD7ZmxSgNBFIbH3Egg2Nj5Arb2VvEB"
    "fAI7X8POB7C29lY+gK2lhYWFhYVlCmsLwSpEmptvsiuTzC5hk8vMhT8ILNnJ/Hvnz+zMzs6iKIri"
    "f1Nu/4QQXyqVSoUQQrVa3fT9h2Bv72D/IOj3+yN0XJalVqvVDZ/pX8hM3qD19m/WpZ1sNnsNXZal"
    "Wq3WBX0YgJ1sNvsIunlEa4CdnN3A1wO0BthJ0T2D/hV0WZZms1kDfdzAjg/oZ2YFvUBrgJ1sNvsI"
    "unlEa4CdFN0z6F9Bl2VpNps10McN7PiAfmZW0Au0BtjJZrOPoJtHtAbYSdE9g/4VdFmWZrNZA33c"
    "wI4P6GdmBb1Aa4CdbDb7CLp5RGuAnRTdM+hfQZdlaTabNdDHDez4gH5mVtALtAbYyWazj6CbR7QG"
    "2EnRPYP+FXRZlmavV98+f7WDLctSr9fr6OMR9C+gy/eQZalWq3X04RH0+R6yLNVisdglfYxofb3Z"
    "bF5Bxz/sZMq2zV+eZf7kM/0Lmbn7oG9WqVQqhBCq1eqm7/8Hj8fjeDweozgBx6i6D6a8t+2/0Icf"
    "f2Oa7lT/4WkAAAAASUVORK5CYII="
)

class ModManagerApp:
    def __init__(self, root, passed_zip=None):
        self.root = root
        self.root.title("Minecraft Smart Mod Manager")
        self.root.geometry("580x560")
        
        try:
            self.icon_img = tk.PhotoImage(data=ICON_BASE64)
            self.root.iconphoto(True, self.icon_img)
        except Exception:
            pass
        
        self.project_dir = tk.StringVar()
        self.downloads_dir = tk.StringVar()
        self.load_config()
        
        self.passed_zip = passed_zip

        # Wykryte platformy w projekcie
        self.detected_platforms = {"fabric": False, "neoforge": False, "forge": False}

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', font=('Segoe UI', 10))
        self.style.configure('Main.TButton', font=('Segoe UI', 10, 'bold'), padding=6)
        self.style.configure('Build.TButton', font=('Segoe UI', 12, 'bold'), padding=10, background='#0078D4', foreground='white')
        self.style.configure('Dump.TButton', font=('Segoe UI', 11, 'bold'), padding=8, background='#D13438', foreground='white')
        
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.detect_project_platforms()
        
        if self.passed_zip:
            self.handle_passed_zip(self.passed_zip)

    def create_widgets(self):
        path_frame = ttk.LabelFrame(self.main_frame, text=" 📂 Konfiguracja Ścieżek projektu ", padding="10")
        path_frame.pack(fill="x", pady=5)

        ttk.Label(path_frame, text="Folder główny projektu (gdzie jest gradlew):").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(path_frame, textvariable=self.project_dir, width=48).grid(row=1, column=0, pady=2, padx=(0,5))
        ttk.Button(path_frame, text="Przeglądaj...", command=self.browse_project).grid(row=1, column=1, pady=2)

        ttk.Label(path_frame, text="Folder z pobranymi ZIPami od Claude:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(path_frame, textvariable=self.downloads_dir, width=48).grid(row=3, column=0, pady=2, padx=(0,5))
        ttk.Button(path_frame, text="Przeglądaj...", command=self.browse_downloads).grid(row=3, column=1, pady=2)

        self.platform_status_label = ttk.Label(path_frame, text="🔍 Stan projektu: Brak wykrytego folderu", font=('Segoe UI', 9, 'italic'))
        self.platform_status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        zip_frame = ttk.LabelFrame(self.main_frame, text=" 📦 Wypakowywanie Kodu (Modyfikacje Claude) ", padding="10")
        zip_frame.pack(fill="both", expand=True, pady=10)

        ttk.Label(zip_frame, text="Wybierz plik ZIP do wstrzyknięcia do projektu:").pack(anchor="w")
        
        self.zip_listbox = tk.Listbox(zip_frame, height=5, font=('Segoe UI', 9))
        self.zip_listbox.pack(fill="both", expand=True, pady=5)
        self.refresh_zip_list()

        btn_zip_frame = ttk.Frame(zip_frame)
        btn_zip_frame.pack(fill="x", pady=2)
        ttk.Button(btn_zip_frame, text="🔄 Odśwież listę", command=self.refresh_zip_list).pack(side="left", padx=2)
        ttk.Button(btn_zip_frame, text="📥 WYPAKUJ I NADPISZ STRUKTURĘ", style='Main.TButton', command=self.unpack_selected_zip).pack(side="right", padx=2)

        build_frame = ttk.Frame(self.main_frame)
        build_frame.pack(fill="x", pady=5)

        self.build_btn = ttk.Button(build_frame, text="🛠️ PANEL GRADLE (AUTODETEKCJA SYSTEMU)", style='Build.TButton', command=self.open_multi_build_window)
        self.build_btn.pack(fill="x", ipady=3, pady=(0, 5))

        self.dump_btn = ttk.Button(build_frame, text="🚨 DUMP ERRORS (TOOLS)", style='Dump.TButton', command=self.execute_dump_errors)
        self.dump_btn.pack(fill="x", ipady=3)

    def detect_project_platforms(self):
        target = self.project_dir.get()
        self.detected_platforms = {"fabric": False, "neoforge": False, "forge": False}
        
        if not target or not os.path.exists(target):
            self.platform_status_label.config(text="❌ Wskazany folder projektu nie istnieje.", foreground="red")
            return

        settings_files = ["settings.gradle", "settings.gradle.kts"]
        settings_content = ""
        for file_name in settings_files:
            file_path = os.path.join(target, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        settings_content += f.read().lower()
                except:
                    pass
        if "fabric" in settings_content or os.path.exists(os.path.join(target, "fabric")):
            self.detected_platforms["fabric"] = True
        if "neoforge" in settings_content or os.path.exists(os.path.join(target, "neoforge")):
            self.detected_platforms["neoforge"] = True
        if "forge" in settings_content and not self.detected_platforms["neoforge"] or os.path.exists(os.path.join(target, "forge")):
            self.detected_platforms["forge"] = True

        found = [k for k, v in self.detected_platforms.items() if v]
        if found:
            display_names = [f.capitalize() for f in found]
            self.platform_status_label.config(text=f"✅ Wykryto strukturę: {', '.join(display_names)}", foreground="green")
        else:
            if os.path.exists(os.path.join(target, "build.gradle")) or os.path.exists(os.path.join(target, "build.gradle.kts")):
                self.platform_status_label.config(text="✅ Wykryto projekt standardowy (Jedno-platformowy)", foreground="blue")
            else:
                self.platform_status_label.config(text="⚠️ Nie wykryto projektu Minecraft w tym folderze.", foreground="orange")

    def browse_project(self):
        directory = filedialog.askdirectory(title="Wybierz folder projektu")
        if directory:
            self.project_dir.set(os.path.normpath(directory))
            self.save_config()
            self.detect_project_platforms()
            self.refresh_zip_list()

    def browse_downloads(self):
        directory = filedialog.askdirectory(title="Wybierz folder pobierania")
        if directory:
            self.downloads_dir.set(os.path.normpath(directory))
            self.save_config()
            self.refresh_zip_list()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.project_dir.set(config.get("project_dir", ""))
                    self.downloads_dir.set(config.get("downloads_dir", ""))
                    return
            except:
                pass
        self.project_dir.set(r"C:\projekty\w_trakcie")
        self.downloads_dir.set(os.path.join(os.path.expanduser("~"), "Downloads"))

    def save_config(self):
        config = {"project_dir": self.project_dir.get(), "downloads_dir": self.downloads_dir.get()}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def refresh_zip_list(self):
        self.zip_listbox.delete(0, tk.END)
        dl_path = self.downloads_dir.get()
        if os.path.exists(dl_path):
            try:
                files = [f for f in os.listdir(dl_path) if f.lower().endswith('.zip')]
                files.sort(key=lambda x: os.path.getmtime(os.path.join(dl_path, x)), reverse=True)
                for f in files:
                    self.zip_listbox.insert(tk.END, f)
            except Exception as e:
                self.zip_listbox.insert(tk.END, f"Błąd wczytywania: {str(e)}")

    def unpack_selected_zip(self):
        selected_index = self.zip_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Brak wyboru", "Zaznacz plik ZIP!")
            return
        self.extract_logic(os.path.join(self.downloads_dir.get(), self.zip_listbox.get(selected_index)))

    def handle_passed_zip(self, zip_path):
        if os.path.exists(zip_path) and zip_path.lower().endswith('.zip'):
            if messagebox.askyesno("Przeciągnięto plik", f"Wypakować {os.path.basename(zip_path)}?"):
                self.extract_logic(zip_path)

    def extract_logic(self, zip_path):
        target = self.project_dir.get()
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target)
            messagebox.showinfo("Wypakowano", "Pomyślnie zaktualizowano pliki projektu.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd: {str(e)}")

    def execute_dump_errors(self):
        target = self.project_dir.get()
        if not target or not os.path.exists(target):
            messagebox.showerror("Błąd", "Wskaż najpierw prawidłowy folder projektu!")
            return
        
        # ZMIANA: Zastąpiono cmd /k parametrem cmd /c, aby okno zamknęło się od razu po wykonaniu skryptu errlog.py
        full_command = f'cmd.exe /c "python tools/errlog.py build.log --md errors.md"'
        subprocess.Popen(f'start cmd /c "cd /d {target} && {full_command}"', shell=True)
            
    def open_multi_build_window(self):
        target = self.project_dir.get()
        gradlew_path = os.path.join(target, "gradlew.bat")
        if not os.path.exists(gradlew_path):
            messagebox.showerror("Błąd", "Brak pliku gradlew.bat!")
            return

        self.detect_project_platforms()
        build_win = tk.Toplevel(self.root)
        build_win.title("Dopasowany Panel Gradle")
        build_win.geometry("500x380")
        build_win.transient(self.root)
        build_win.grab_set()

        ttk.Label(build_win, text="Uruchom zadanie Gradle (Dopasowane do projektu):", font=('Segoe UI', 11, 'bold')).pack(pady=10)
        notebook = ttk.Notebook(build_win)
        notebook.pack(fill="both", expand=True, padx=15, pady=5)

        def execute_gradle(task_command):
            build_win.destroy()
            # ZMIANA: Zastąpiono cmd /k parametrem cmd /c, dzięki czemu po skończeniu zadania Gradle terminal sam zniknie z ekranu
            subprocess.Popen(f'start cmd /c "cd /d {target} && gradlew.bat {task_command} --no-daemon > build.log 2>&1"', shell=True)

        def create_tab(tab_title, task_dict):
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=tab_title)
            for label, command in task_dict.items():
                ttk.Button(frame, text=label, width=45, command=lambda cmd=command: execute_gradle(cmd)).pack(pady=5)

        tasks_global = {"🧹 Wyczyść pamięć podręczną (clean)": "clean"}
        if any(self.detected_platforms.values()):
            tasks_global["🏗️ Zbuduj wszystkie platformy (buildAll)"] = "buildAll"
        else:
            tasks_global["📦 Zbuduj projekt standardowy (build)"] = "build"
            tasks_global["🎮 Uruchom Klienta (runClient)"] = "runClient"
            
        create_tab("🌐 Ogólne", tasks_global)

        if self.detected_platforms["neoforge"]:
            create_tab("🔥 NeoForge", {
                "🎮 Uruchom Klienta NeoForge (:neoforge:runClient)": ":neoforge:runClient",
                "🖥️ Uruchom Serwer NeoForge (:neoforge:runServer)": ":neoforge:runServer",
                "📦 Buduj moduł NeoForge (:neoforge:build)": ":neoforge:build"
            })

        if self.detected_platforms["fabric"]:
            create_tab("🧬 Fabric", {
                "🎮 Uruchom Klienta Fabric (:fabric:runClient)": ":fabric:runClient",
                "🖥️ Uruchom Serwer Fabric (:fabric:runServer)": ":fabric:runServer",
                "📦 Buduj moduł Fabric (:fabric:build)": ":fabric:build"
            })

        if self.detected_platforms["forge"]:
            create_tab("🛠️ Starszy Forge", {
                "🎮 Uruchom Klienta Forge (:forge:runClient)": ":forge:runClient",
                "🖥️ Uruchom Serwer Forge (:forge:runServer)": ":forge:runServer",
                "📦 Buduj moduł Forge (:forge:build)": ":forge:build"
            })

        ttk.Button(build_win, text="Zamknij", command=build_win.destroy).pack(pady=10)

if __name__ == "__main__":
    passed_file = sys.argv if len(sys.argv) > 1 else None
    root = tk.Tk()
    app = ModManagerApp(root, passed_file)
    root.mainloop()
