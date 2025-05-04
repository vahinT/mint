import subprocess
import sys

# Ensure dependencies are installed
required = ["requests", "tkinterdnd2"]
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import base64
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, END
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import threading

# ========== CONFIG ==========
# Corrected GitHub credentials (no typos)
GITHUB_USERNAME = "ncs-x1"  # Fixed from "ncs-xl"
GITHUB_REPO = "skybux"
BRANCH = "main"

# Decode GitHub token securely
encoded_token = "Z2l0aHViX3BhdF8xMUJSUVRCQkkwTUtHVmJQck10TlNPXzB5VGdtUTdqWFpTZEhVNmFMV3dycjZaOGxWYnlDZHZVa2pCQ1hxWldkajk3R0FWMjJIQUFWc0YyRndj"
GITHUB_TOKEN = base64.b64decode(encoded_token).decode("ascii")

API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ========== APP CLASS ==========
class SkyBoxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SkyBox (GitHub Cloud)")
        self.root.geometry("600x480")

        # GUI Elements
        self.drop_area = tk.Label(root, text="📂 Drag & Drop Files Here", bg="#eee", height=4)
        self.drop_area.pack(fill=tk.X, padx=10, pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        self.browse_btn = tk.Button(root, text="📁 Browse File", command=self.browse_file)
        self.browse_btn.pack(pady=5)

        self.file_list = Listbox(root)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_btn = tk.Button(root, text="🔄 Refresh File List", command=self.load_files)
        self.refresh_btn.pack(pady=5)

        self.download_btn = tk.Button(root, text="⬇️ Download Selected File", command=self.download_selected)
        self.download_btn.pack(pady=5)

        self.status = tk.Label(root, text="", fg="green")
        self.status.pack()

        self.files = []
        self.load_files()

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for file in files:
            self.upload_file(file)

    def browse_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.upload_file(file)

    def upload_file(self, path):
        threading.Thread(target=self._upload_file, args=(path,)).start()

    def _upload_file(self, path):
        self.status.config(text="Uploading...")
        try:
            filename = os.path.basename(path)
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf-8")

            response = requests.put(
                f"{API_URL}/{filename}",
                headers=HEADERS,
                json={
                    "message": f"Upload {filename}",
                    "content": content,
                    "branch": BRANCH
                }
            )

            if response.status_code in [200, 201]:
                self.status.config(text=f"{filename} uploaded.")
                self.load_files()
            else:
                raise Exception(f"GitHub Error: {response.json().get('message', 'Unknown error')}")

        except Exception as e:
            messagebox.showerror("Upload Error", str(e))
            self.status.config(text="Upload failed.")

    def load_files(self):
        threading.Thread(target=self._load_files).start()

    def _load_files(self):
        self.status.config(text="Loading file list...")
        try:
            response = requests.get(API_URL, headers=HEADERS)
            
            # Handle empty repository
            if response.status_code == 404:
                self.file_list.delete(0, END)
                self.file_list.insert(END, "Repository is empty")
                self.status.config(text="No files found")
                return

            data = response.json()
            
            # Handle API errors
            if isinstance(data, dict) and "message" in data:
                raise Exception(f"GitHub API Error: {data['message']}")

            # Update file list
            self.files = [item for item in data if isinstance(item, dict)]
            self.file_list.delete(0, END)
            for f in self.files:
                self.file_list.insert(END, f["name"])
            self.status.config(text="File list loaded")

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Failed",
                "Could not connect to GitHub. Check your internet connection."
            )
            self.status.config(text="Connection failed")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            self.status.config(text="Load failed")

    def download_selected(self):
        if not (sel := self.file_list.curselection()):
            messagebox.showwarning("Select File", "Please select a file to download.")
            return

        file_info = self.files[sel[0]]
        threading.Thread(target=self._download_file, args=(file_info,)).start()

    def _download_file(self, file_info):
        self.status.config(text="Downloading...")
        try:
            response = requests.get(file_info["download_url"])
            with open(file_info["name"], "wb") as f:
                f.write(response.content)  # Direct write without Base64 decoding
            self.status.config(text=f"Downloaded {file_info['name']}")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
            self.status.config(text="Download failed")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    SkyBoxApp(root)
    root.mainloop()