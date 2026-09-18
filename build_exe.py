import sys
import os
import subprocess
import shutil

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

print("===================================================")
print("  BUILDING 4K VIDEO DOWNLOADER (COMPACT MOBILE UI)")
print("===================================================")

base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Ensure PyInstaller is installed
try:
    import PyInstaller
    print("[OK] PyInstaller is ready.")
except ImportError:
    print("[*] Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

# 2. Ensure ffmpeg & ffprobe are ready in root
build_bin = os.path.join(base_dir, "ffmpeg-9.0.1-essentials_build", "bin")
if os.path.exists(build_bin):
    for f in ["ffmpeg.exe", "ffprobe.exe"]:
        src = os.path.join(build_bin, f)
        dst = os.path.join(base_dir, f)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
                print(f"[OK] Copied {f} to application directory.")
            except Exception: pass

# 3. Ensure app_icon.ico is generated before building
ico_path = os.path.join(base_dir, "app_icon.ico")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_module", os.path.join(base_dir, "4K_Video_Downloader.py"))
    if spec and spec.loader:
        app_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_mod)
        if hasattr(app_mod, "ensure_ico_file"):
            app_mod.ensure_ico_file()
except Exception as e:
    print(f"[*] Icon check notice: {e}")

# 4. Build Single Standalone Windowed Desktop EXE
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--windowed", # Stealth Native Window
    "--name", "4K_Video_Downloader",
]

if os.path.exists(ico_path):
    cmd.extend(["--icon", ico_path])
    print(f"[OK] Using application icon: {ico_path}")

cmd.append("--add-binary")
cmd.append(f"{os.path.join(base_dir, 'yt-dlp.exe')};.")

ffmpeg_src = os.path.join(base_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_src) and os.path.exists(os.path.join(build_bin, "ffmpeg.exe")):
    ffmpeg_src = os.path.join(build_bin, "ffmpeg.exe")
cmd.extend(["--add-binary", f"{ffmpeg_src};."])

ffprobe_src = os.path.join(base_dir, "ffprobe.exe")
if not os.path.exists(ffprobe_src) and os.path.exists(os.path.join(build_bin, "ffprobe.exe")):
    ffprobe_src = os.path.join(build_bin, "ffprobe.exe")
if os.path.exists(ffprobe_src):
    cmd.extend(["--add-binary", f"{ffprobe_src};."])

cmd.append(os.path.join(base_dir, "4K_Video_Downloader.py"))

print("\n[*] Packing into single 4K_Video_Downloader.exe file (Please wait ~30s)...")
res = subprocess.run(cmd, cwd=base_dir)

if res.returncode == 0:
    dist_exe = os.path.join(base_dir, "dist", "4K_Video_Downloader.exe")
    target_exe = os.path.join(base_dir, "4K_Video_Downloader.exe")
    
    try:
        shutil.copy(dist_exe, target_exe)
        print("\n===================================================")
        print("  BUILD SUCCESSFUL!")
        print(f"  Your Standalone Desktop EXE is located at:\n  {target_exe}")
        print("===================================================")
    except Exception:
        print(f"\n  Build complete! Executable located at:\n  {dist_exe}")
else:
    print(f"\n[!] Build failed with exit code {res.returncode}")

if sys.stdin.isatty():
    input("\nPress Enter to exit...")


