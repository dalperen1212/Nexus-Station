import subprocess
import os
import psutil
import shutil
import requests
import json


GITHUB_USERNAME = "Github_Name" 
CONFIG_FILE = "nexus_config.json"

class SystemCore:
    @staticmethod
    def get_terminal_emulator():
        terminals = ['gnome-terminal', 'x-terminal-emulator', 'konsole', 'xfce4-terminal']
        for term in terminals:
            if shutil.which(term): return term
        return None

    @staticmethod
    def run_terminal_command(command_str):
        emulator = SystemCore.get_terminal_emulator()
        if not emulator: return False, "terminal bulamadım"
        try:
            final_cmd = f"{command_str}; echo; echo 'bitti işlem'; read"
            if emulator == 'gnome-terminal':
                subprocess.Popen([emulator, '--', 'bash', '-c', final_cmd])
            else:
                subprocess.Popen([emulator, '-e', f"bash -c '{final_cmd}'"])
            return True, "terminal açıldı"
        except Exception as e: return False, str(e)

    @staticmethod
    def get_system_stats():
        try:
            return {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent, "disk": psutil.disk_usage('/').percent}
        except: return {"cpu": 0, "ram": 0, "disk": 0}

    @staticmethod
    def run_maintenance_task(task_type):
        commands = {
            "update": "sudo apt update && sudo apt full-upgrade -y",
            "fix": "sudo apt --fix-broken install -y && sudo dpkg --configure -a && sudo apt autoremove -y",
            "clean": "sudo apt autoclean && sudo apt clean && rm -rf ~/.cache/thumbnails/*"
        }
        return SystemCore.run_terminal_command(commands.get(task_type, "echo Hata"))

class GitManager:
    @staticmethod
    def get_saved_token():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("github_token")
            except: pass
        return None

    @staticmethod
    def save_token(token):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"github_token": token}, f)

    @staticmethod
    def fetch_github_repos():
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"

        token = GitManager.get_saved_token()
        headers = {'User-Agent': 'NexusStation'}
        if token: headers['Authorization'] = f'token {token}'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200: return True, response.json()
            return False, f"api hatası: {response.status_code}"
        except Exception as e: return False, str(e)

    @staticmethod
    def create_and_push_repo(local_path, repo_name, token, is_private):

        

        create_url = "https://api.github.com/user/repos"
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        payload = {"name": repo_name, "private": is_private, "auto_init": False}
        
        try:
            resp = requests.post(create_url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 422: return False, "bu isimde repo var zaten"
            if resp.status_code != 201: return False, f"oluşturamadım hata şu: {resp.text}"
            
            repo_data = resp.json()
            ssh_url = repo_data['ssh_url']
        except Exception as e: return False, f"bağlanamadım hata: {str(e)}"


        try:

            if not os.path.exists(os.path.join(local_path, ".git")):
                subprocess.run(["git", "init"], cwd=local_path, check=True)


            subprocess.run(["git", "add", "."], cwd=local_path, check=True)
            

            subprocess.run(["git", "commit", "-m", "Nexus Station Initial Commit"], cwd=local_path, capture_output=True)
            

            subprocess.run(["git", "branch", "-M", "main"], cwd=local_path, check=True)
            

            subprocess.run(["git", "remote", "remove", "origin"], cwd=local_path, capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", ssh_url], cwd=local_path, check=True)
            

            push_res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_path, capture_output=True, text=True)
            
            if push_res.returncode == 0:
                return True, f"tamamdır \nproje: {repo_name}\ngithub'da artık"
            else:
                return False, f"repo tamam ama push olmadı bak:\n{push_res.stderr}"

        except Exception as e:
            return False, f"git komutunda hata çıktı: {str(e)}"


    @staticmethod
    def check_git_status(path):
        if not os.path.exists(os.path.join(path, ".git")): return "NO_GIT"
        try:
            res = subprocess.run(["git", "-C", path, "remote", "get-url", "origin"], capture_output=True, text=True)
            if "https://" in res.stdout: return "HTTPS_WARNING"
            return "READY"
        except: return "ERROR"

    @staticmethod
    def clone_repo(repo_name, target_base):
        ssh_url = f"git@github.com:{GITHUB_USERNAME}/{repo_name}.git"
        cmd = f"git clone {ssh_url} {os.path.join(target_base, repo_name)}"
        return SystemCore.run_terminal_command(cmd)

    @staticmethod
    def push_changes(path, message):
        try:
            subprocess.run(["git", "-C", path, "add", "."], check=True)
            subprocess.run(["git", "-C", path, "commit", "-m", message], capture_output=True)
            res = subprocess.run(["git", "-C", path, "push"], capture_output=True, text=True)
            if res.returncode == 0: return True, "başardık"
            return False, res.stderr
        except Exception as e: return False, str(e)
        
    @staticmethod
    def convert_to_ssh(path, repo_name):
        new_url = f"git@github.com:{GITHUB_USERNAME}/{repo_name}.git"
        try:
            subprocess.run(["git", "-C", path, "remote", "set-url", "origin", new_url], check=True)
            return True, "düzelttim"
        except Exception as e: return False, str(e)
