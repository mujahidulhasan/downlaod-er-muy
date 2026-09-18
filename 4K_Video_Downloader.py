import sys
import os
import re
import json
import shutil
import base64
import subprocess
import threading
import ctypes
import io
import struct
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Persistent App Configuration Directory
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "4KVideoDownloader")
os.makedirs(APP_DATA_DIR, exist_ok=True)

STATE_FILE = os.path.join(APP_DATA_DIR, "downloads_state.json")
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "app_settings.json")
DEFAULT_OUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Embedded High-Quality 32x32 Application Icon (Base64)
ICON_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwY
AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJwSURBVHgB7VdLauNAEN1qS35sPAhh
wGQhS0ECJwsdQnYZshByGHIYQhLInhkgCxl8yEEGAgOBEEJYyEJIIEvhT+Wp2jJt65FGspM8
8GB6qqvf6/eq1V3TLFasWBnLsmzbNu3b/c98Ph/Ecdz3fX9jmqZlWRw0TVNkGAZ/JgghQ56r
qup5ns+yv5xMJv1arTYuFospG+50OpHjOKyYsm17wN8w0zQ913Vd/kYwxmB3v9+PlsvltNPp
TBi7wZ988gZ13dhsNpPtdssyqCqE2n1vNBov5/N52Ol0JoxhWdbIdd1tURQd27YrQggkYhCG
YRhFUcifcK7rusxV+wPjOGYYhnAcpx/Hca/X62G4VSoVyPM8gBACEgS/3++Nvu/veT6V04/C
MAxD/jJFUQxEUXTeeF0h4P/rA8qyvIfBsqyrX7c8z+P51G00Go08z2shgV/LwDAMtG63G4nZ
fD6HQkqlEsTjccjlcme/lUqlP0mSAD41dDqdSNNmsxnhg/F4DEQ0GvXz+fw79w/gD7VarZ2B
LgzD/a+71Wo1xIetVsufTqf+cDi8jEajq9/5Bfy922w2x7gSjK/FGGutXw7kC133+x/P8xye
f6/X69/g+aVyuXyBgwC/p6rVPwM4jsN/eFmWdfE8/6Fp2s3zPF/lcvmL53l8rB/5vv/xewdM
0/S4eT+Tydzl/hO/u6Gz2wGj2+1+4XN1OBx+qdVqFxiu7/f7j8Vigfdlfn9bLBZveIeK/c/v
v1Kp9It2c2EY0g7sB/E7l2EYL8z7y8Fg8ML4B+m93K1YsWI1/AMsD1nryF+vPgAAAABJRU5Er
kJggg==
"""

if os.name == 'nt':
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Apple.4KVideoDownloader.1.0")
    except Exception:
        pass

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

def get_ytdlp_exe():
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, "yt-dlp.exe")
        if os.path.exists(p): return p
    p = os.path.join(BASE_DIR, "yt-dlp.exe")
    if os.path.exists(p): return p
    p_dev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt-dlp.exe")
    if os.path.exists(p_dev): return p_dev
    w = shutil.which("yt-dlp")
    return w if w else "yt-dlp.exe"

def get_ffmpeg_dir():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS

    for folder in ["ffmpeg-9.0.1-essentials_build", "ffmpeg"]:
        p = os.path.join(BASE_DIR, folder, "bin")
        if os.path.exists(os.path.join(p, "ffmpeg.exe")):
            try:
                src_p = os.path.join(p, "ffprobe.exe")
                dst_p = os.path.join(BASE_DIR, "ffprobe.exe")
                if os.path.exists(src_p) and not os.path.exists(dst_p):
                    shutil.copy2(src_p, dst_p)
            except Exception: pass
            return p

    if os.path.exists(os.path.join(BASE_DIR, "ffmpeg.exe")):
        return BASE_DIR

    if os.path.exists(BASE_DIR):
        for root_dir, dirs, files in os.walk(BASE_DIR):
            if "ffmpeg.exe" in files:
                return root_dir

    w = shutil.which("ffmpeg")
    if w:
        return os.path.dirname(w)
    return BASE_DIR

def get_ffmpeg_exe():
    d = get_ffmpeg_dir()
    p = os.path.join(d, "ffmpeg.exe")
    if os.path.exists(p): return p
    w = shutil.which("ffmpeg")
    return w if w else "ffmpeg.exe"

def get_ffprobe_exe():
    d = get_ffmpeg_dir()
    p = os.path.join(d, "ffprobe.exe")
    if os.path.exists(p): return p
    w = shutil.which("ffprobe")
    return w if w else "ffprobe.exe"

def verify_downloaded_file(file_path, is_audio_only=False):
    """
    Verifies that the target file exists, is non-empty, has no leftover .part/stream files,
    and contains valid readable video/audio streams via ffprobe.
    Returns (is_valid: bool, reason: str)
    """
    if not file_path or not os.path.exists(file_path):
        return False, "File missing on disk"

    if os.path.getsize(file_path) == 0:
        return False, "0-byte file"

    # Check for leftover .part or .ytdl files
    part1 = file_path + ".part"
    part2 = file_path + ".ytdl"
    if os.path.exists(part1) or os.path.exists(part2):
        return False, "Incomplete (.part file remaining)"

    # Check for temporary stream files in directory matching base name
    folder = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.startswith(base_name) and f != os.path.basename(file_path):
                if f.endswith(".part") or f.endswith(".ytdl") or ".f" in f:
                    return False, "Incomplete (download stream file remaining)"

    # FFprobe stream verification
    ffprobe_bin = get_ffprobe_exe()
    if not ffprobe_bin or not os.path.exists(ffprobe_bin):
        return True, "Valid (ffprobe check skipped)"

    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_entries", "stream=codec_type:format=duration",
        "-of", "json",
        file_path
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
        if proc.returncode != 0:
            return False, "Corrupt or unreadable media stream"
        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        if not streams:
            return False, "No audio/video streams found"

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        if is_audio_only:
            if not has_audio:
                return False, "Missing audio stream"
        else:
            if not has_video:
                return False, "Missing video stream"
            if not has_audio:
                return False, "Missing audio stream (video has no sound)"

        return True, "Valid"
    except Exception as e:
        return False, f"Verification failed: {str(e)[:30]}"


def ensure_ico_file():
    ico_path = os.path.join(APP_DATA_DIR, "app_icon.ico")
    if not os.path.exists(ico_path):
        try:
            ic_bytes = base64.b64decode(ICON_BASE64.strip())
            header = struct.pack('<HHH', 0, 1, 1)
            entry = struct.pack('<BBBBHHII', 32, 32, 0, 0, 1, 32, len(ic_bytes), 6 + 16)
            with open(ico_path, 'wb') as f:
                f.write(header + entry + ic_bytes)
        except Exception:
            pass
    return ico_path if os.path.exists(ico_path) else None

def cleanup_pyinstaller_temp():
    try:
        current_mei = getattr(sys, '_MEIPASS', None)
        user_temp = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
        if os.path.exists(user_temp):
            for item in os.listdir(user_temp):
                if item.startswith("_MEI") and (not current_mei or item not in current_mei):
                    path = os.path.join(user_temp, item)
                    try: shutil.rmtree(path, ignore_errors=True)
                    except Exception: pass
    except Exception: pass

cleanup_pyinstaller_temp()

class AppleVideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4K Video Downloader Pro")
        self.root.geometry("420x720")
        self.root.minsize(360, 200)

        self.is_mini_mode = False

        ico_file = ensure_ico_file()
        if ico_file:
            try: self.root.iconbitmap(ico_file)
            except Exception: pass

        try:
            ic_data = base64.b64decode(ICON_BASE64.strip())
            self.icon_img = tk.PhotoImage(data=ic_data)
            self.root.iconphoto(True, self.icon_img)
        except Exception: pass

        self.download_queue = []
        self.active_process = None
        self.is_downloading = False
        self.is_paused = False
        self.worker_lock = threading.Lock()

        # Download Stats Tracking
        self.current_speed = ""
        self.current_eta = ""
        self.current_task_index = 0
        self.completed_durations = [] # Track average completion time per task

        # Apple Human Interface System Dark Palette
        self.c_bg = "#1C1C1E"          # Apple System Dark Background
        self.c_card = "#2C2C2E"        # Apple Elevated Grouped Card
        self.c_card_border = "#38383A" # Subtle Divider / Border
        self.c_input = "#3A3A3C"       # Apple Tertiary Fill / Inputs
        self.c_text = "#FFFFFF"        # Primary Text
        self.c_muted = "#8E8E93"       # Secondary System Gray Text
        self.c_blue = "#0A84FF"        # Apple System Blue Accent
        self.c_blue_hover = "#0071E3"
        self.c_red = "#FF453A"         # Apple System Red
        self.c_green = "#30D158"       # Apple System Green
        self.c_yellow = "#FFD60A"      # Apple System Yellow

        self.load_settings()

        self.root.configure(bg=self.c_bg)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.setup_ui()
        self.load_persisted_state()
        self.run_engine_self_test()

    def run_engine_self_test(self):
        ytdlp = os.path.exists(get_ytdlp_exe())
        ffmpeg = os.path.exists(get_ffmpeg_exe())
        ffprobe = os.path.exists(get_ffprobe_exe())

        if not ytdlp or not ffmpeg:
            self.lbl_progress_detail.config(text="⚠ Downloader engine incomplete (missing binaries)")
        else:
            self.lbl_progress_detail.config(text=f"Engine Ready (yt-dlp ✓, ffmpeg ✓, ffprobe {'✓' if ffprobe else '✕'})")

    def load_settings(self):
        self.default_save_folder = DEFAULT_OUT_DIR
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved = data.get("default_save_folder", "").strip()
                    if saved and os.path.exists(saved):
                        self.default_save_folder = saved
            except Exception: pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"default_save_folder": self.default_save_folder}, f, indent=2)
        except Exception: pass

    def configure_styles(self):
        font_main = ("Segoe UI", 9)
        font_bold = ("Segoe UI", 9, "bold")

        self.style.configure(".", background=self.c_bg, foreground=self.c_text, font=font_main)
        
        # Apple Segmented Tabs
        self.style.configure("TNotebook", background=self.c_bg, borderwidth=0, tabmargins=[0, 0, 0, 0])
        self.style.configure("TNotebook.Tab", 
            background=self.c_card, 
            foreground=self.c_muted, 
            padding=[18, 6], 
            font=font_bold, 
            borderwidth=0
        )
        self.style.map("TNotebook.Tab", 
            background=[('selected', self.c_blue)], 
            foreground=[('selected', '#FFFFFF')]
        )

        # Apple Progress Bar
        self.style.configure("Apple.Horizontal.TProgressbar", 
            background=self.c_blue, 
            troughcolor=self.c_input, 
            borderwidth=0, 
            thickness=6
        )

        # Apple Combobox
        self.style.configure("TCombobox", 
            fieldbackground=self.c_input, 
            background=self.c_card_border, 
            foreground=self.c_text, 
            arrowcolor=self.c_text, 
            borderwidth=0,
            padding=5
        )
        self.style.map("TCombobox", 
            fieldbackground=[('readonly', self.c_input)], 
            selectbackground=[('readonly', self.c_blue)],
            selectforeground=[('readonly', '#FFFFFF')]
        )

        self.style.configure("Vertical.TScrollbar",
            background=self.c_card_border,
            troughcolor=self.c_card,
            borderwidth=0,
            arrowsize=10
        )

    def setup_ui(self):
        # 1. Clean Apple Navigation Bar
        self.header_frame = tk.Frame(self.root, bg=self.c_bg, padx=16, pady=12)
        self.header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(self.header_frame, text="4K Video Downloader", font=("Segoe UI", 12, "bold"), bg=self.c_bg, fg=self.c_text)
        title_lbl.pack(side=tk.LEFT)

        header_btns = tk.Frame(self.header_frame, bg=self.c_bg)
        header_btns.pack(side=tk.RIGHT)

        btn_mini = tk.Button(header_btns, text="🗗 Mini Mode", font=("Segoe UI", 8), bg=self.c_card, fg=self.c_text, activebackground=self.c_input, activeforeground="#FFFFFF", relief="flat", bd=0, padx=10, pady=4, cursor="hand2", command=self.toggle_mini_mode)
        btn_mini.pack(side=tk.RIGHT)

        # Mini Mode Header Bar (Hidden by default)
        self.mini_bar = tk.Frame(self.root, bg=self.c_bg, padx=14, pady=6)
        
        lbl_mini_title = tk.Label(self.mini_bar, text="4K Downloader (Mini)", font=("Segoe UI", 9, "bold"), bg=self.c_bg, fg=self.c_text)
        lbl_mini_title.pack(side=tk.LEFT)

        btn_expand = tk.Button(self.mini_bar, text="🗖 Expand", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_text, relief="flat", bd=0, padx=8, pady=3, cursor="hand2", command=self.toggle_mini_mode)
        btn_expand.pack(side=tk.RIGHT)

        self.mini_stats_lbl = tk.Label(self.mini_bar, text="✓ 0 | ↓ 0 | ⏳ 0 | ⏸ 0 | ✕ 0 | ⚠ 0", font=("Segoe UI", 8), bg=self.c_bg, fg=self.c_muted)
        self.mini_stats_lbl.pack(side=tk.LEFT, padx=8)

        # 2. Apple Live Counter Dashboard (7 Status Categories)
        self.dash_frame = tk.Frame(self.root, bg=self.c_card, bd=1, highlightbackground=self.c_card_border, highlightthickness=1, padx=12, pady=8)
        self.dash_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        counts_box = tk.Frame(self.dash_frame, bg=self.c_card)
        counts_box.pack(fill=tk.X)

        self.lbl_queue = tk.Label(counts_box, text="Total: 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_text)
        self.lbl_queue.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_done = tk.Label(counts_box, text="✓ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_green)
        self.lbl_done.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_active = tk.Label(counts_box, text="↓ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_blue)
        self.lbl_active.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_pending = tk.Label(counts_box, text="⏳ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_yellow)
        self.lbl_pending.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_paused = tk.Label(counts_box, text="⏸ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_muted)
        self.lbl_paused.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_error = tk.Label(counts_box, text="✕ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_red)
        self.lbl_error.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_incomplete = tk.Label(counts_box, text="⚠ 0", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg="#FF9500")
        self.lbl_incomplete.pack(side=tk.LEFT)

        self.lbl_overall_eta = tk.Label(self.dash_frame, text="Overall Remaining: ~0m", font=("Segoe UI", 8), bg=self.c_card, fg=self.c_muted)
        self.lbl_overall_eta.pack(anchor=tk.W, pady=(4, 0))

        # 3. Apple Inset Tabs (Single Video & Playlist)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        self.tab_single = tk.Frame(self.notebook, bg=self.c_bg, padx=2, pady=6)
        self.tab_multi = tk.Frame(self.notebook, bg=self.c_bg, padx=2, pady=6)
        self.tab_playlist = tk.Frame(self.notebook, bg=self.c_bg, padx=2, pady=6)

        self.notebook.add(self.tab_single, text="  Single Video  ")
        self.notebook.add(self.tab_multi, text="  Multiple Videos  ")
        self.notebook.add(self.tab_playlist, text="  Playlist  ")

        self.setup_single_tab()
        self.setup_multi_tab()
        self.setup_real_playlist_tab()

        # 4. Apple Bottom Control & Progress Card
        self.bottom_card = tk.Frame(self.root, bg=self.c_card, bd=1, highlightbackground=self.c_card_border, highlightthickness=1, padx=14, pady=10)
        self.bottom_card.pack(fill=tk.X, padx=16, pady=(0, 12))

        self.lbl_current_task = tk.Label(self.bottom_card, text="Status: Ready", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text, anchor="w")
        self.lbl_current_task.pack(fill=tk.X)

        self.lbl_progress_detail = tk.Label(self.bottom_card, text="Ready for downloads", font=("Segoe UI", 8), bg=self.c_card, fg=self.c_muted, anchor="w")
        self.lbl_progress_detail.pack(fill=tk.X, pady=(2, 6))

        self.progress_bar = ttk.Progressbar(self.bottom_card, style="Apple.Horizontal.TProgressbar", mode="determinate", value=0)
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Action Control Buttons
        self.controls_box = tk.Frame(self.bottom_card, bg=self.c_card)
        self.controls_box.pack(fill=tk.X)

        self.btn_pause = tk.Button(self.controls_box, text="⏸ Pause", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_text, activebackground=self.c_card_border, activeforeground="#FFFFFF", relief="flat", bd=0, padx=10, pady=4, cursor="hand2", command=self.pause_all)
        self.btn_pause.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_resume = tk.Button(self.controls_box, text="▶ Resume", font=("Segoe UI", 8, "bold"), bg=self.c_blue, fg="#FFFFFF", activebackground=self.c_blue_hover, activeforeground="#FFFFFF", relief="flat", bd=0, padx=10, pady=4, cursor="hand2", command=self.resume_all)
        self.btn_resume.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_reset = tk.Button(self.controls_box, text="🗑 Reset Queue", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_red, activebackground=self.c_card_border, activeforeground=self.c_red, relief="flat", bd=0, padx=10, pady=4, cursor="hand2", command=self.reset_progress_data)
        self.btn_reset.pack(side=tk.RIGHT)

    def toggle_mini_mode(self):
        self.is_mini_mode = not self.is_mini_mode
        if self.is_mini_mode:
            self.header_frame.pack_forget()
            self.dash_frame.pack_forget()
            self.notebook.pack_forget()
            self.bottom_card.pack_forget()
            
            self.mini_bar.pack(fill=tk.X, padx=12, pady=(6, 2))
            self.bottom_card.pack(fill=tk.X, padx=12, pady=(0, 10))
            
            self.root.geometry("360x180")
            self.root.attributes("-topmost", True)
        else:
            self.mini_bar.pack_forget()
            self.bottom_card.pack_forget()
            
            self.header_frame.pack(fill=tk.X)
            self.dash_frame.pack(fill=tk.X, padx=16, pady=(0, 10))
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))
            self.bottom_card.pack(fill=tk.X, padx=16, pady=(0, 12))
            
            self.root.geometry("420x720")
            self.root.attributes("-topmost", False)

    def update_window_title(self, percent=None):
        total = len(self.download_queue)
        completed = len([t for t in self.download_queue if t["status"] == "Completed"])
        
        if percent is not None:
            title_str = f"[{percent:.0f}%] ({completed+1}/{total}) - 4K Video Downloader"
        elif self.is_paused:
            title_str = f"[Paused] ({completed}/{total}) - 4K Video Downloader"
        elif total > 0 and completed == total:
            title_str = "All Completed ✓ - 4K Video Downloader"
        else:
            title_str = "4K Video Downloader"
        
        self.root.title(title_str)

    def choose_destination_folder(self):
        folder = filedialog.askdirectory(initialdir=self.default_save_folder, title="Select Download Folder")
        if folder:
            self.default_save_folder = folder
            self.save_settings()
            self.lbl_dest_path.config(text=self.get_short_path(folder))
            self.lbl_dest_path_pl.config(text=self.get_short_path(folder))

    def get_short_path(self, p):
        if len(p) > 28:
            return "..." + p[-25:]
        return p

    def setup_single_tab(self):
        card = tk.Frame(self.tab_single, bg=self.c_card, bd=1, highlightbackground=self.c_card_border, highlightthickness=1, padx=14, pady=12)
        card.pack(fill=tk.X)

        tk.Label(card, text="Video URL", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text).pack(anchor=tk.W, pady=(0, 4))
        
        self.single_url = tk.Entry(card, font=("Segoe UI", 9), bg=self.c_input, fg=self.c_text, insertbackground=self.c_blue, relief="flat", bd=0)
        self.single_url.pack(fill=tk.X, ipady=6, pady=(0, 10))

        # Persistent Destination Row
        dest_box = tk.Frame(card, bg=self.c_input, padx=8, pady=5)
        dest_box.pack(fill=tk.X, pady=(0, 10))

        tk.Label(dest_box, text="Save to:", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_muted).pack(side=tk.LEFT)
        self.lbl_dest_path = tk.Label(dest_box, text=self.get_short_path(self.default_save_folder), font=("Segoe UI", 8), bg=self.c_input, fg=self.c_text)
        self.lbl_dest_path.pack(side=tk.LEFT, padx=(4, 0))

        btn_chg = tk.Button(dest_box, text="Change", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_blue, activebackground=self.c_card_border, activeforeground=self.c_blue, relief="flat", bd=0, padx=6, pady=1, cursor="hand2", command=self.choose_destination_folder)
        btn_chg.pack(side=tk.RIGHT)

        tk.Label(card, text="Resolution & Format", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text).pack(anchor=tk.W, pady=(0, 4))
        
        self.single_quality = tk.StringVar(value="1080p Full HD (MP4)")
        combo_q = ttk.Combobox(
            card,
            textvariable=self.single_quality,
            state="readonly",
            values=[
                "1080p Full HD (MP4)",
                "720p HD (MP4)",
                "480p SD (MP4)",
                "360p SD (MP4)",
                "240p SD (MP4)",
                "2K Quad HD (1440p MP4)",
                "4K Ultra HD (2160p MP4)",
                "1080p Original (Raw VP9/AV1)",
                "MP3 Audio (320 kbps)",
                "MP3 Audio (128 kbps)"
            ]
        )
        combo_q.pack(fill=tk.X, pady=(0, 10))

        opts_frame = tk.Frame(card, bg=self.c_card)
        opts_frame.pack(fill=tk.X, pady=(0, 4))

        self.single_thumb = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Download Cover (.jpg)", variable=self.single_thumb, bg=self.c_card, fg=self.c_muted, selectcolor=self.c_input, activebackground=self.c_card, activeforeground=self.c_text, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 10))

        self.single_subs = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Subtitles (.srt)", variable=self.single_subs, bg=self.c_card, fg=self.c_muted, selectcolor=self.c_input, activebackground=self.c_card, activeforeground=self.c_text, font=("Segoe UI", 8)).pack(side=tk.LEFT)

        btn_dl = tk.Button(self.tab_single, text="⬇ Download Video", font=("Segoe UI", 10, "bold"), bg=self.c_blue, fg="#FFFFFF", activebackground=self.c_blue_hover, activeforeground="#FFFFFF", relief="flat", bd=0, cursor="hand2", command=self.add_single_download)
        btn_dl.pack(fill=tk.X, pady=10, ipady=8)

    def setup_multi_tab(self):
        card = tk.Frame(self.tab_multi, bg=self.c_card, bd=1, highlightbackground=self.c_card_border, highlightthickness=1, padx=12, pady=10)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Label(card, text="Multiple URLs (Raw Text):", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text).pack(anchor=tk.W, pady=(0, 4))
        
        self.multi_text = tk.Text(card, height=3, font=("Segoe UI", 8), bg=self.c_input, fg=self.c_text, insertbackground=self.c_blue, relief="flat", bd=0)
        self.multi_text.pack(fill=tk.X, pady=(0, 6))

        dest_box_multi = tk.Frame(card, bg=self.c_input, padx=8, pady=4)
        dest_box_multi.pack(fill=tk.X, pady=(0, 6))

        tk.Label(dest_box_multi, text="Save to:", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_muted).pack(side=tk.LEFT)
        self.lbl_dest_path_multi = tk.Label(dest_box_multi, text=self.get_short_path(self.default_save_folder), font=("Segoe UI", 8), bg=self.c_input, fg=self.c_text)
        self.lbl_dest_path_multi.pack(side=tk.LEFT, padx=(4, 0))

        btn_chg_multi = tk.Button(dest_box_multi, text="Change", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_blue, activebackground=self.c_card_border, activeforeground=self.c_blue, relief="flat", bd=0, padx=6, pady=1, cursor="hand2", command=self.choose_destination_folder_multi)
        btn_chg_multi.pack(side=tk.RIGHT)

        ctrl = tk.Frame(card, bg=self.c_card)
        ctrl.pack(fill=tk.X, pady=(0, 6))

        btn_fetch = tk.Button(ctrl, text="🔍 Extract URLs", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_text, relief="flat", bd=0, padx=8, pady=3, cursor="hand2", command=self.fetch_multi_urls)
        btn_fetch.pack(side=tk.LEFT)

        self.global_quality_multi = tk.StringVar(value="1080p Full HD (MP4)")
        combo_g = ttk.Combobox(ctrl, textvariable=self.global_quality_multi, state="readonly", values=["1080p Full HD (MP4)", "720p HD (MP4)", "480p SD (MP4)", "360p SD (MP4)", "240p SD (MP4)", "4K Ultra HD (2160p MP4)", "MP3 Audio (320 kbps)"], width=18)
        combo_g.pack(side=tk.RIGHT)
        combo_g.bind("<<ComboboxSelected>>", self.apply_global_quality_multi)

        self.multi_scroll_box = tk.Frame(card, bg=self.c_input, bd=1, highlightbackground=self.c_card_border, highlightthickness=1)
        self.multi_scroll_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.multi_canvas = tk.Canvas(self.multi_scroll_box, bg=self.c_input, highlightthickness=0)
        self.multi_scrollbar = ttk.Scrollbar(self.multi_scroll_box, orient="vertical", command=self.multi_canvas.yview)
        self.multi_inner = tk.Frame(self.multi_canvas, bg=self.c_input)

        self.multi_inner.bind("<Configure>", lambda e: self.multi_canvas.configure(scrollregion=self.multi_canvas.bbox("all")))
        self.multi_canvas.create_window((0, 0), window=self.multi_inner, anchor="nw")
        self.multi_canvas.configure(yscrollcommand=self.multi_scrollbar.set)

        self.multi_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.multi_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.fetched_multi_data = []

        btn_dl_multi = tk.Button(self.tab_multi, text="⬇ Download Multiple Videos", font=("Segoe UI", 9, "bold"), bg=self.c_blue, fg="#FFFFFF", activebackground=self.c_blue_hover, activeforeground="#FFFFFF", relief="flat", bd=0, cursor="hand2", command=self.add_multi_download)
        btn_dl_multi.pack(fill=tk.X, pady=6, ipady=6)

    def choose_destination_folder_multi(self):
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.default_save_folder = folder
            self.lbl_dest_path_multi.config(text=self.get_short_path(folder))
            self.save_persisted_state()

    def apply_global_quality_multi(self, event=None):
        g = self.global_quality_multi.get()
        for item in self.fetched_multi_data:
            item["var_qual"].set(g)

    def fetch_multi_urls(self):
        text = self.multi_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input Required", "Please paste text containing video URLs.")
            return

        import re
        pattern = r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
        matches = re.findall(pattern, text)
        
        seen = set()
        entries = []
        idx = 1
        for v_id in matches:
            if v_id not in seen:
                seen.add(v_id)
                entries.append({
                    "index": idx,
                    "title": f"Video {v_id}",
                    "url": f"https://www.youtube.com/watch?v={v_id}"
                })
                idx += 1
                
        if not entries:
            messagebox.showwarning("No Videos Found", "No valid YouTube video URLs were detected in the input.")
            return
            
        self.render_multi_items(entries)

    def render_multi_items(self, entries):
        for w in self.multi_inner.winfo_children():
            w.destroy()
        self.fetched_multi_data.clear()

        g = self.global_quality_multi.get()

        for item in entries:
            var_cb = tk.BooleanVar(value=True)
            var_q = tk.StringVar(value=g)

            row = tk.Frame(self.multi_inner, bg=self.c_input)
            row.pack(fill=tk.X, pady=2, padx=4)

            cb = tk.Checkbutton(row, text=f"#{item['index']} {item['title'][:22]}", variable=var_cb, bg=self.c_input, fg=self.c_text, selectcolor=self.c_bg, activebackground=self.c_input, activeforeground=self.c_text, font=("Segoe UI", 8))
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

            combo = ttk.Combobox(row, textvariable=var_q, state="readonly", values=["1080p Full HD (MP4)", "720p HD (MP4)", "480p SD (MP4)", "360p SD (MP4)", "240p SD (MP4)", "4K Ultra HD (2160p MP4)", "MP3 Audio (320 kbps)"], width=15, font=("Segoe UI", 8))
            combo.pack(side=tk.RIGHT)

            self.fetched_multi_data.append({"index": item["index"], "title": item["title"], "url": item["url"], "var_cb": var_cb, "var_qual": var_q})

        self.lbl_progress_detail.config(text=f"Loaded {len(entries)} URLs.")

    def add_single_download(self):
        url = self.single_url.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please paste a video URL.")
            return

        target_dir = self.default_save_folder if self.default_save_folder else DEFAULT_OUT_DIR

        task = {
            "id": f"task_{len(self.download_queue)+1}",
            "url": url,
            "title": "Single Video",
            "folder": target_dir,
            "quality": self.single_quality.get(),
            "thumb": self.single_thumb.get(),
            "subs": self.single_subs.get(),
            "is_playlist_item": False,
            "status": "Queued",
            "progress": 0.0,
            "speed": "",
            "eta": "",
            "detail": "Queued ⏳"
        }
        self.download_queue.append(task)
        self.save_persisted_state()
        self.update_dashboard_ui()

        self.lbl_progress_detail.config(text=f"Queued: {task['title']}")
        self.is_paused = False
        self.start_queue_worker()

    def add_multi_download(self):
        selected = [i for i in self.fetched_multi_data if i["var_cb"].get()]
        if not selected:
            messagebox.showwarning("Selection Required", "Please select at least one video.")
            return

        target_dir = self.default_save_folder if self.default_save_folder else DEFAULT_OUT_DIR

        for idx, item in enumerate(selected, start=1):
            task = {
                "id": f"task_{len(self.download_queue)+1}",
                "url": item["url"],
                "title": item["title"],
                "playlist_index": idx,
                "folder": target_dir,
                "quality": item["var_qual"].get(),
                "thumb": False,
                "subs": False,
                "is_playlist_item": True,
                "status": "Queued",
                "progress": 0.0,
                "speed": "",
                "eta": "",
                "detail": "Queued ⏳"
            }
            self.download_queue.append(task)

        self.save_persisted_state()
        self.update_dashboard_ui()
        self.lbl_progress_detail.config(text=f"Queued {len(selected)} URLs.")
        self.is_paused = False
        self.start_queue_worker()

    def setup_real_playlist_tab(self):
        card = tk.Frame(self.tab_playlist, bg=self.c_card, bd=1, highlightbackground=self.c_card_border, highlightthickness=1, padx=12, pady=10)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Label(card, text="YouTube Playlist URL:", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text).pack(anchor=tk.W, pady=(0, 4))
        
        self.real_pl_text = tk.Entry(card, font=("Segoe UI", 8), bg=self.c_input, fg=self.c_text, insertbackground=self.c_blue, relief="flat", bd=0)
        self.real_pl_text.pack(fill=tk.X, pady=(0, 6))

        dest_box_pl = tk.Frame(card, bg=self.c_input, padx=8, pady=4)
        dest_box_pl.pack(fill=tk.X, pady=(0, 6))

        tk.Label(dest_box_pl, text="Save to:", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_muted).pack(side=tk.LEFT)
        self.lbl_dest_path_real_pl = tk.Label(dest_box_pl, text=self.get_short_path(self.default_save_folder), font=("Segoe UI", 8), bg=self.c_input, fg=self.c_text)
        self.lbl_dest_path_real_pl.pack(side=tk.LEFT, padx=(4, 0))

        btn_chg_pl = tk.Button(dest_box_pl, text="Change", font=("Segoe UI", 8, "bold"), bg=self.c_card, fg=self.c_blue, activebackground=self.c_card_border, activeforeground=self.c_blue, relief="flat", bd=0, padx=6, pady=1, cursor="hand2", command=self.choose_destination_folder_real_pl)
        btn_chg_pl.pack(side=tk.RIGHT)

        ctrl = tk.Frame(card, bg=self.c_card)
        ctrl.pack(fill=tk.X, pady=(0, 6))

        btn_fetch = tk.Button(ctrl, text="🔍 Load Playlist", font=("Segoe UI", 8, "bold"), bg=self.c_input, fg=self.c_text, relief="flat", bd=0, padx=8, pady=3, cursor="hand2", command=self.load_real_playlist)
        btn_fetch.pack(side=tk.LEFT)

        self.global_quality_real_pl = tk.StringVar(value="1080p Full HD (MP4)")
        combo_g = ttk.Combobox(ctrl, textvariable=self.global_quality_real_pl, state="readonly", values=["1080p Full HD (MP4)", "720p HD (MP4)", "480p SD (MP4)", "360p SD (MP4)", "240p SD (MP4)", "4K Ultra HD (2160p MP4)", "MP3 Audio (320 kbps)"], width=18)
        combo_g.pack(side=tk.RIGHT)
        combo_g.bind("<<ComboboxSelected>>", self.apply_global_quality_real_pl)

        self.real_pl_scroll_box = tk.Frame(card, bg=self.c_input, bd=1, highlightbackground=self.c_card_border, highlightthickness=1)
        self.real_pl_scroll_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.real_pl_canvas = tk.Canvas(self.real_pl_scroll_box, bg=self.c_input, highlightthickness=0)
        self.real_pl_scrollbar = ttk.Scrollbar(self.real_pl_scroll_box, orient="vertical", command=self.real_pl_canvas.yview)
        self.real_pl_inner = tk.Frame(self.real_pl_canvas, bg=self.c_input)

        self.real_pl_inner.bind("<Configure>", lambda e: self.real_pl_canvas.configure(scrollregion=self.real_pl_canvas.bbox("all")))
        self.real_pl_canvas.create_window((0, 0), window=self.real_pl_inner, anchor="nw")
        self.real_pl_canvas.configure(yscrollcommand=self.real_pl_scrollbar.set)

        self.real_pl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.real_pl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.fetched_real_pl_data = []

        btn_dl_pl = tk.Button(self.tab_playlist, text="⬇ Download Playlist", font=("Segoe UI", 9, "bold"), bg=self.c_blue, fg="#FFFFFF", activebackground=self.c_blue_hover, activeforeground="#FFFFFF", relief="flat", bd=0, cursor="hand2", command=self.add_real_playlist_download)
        btn_dl_pl.pack(fill=tk.X, pady=6, ipady=6)

    def choose_destination_folder_real_pl(self):
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.default_save_folder = folder
            self.lbl_dest_path_real_pl.config(text=self.get_short_path(folder))
            self.save_persisted_state()

    def apply_global_quality_real_pl(self, event=None):
        g = self.global_quality_real_pl.get()
        for item in self.fetched_real_pl_data:
            item["var_qual"].set(g)

    def load_real_playlist(self):
        url = self.real_pl_text.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please paste a playlist URL.")
            return

        self.lbl_progress_detail.config(text="Fetching playlist details...")
        threading.Thread(target=self.run_fetch_real_playlist, args=(url,), daemon=True).start()

    def run_fetch_real_playlist(self, url):
        entries = []
        cmd = [get_ytdlp_exe(), "--flat-playlist", "-j", "-i", url]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
            
            idx = 1
            for line in proc.stdout.splitlines():
                line = line.strip()
                if not line.startswith("{"): continue
                try:
                    e = json.loads(line)
                    v_id = e.get("id") or e.get("url")
                    
                    if not v_id:
                        # Fallback for completely inaccessible entries, though yt-dlp usually includes id
                        entries.append({
                            "index": idx,
                            "title": "[Unavailable Video]",
                            "url": "",
                            "valid": False
                        })
                        idx += 1
                        continue

                    if not v_id.startswith("http"):
                        web_url = f"https://www.youtube.com/watch?v={v_id}"
                    else:
                        web_url = e.get("url") or e.get("webpage_url") or url

                    # Check if it's explicitly marked private/deleted
                    title = e.get("title", f"Video {idx}")
                    valid = True
                    if title in ["[Private video]", "[Deleted video]", "[Unavailable video]"]:
                        valid = False

                    entries.append({
                        "index": e.get("playlist_index", idx),
                        "title": title,
                        "url": web_url,
                        "valid": valid
                    })
                    idx += 1
                except json.JSONDecodeError:
                    continue

        except Exception as ex:
            print("Playlist fetch exception:", ex)

        self.root.after(0, self.render_real_playlist_items, entries)

    def render_real_playlist_items(self, entries):
        for w in self.real_pl_inner.winfo_children():
            w.destroy()
        self.fetched_real_pl_data.clear()

        g = self.global_quality_real_pl.get()

        for item in entries:
            var_cb = tk.BooleanVar(value=item["valid"])
            var_q = tk.StringVar(value=g)

            row = tk.Frame(self.real_pl_inner, bg=self.c_input)
            row.pack(fill=tk.X, pady=2, padx=4)

            # If invalid, disable checkbox
            state = tk.NORMAL if item["valid"] else tk.DISABLED
            title_text = f"#{item['index']} {item['title'][:22]}"
            if not item["valid"]:
                title_text += " [Skipped]"

            cb = tk.Checkbutton(row, text=title_text, variable=var_cb, bg=self.c_input, fg=self.c_text if item["valid"] else self.c_muted, selectcolor=self.c_bg, activebackground=self.c_input, activeforeground=self.c_text, font=("Segoe UI", 8), state=state)
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

            combo = ttk.Combobox(row, textvariable=var_q, state="readonly", values=["1080p Full HD (MP4)", "720p HD (MP4)", "480p SD (MP4)", "360p SD (MP4)", "240p SD (MP4)", "4K Ultra HD (2160p MP4)", "MP3 Audio (320 kbps)"], width=15, font=("Segoe UI", 8))
            combo.pack(side=tk.RIGHT)
            if not item["valid"]:
                combo.configure(state=tk.DISABLED)

            if item["valid"]:
                self.fetched_real_pl_data.append({"index": item["index"], "title": item["title"], "url": item["url"], "var_cb": var_cb, "var_qual": var_q})

        self.lbl_progress_detail.config(text=f"Loaded {len(entries)} playlist items.")

    def add_real_playlist_download(self):
        selected = [i for i in self.fetched_real_pl_data if i["var_cb"].get()]
        if not selected:
            messagebox.showwarning("Selection Required", "Please select at least one valid video.")
            return

        target_dir = self.default_save_folder if self.default_save_folder else DEFAULT_OUT_DIR

        for idx, item in enumerate(selected, start=1):
            task = {
                "id": f"task_{len(self.download_queue)+1}",
                "url": item["url"],
                "title": item["title"],
                "playlist_index": item["index"],
                "folder": target_dir,
                "quality": item["var_qual"].get(),
                "thumb": False,
                "subs": False,
                "is_playlist_item": True,
                "status": "Queued",
                "progress": 0.0,
                "speed": "",
                "eta": "",
                "detail": "Queued ⏳"
            }
            self.download_queue.append(task)

        self.save_persisted_state()
        self.update_dashboard_ui()
        self.lbl_progress_detail.config(text=f"Queued {len(selected)} playlist items.")
        self.is_paused = False
        self.start_queue_worker()

    def pause_all(self):
        self.is_paused = True
        if self.active_process:
            try: self.active_process.kill()
            except Exception: pass

        for t in self.download_queue:
            if t["status"] in ["Downloading", "Merging", "Queued"]:
                t["status"] = "Paused"
                t["detail"] = "Paused ⏸"

        self.save_persisted_state()
        self.lbl_current_task.config(text="Status: Paused ⏸")
        self.lbl_progress_detail.config(text="Downloads paused.")
        self.update_window_title()
        self.update_dashboard_ui()

    def resume_all(self):
        self.is_paused = False
        for t in self.download_queue:
            if t["status"] in ["Paused", "Interrupted", "Error", "Incomplete"]:
                t["status"] = "Queued"
                t["detail"] = "Queued ⏳"

        self.save_persisted_state()
        self.update_window_title()
        self.update_dashboard_ui()
        self.start_queue_worker()

    def reset_progress_data(self):
        if messagebox.askyesno("Reset Queue", "Clear all download queue items and history?"):
            self.pause_all()
            self.download_queue.clear()
            if os.path.exists(STATE_FILE):
                try: os.remove(STATE_FILE)
                except Exception: pass

            self.lbl_current_task.config(text="Status: Ready")
            self.lbl_progress_detail.config(text="Queue cleared.")
            self.progress_bar.config(value=0)
            self.update_window_title()
            self.update_dashboard_ui()

    def start_queue_worker(self):
        if not self.is_downloading and not self.is_paused:
            threading.Thread(target=self.queue_loop, daemon=True).start()

    def queue_loop(self):
        with self.worker_lock:
            self.is_downloading = True

            while not self.is_paused:
                pending = [t for t in self.download_queue if t["status"] == "Queued"]
                if not pending: break

                task = pending[0]
                self.run_task(task)

            self.is_downloading = False
            self.root.after(0, self.update_window_title)
            self.root.after(0, self.update_dashboard_ui)

    def run_task(self, task):
        task["status"] = "Downloading"
        self.save_persisted_state()
        self.root.after(0, self.update_dashboard_ui)

        out_dir = task["folder"]
        if not os.path.exists(out_dir):
            try: os.makedirs(out_dir)
            except Exception: pass

        start_time = time.time()
        self.root.after(0, lambda: self.lbl_current_task.config(text=f"Downloading #{task.get('playlist_index', '')} {task['title'][:22]}"))

        quality = task["quality"]
        ffmpeg_bin = get_ffmpeg_exe()
        ffmpeg_dir = get_ffmpeg_dir()

        proc_env = os.environ.copy()
        if ffmpeg_dir:
            proc_env["PATH"] = ffmpeg_dir + os.pathsep + proc_env.get("PATH", "")

        cmd = [
            get_ytdlp_exe(),
            "--ffmpeg-location", ffmpeg_dir,
            "--newline",
            "--progress"
        ]

        if "MP3" in quality:
            bitrate = "320K" if "320" in quality else "128K"
            cmd.extend([
                "-f", "bestaudio/best",
                "-x", "--audio-format", "mp3",
                "--audio-quality", bitrate
            ])
        else:
            q_val = "1080"
            if "2160p" in quality or "4K" in quality: q_val = "2160"
            elif "1440p" in quality or "2K" in quality: q_val = "1440"
            elif "720p" in quality: q_val = "720"
            elif "480p" in quality: q_val = "480"
            elif "360p" in quality: q_val = "360"
            elif "240p" in quality: q_val = "240"

            if "Original" in quality:
                # Fast Direct Merge (Original Quality VP9/AV1/Opus - Fastest, no conversion)
                cmd.extend([
                    "-f", f"bv*[height<={q_val}]+ba/b[height<={q_val}]/bv*+ba/b",
                    "--merge-output-format", "mp4"
                ])
            else:
                # Compatible MP4 (Guaranteed H.264 Video + AAC Audio - Plays on all devices/players)
                cmd.extend([
                    "-f", f"bv*[height<={q_val}][vcodec^=avc1]+ba[acodec^=mp4a]/bv*[height<={q_val}][vcodec^=avc1]+ba[acodec^=m4a]/bv*[height<={q_val}][ext=mp4]+ba[ext=m4a]/bv*[height<={q_val}]+ba/b",
                    "--merge-output-format", "mp4",
                    "--recode-video", "mp4",
                    "--postprocessor-args", "FFmpegVideoConvertor:-c:v libx264 -c:a aac"
                ])

        # Formatting Output Template
        if task.get("is_playlist_item"):
            cmd.extend([
                "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
                "--no-write-thumbnail",
                "--no-write-subs",
                "--no-write-auto-subs",
                "--no-write-comments",
                "--no-write-description",
                "--no-write-info-json",
                "--no-write-playlist-metafiles",
                "--no-embed-thumbnail",
                "--no-embed-metadata",
                "--no-embed-info-json"
            ])
        else:
            if task.get("thumb"):
                cmd.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
            else:
                cmd.extend(["--no-write-thumbnail", "--no-embed-thumbnail"])

            if task.get("subs"):
                cmd.extend(["--write-subs", "--sub-langs", "en,bn"])
            else:
                cmd.extend(["--no-write-subs", "--no-write-auto-subs"])

            cmd.extend([
                "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
                "--no-write-comments",
                "--no-write-description",
                "--no-write-info-json"
            ])

        cmd.append(task["url"])

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        last_error_lines = []
        expected_output_file = None

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=proc_env,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            self.active_process = process

            for line in process.stdout:
                if self.is_paused: break
                line_str = line.strip()
                if line_str:
                    last_error_lines.append(line_str)
                    if len(last_error_lines) > 8:
                        last_error_lines.pop(0)

                # Capture output filename from yt-dlp logs
                if "[download] Destination:" in line_str:
                    expected_output_file = line_str.replace("[download] Destination:", "").strip()
                elif "[Merger] Merging formats into" in line_str:
                    expected_output_file = line_str.replace("[Merger] Merging formats into", "").replace('"', '').strip()

                if "%" in line_str:
                    match_p = re.search(r'(\d+(?:\.\d+)?)%', line_str)
                    match_speed = re.search(r'at\s+([\d\.]+\s*[kKMGT]?i?B/s)', line_str)
                    match_eta = re.search(r'ETA\s+(\d+:\d+(?::\d+)?)', line_str)

                    if match_p:
                        p_val = float(match_p.group(1))
                        task["progress"] = p_val
                        
                        speed_str = match_speed.group(1) if match_speed else ""
                        eta_str = match_eta.group(1) if match_eta else ""

                        task["speed"] = speed_str
                        task["eta"] = eta_str

                        detail_txt = f"{p_val:.1f}%"
                        if speed_str: detail_txt += f" • {speed_str}"
                        if eta_str: detail_txt += f" • ETA {eta_str}"

                        task["detail"] = detail_txt
                        self.root.after(0, lambda v=p_val, d=detail_txt: self.update_progress_ui(v, d))

                elif "[Merger]" in line_str or "[ffmpeg]" in line_str or "[ExtractAudio]" in line_str or "[Fixup" in line_str:
                    task["status"] = "Merging"
                    detail_txt = "Merging video & audio with FFmpeg..."
                    task["detail"] = detail_txt
                    self.root.after(0, lambda d=detail_txt: self.lbl_progress_detail.config(text=d))

            process.wait()

            # --- POST-DOWNLOAD INTEGRITY & OUTPUT VALIDATION ---
            if self.is_paused:
                task["status"] = "Paused"
                task["detail"] = "Paused ⏸"
            elif process.returncode == 0:
                # Find output file if not captured in stdout
                if not expected_output_file or not os.path.exists(expected_output_file):
                    ext = "mp3" if "MP3" in quality else "mp4"
                    for f in os.listdir(out_dir):
                        if f.endswith(f".{ext}") and not f.endswith(".part"):
                            expected_output_file = os.path.join(out_dir, f)
                            break

                is_audio_only = "MP3" in quality
                # Rigorous FFprobe Integrity Check
                is_valid, reason = verify_downloaded_file(expected_output_file, is_audio_only=is_audio_only)

                if is_valid:
                    task["status"] = "Completed"
                    task["progress"] = 100.0
                    task["detail"] = "Completed ✓"
                    elapsed = time.time() - start_time
                    self.completed_durations.append(elapsed)
                else:
                    # Remove bad output file (e.g. video without audio or half-merged mp4)
                    if expected_output_file and os.path.exists(expected_output_file) and not expected_output_file.endswith(".part"):
                        try: os.remove(expected_output_file)
                        except Exception: pass

                    task["status"] = "Incomplete"
                    task["detail"] = f"Validation Failed: {reason}"
            else:
                err_msg = "Download Failed"
                for el in reversed(last_error_lines):
                    if "ERROR" in el or "Error" in el:
                        err_msg = el[:60]
                        break
                task["status"] = "Error"
                task["detail"] = err_msg

            self.save_persisted_state()
            self.root.after(0, self.update_window_title)
            self.root.after(0, self.update_dashboard_ui)

        except Exception as e:
            task["status"] = "Error"
            task["detail"] = str(e)[:60]
            self.save_persisted_state()
            self.root.after(0, self.update_dashboard_ui)
        finally:
            self.active_process = None

    def update_progress_ui(self, value, detail):
        self.progress_bar.config(value=value)
        self.lbl_progress_detail.config(text=detail)
        self.update_window_title(value)
        self.update_dashboard_ui()

    def update_dashboard_ui(self):
        total = len(self.download_queue)
        completed = len([t for t in self.download_queue if t["status"] == "Completed"])
        active = len([t for t in self.download_queue if t["status"] in ["Downloading", "Merging"]])
        queued = len([t for t in self.download_queue if t["status"] == "Queued"])
        paused = len([t for t in self.download_queue if t["status"] == "Paused"])
        error = len([t for t in self.download_queue if t["status"] == "Error"])
        incomplete = len([t for t in self.download_queue if t["status"] in ["Incomplete", "Interrupted"]])

        self.lbl_queue.config(text=f"Total: {total}")
        self.lbl_done.config(text=f"✓ {completed}")
        self.lbl_active.config(text=f"↓ {active}")
        self.lbl_pending.config(text=f"⏳ {queued}")
        self.lbl_paused.config(text=f"⏸ {paused}")
        self.lbl_error.config(text=f"✕ {error}")
        self.lbl_incomplete.config(text=f"⚠ {incomplete}")

        # Update Mini Mode Compact Badges
        self.mini_stats_lbl.config(text=f"✓ {completed} | ↓ {active} | ⏳ {queued} | ⏸ {paused} | ✕ {error} | ⚠ {incomplete}")

        # Overall ETA Calculation
        remaining_count = queued + active
        if remaining_count > 0:
            avg_time = sum(self.completed_durations) / len(self.completed_durations) if self.completed_durations else 40.0
            total_est_sec = remaining_count * avg_time
            m = int(total_est_sec // 60)
            self.lbl_overall_eta.config(text=f"Overall Remaining: ~{m}m ({remaining_count} tasks left)")
        elif total > 0 and completed == total:
            self.lbl_overall_eta.config(text="All Queue Downloads Completed ✓")
            self.lbl_current_task.config(text="Status: All Downloads Completed ✓")
        else:
            self.lbl_overall_eta.config(text="Overall Remaining: 0m")

    def save_persisted_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.download_queue, f, indent=2)
        except Exception: pass

    def load_persisted_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.download_queue = json.load(f)
                    
                    # Crash Recovery: Reset active tasks on restart to Interrupted
                    for t in self.download_queue:
                        if t.get("status") in ["Downloading", "Merging"]:
                            t["status"] = "Interrupted"
                            t["detail"] = "Interrupted ⚠"

                    self.update_dashboard_ui()
                    self.update_window_title()
            except Exception:
                self.download_queue = []

if __name__ == "__main__":
    root = tk.Tk()
    app = AppleVideoDownloaderApp(root)
    root.mainloop()
