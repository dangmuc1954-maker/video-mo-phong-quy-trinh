"""Chuyển video mới tải nhất (Muse hoặc tool của anh) vào thư mục clip của dự án.

python collect_clip.py <clips_dir> <so_canh> [--max-age 600] [--src <thư mục nguồn, mặc định Downloads>]
→ clips_dir/scene_XX.mp4, in thời lượng + kích thước để kiểm tra.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("clips_dir")
ap.add_argument("scene", type=int)
ap.add_argument("--max-age", type=int, default=600, help="chỉ lấy file tải trong N giây gần đây")
ap.add_argument("--src", default=os.path.join(os.path.expanduser("~"), "Downloads"),
                help="thư mục chứa video vừa tạo (chế độ Tool có thể lưu chỗ khác)")
a = ap.parse_args()

dl = a.src
files = [f for f in glob.glob(os.path.join(dl, "*.mp4")) if not f.endswith(".crdownload")]
if not files:
    sys.exit(f"Không thấy file mp4 nào trong {dl}.")
named = os.path.join(dl, f"scene_{a.scene:02d}.mp4")
newest = named if os.path.isfile(named) else max(files, key=os.path.getmtime)
age = time.time() - os.path.getmtime(newest)
if newest != named and age > a.max_age:
    sys.exit(f"File mới nhất ({os.path.basename(newest)}) tải cách đây {int(age)}s — có thể chưa tải xong cảnh này.")

os.makedirs(a.clips_dir, exist_ok=True)
dst = os.path.join(a.clips_dir, f"scene_{a.scene:02d}.mp4")
shutil.move(newest, dst)

ff = shutil.which("ffprobe")
info = json.loads(subprocess.run([ff, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=width,height:format=duration", "-of", "json", dst],
                                 capture_output=True, text=True).stdout)
st, dur = info["streams"][0], float(info["format"]["duration"])
ok = abs(dur - 10) < 0.6
print(f"{os.path.basename(newest)} → {dst}")
print(f"{dur:.1f}s, {st['width']}x{st['height']}" + ("" if ok else "  ⚠ thời lượng khác 10s"))
