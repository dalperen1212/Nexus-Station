import customtkinter as ctk
import os
import threading
import subprocess
from tkinter import filedialog, messagebox, StringVar
from nexus_core import SystemCore, GitManager, GITHUB_USERNAME

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
WORK_DIR = os.path.expanduser("~/Masaüstü") 

class NexusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEXUS STATION v6.0 - Creator Edition")
        self.geometry("1200x800")
        
        self.current_repo_path = None
        self.current_repo_name = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.show_dashboard()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="NEXUS\nSTATION", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=30)
        self.create_nav_btn(" Sistem Paneli", self.show_dashboard)
        self.create_nav_btn(" GitHub Stüdyo", self.show_git_studio)
        self.create_nav_btn(" Hızlı Araçlar", self.show_tools)
        ctk.CTkLabel(self.sidebar, text=f"Dev: {GITHUB_USERNAME}", text_color="gray").pack(side="bottom", pady=20)

    def create_nav_btn(self, text, cmd):
        ctk.CTkButton(self.sidebar, text=text, command=cmd, height=45, fg_color="transparent", border_width=1, anchor="w").pack(fill="x", padx=15, pady=5)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()


    def show_dashboard(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="sistem durumu", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 20))
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(fill="x")
        self.cpu_ui = self.create_stat_card(stats_frame, "CPU", 0)
        self.ram_ui = self.create_stat_card(stats_frame, "RAM", 1)
        self.disk_ui = self.create_stat_card(stats_frame, "DISK", 2)
        self.update_stats_loop()
        
        ctk.CTkLabel(self.main_frame, text="bakım zamanı", font=ctk.CTkFont(size=20)).pack(anchor="w", pady=(40, 10))
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(fill="x", ipady=10)
        self.create_maint_btn(btn_frame, " güncelle", "update", "#2CC985", 0)
        self.create_maint_btn(btn_frame, " onar", "fix", "#D4A017", 1)
        self.create_maint_btn(btn_frame, " temizle", "clean", "#3B8ED0", 2)

    def create_stat_card(self, parent, title, col):
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(card, text=title).pack(pady=5)
        bar = ctk.CTkProgressBar(card, progress_color="#b30000"); bar.pack(pady=5)
        lbl = ctk.CTkLabel(card, text="%0"); lbl.pack(pady=5)
        return {"bar": bar, "lbl": lbl}

    def create_maint_btn(self, parent, text, task, color, col):
        btn = ctk.CTkButton(parent, text=text, command=lambda: SystemCore.run_maintenance_task(task), fg_color=color, height=60, text_color="black")
        btn.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)

    def update_stats_loop(self):
        if not self.main_frame.winfo_exists(): return
        stats = SystemCore.get_system_stats()
        try:
            self.cpu_ui["bar"].set(stats["cpu"]/100); self.cpu_ui["lbl"].configure(text=f"%{stats['cpu']}")
            self.ram_ui["bar"].set(stats["ram"]/100); self.ram_ui["lbl"].configure(text=f"%{stats['ram']}")
            self.disk_ui["bar"].set(stats["disk"]/100); self.disk_ui["lbl"].configure(text=f"%{stats['disk']}")
        except: pass
        self.after(2000, self.update_stats_loop)


    def show_git_studio(self):
        self.clear_frame()
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True)

        left = ctk.CTkFrame(content, width=300)
        left.pack(side="left", fill="y", padx=(0, 20))
        

        ctk.CTkButton(left, text=" yeni repo yap", command=self.open_create_repo_window, fg_color="#2CC985", text_color="black", height=40).pack(fill="x", pady=10)
        
        ctk.CTkLabel(left, text="repo listesi", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkButton(left, text="🔄 yenile", command=self.fetch_repos_thread).pack(pady=5)
        self.repo_scroll = ctk.CTkScrollableFrame(left)
        self.repo_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        right = ctk.CTkFrame(content)
        right.pack(side="right", fill="both", expand=True)
        self.project_label = ctk.CTkLabel(right, text="proje seçmedin", font=ctk.CTkFont(size=22, weight="bold"))
        self.project_label.pack(pady=20)
        self.git_status_label = ctk.CTkLabel(right, text="")
        self.git_status_label.pack(pady=5)
        self.action_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=20)
        
        self.fetch_repos_thread()

    def open_create_repo_window(self):

        if not GitManager.get_saved_token():
            dialog = ctk.CTkInputDialog(text="github personal access token girmen lazım:\n(bi kere girsen yeter)", title="github girişi")
            token = dialog.get_input()
            if token: GitManager.save_token(token)
            else: return


        self.win_create = ctk.CTkToplevel(self)
        self.win_create.title("yeni github projesi")
        self.win_create.geometry("500x400")
        
        ctk.CTkLabel(self.win_create, text="proje sihirbazı", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        self.entry_new_repo_name = ctk.CTkEntry(self.win_create, placeholder_text="repo adı (mesela: my-app)")
        self.entry_new_repo_name.pack(fill="x", padx=20, pady=10)
        
        self.selected_folder_var = StringVar(value="klasör seçmedin")
        ctk.CTkLabel(self.win_create, textvariable=self.selected_folder_var, text_color="gray").pack(pady=5)
        
        ctk.CTkButton(self.win_create, text=" proje klasörünü seç", command=self.select_folder_for_new).pack(pady=5)
        
        self.chk_private = ctk.CTkCheckBox(self.win_create, text="gizli olsun (private)")
        self.chk_private.pack(pady=15)
        
        ctk.CTkButton(self.win_create, text=" oluştur yükle", command=self.run_create_repo_process, fg_color="#b30000", height=50).pack(fill="x", padx=20, pady=20)

    def select_folder_for_new(self):
        path = filedialog.askdirectory()
        if path: self.selected_folder_var.set(path)

    def run_create_repo_process(self):
        name = self.entry_new_repo_name.get()
        path = self.selected_folder_var.get()
        token = GitManager.get_saved_token()
        is_private = self.chk_private.get() == 1
        
        if not name or path == "klasör seçmedin":
            messagebox.showwarning("eksik", "isim yazıp klasör seçmelisin")
            return

        self.win_create.destroy()
        messagebox.showinfo("başlıyoruz", "github ile konuşuyorum bekle biraz")
        
        threading.Thread(target=lambda: self._create_thread(path, name, token, is_private)).start()

    def _create_thread(self, path, name, token, is_private):
        success, msg = GitManager.create_and_push_repo(path, name, token, is_private)
        if success:
            self.after(0, lambda: messagebox.showinfo("harika", msg))
            self.fetch_repos_thread()
        else:
            self.after(0, lambda: messagebox.showerror("hata", msg))


    def fetch_repos_thread(self): threading.Thread(target=self._fetch_logic).start()
    def _fetch_logic(self):
        success, data = GitManager.fetch_github_repos()
        self.after(0, lambda: self._update_repo_ui(success, data))
    
    def _update_repo_ui(self, success, data):
        for w in self.repo_scroll.winfo_children(): w.destroy()
        if not success: return
        for repo in data:
            name = repo['name']
            ctk.CTkButton(self.repo_scroll, text=name, command=lambda n=name: self.select_repo(n), fg_color="transparent", border_width=1, anchor="w").pack(fill="x", pady=2)

    def select_repo(self, name):
        self.current_repo_name = name
        self.current_repo_path = os.path.join(WORK_DIR, name)
        self.project_label.configure(text=name)
        for w in self.action_frame.winfo_children(): w.destroy()
        
        status = GitManager.check_git_status(self.current_repo_path)
        if status == "NO_GIT":
            self.git_status_label.configure(text=" bilgisayarda yok bu", text_color="red")
            ctk.CTkButton(self.action_frame, text=" indir (clone)", command=self.do_clone, fg_color="#D4A017", text_color="black").pack(fill="x")
        elif status == "HTTPS_WARNING":
            self.git_status_label.configure(text=" şifre sıkıntısı var", text_color="orange")
            ctk.CTkButton(self.action_frame, text=" ssh düzelt", command=self.do_convert_ssh).pack(fill="x")
            self.add_controls()
        elif status == "READY":
            self.git_status_label.configure(text=" her şey hazır", text_color="green")
            self.add_controls()

    def add_controls(self):
        ctk.CTkButton(self.action_frame, text="💻 VS Code", command=lambda: subprocess.Popen(['code', self.current_repo_path]), fg_color="#007ACC").pack(fill="x", pady=5)
        push_box = ctk.CTkFrame(self.action_frame, border_color="red", border_width=1)
        push_box.pack(fill="x", pady=10)
        self.entry_commit = ctk.CTkEntry(push_box, placeholder_text="kısaca ne yaptın..."); self.entry_commit.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(push_box, text=" yolla (push)", command=self.do_push, fg_color="#b30000").pack(fill="x", padx=5, pady=5)

    def do_clone(self):
        GitManager.clone_repo(self.current_repo_name, WORK_DIR)
        messagebox.showinfo("bilgi", "terminali açtım")
    def do_convert_ssh(self):
        GitManager.convert_to_ssh(self.current_repo_path, self.current_repo_name)
        self.select_repo(self.current_repo_name)
    def do_push(self):
        threading.Thread(target=lambda: self._push_thread(self.entry_commit.get())).start()
    def _push_thread(self, msg):
        s, m = GitManager.push_changes(self.current_repo_path, msg)
        self.after(0, lambda: messagebox.showinfo("sonuç", m) if s else messagebox.showerror("hata", m))


    def show_tools(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="araçlar", font=ctk.CTkFont(size=26)).pack(pady=20)
        tools = [("Terminal", "gnome-terminal"), ("Dosyalar", "nautilus"), ("Sistem", "gnome-system-monitor")]
        for n, c in tools: ctk.CTkButton(self.main_frame, text=n, command=lambda c=c: subprocess.Popen(c.split()), height=50, fg_color="#333").pack(fill="x", padx=100, pady=5)

if __name__ == "__main__":
    app = NexusApp()
    app.mainloop()
