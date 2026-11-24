"""Soi khung hình để lấy mốc SFX CHÍNH XÁC (bắt đầu + kết thúc hành động) trên video đã dựng.

Mỗi cảnh → 1 ảnh lưới khung hình, 4 khung/giây (mỗi ô 0,25s), góc trên ghi GIÂY TRÊN TIMELINE.
Claude xem ảnh, đọc đúng giây hành động bắt đầu / kết thúc (gõ phím, cãi nhau, bước chân, chim bay…)
rồi ghi vào storyboard: scene.sfx[i].at / .end (giây timeline). capcut_post.py dùng các mốc này.

  python sfx_frames.py projects/<slug>/storyboard.json [--video <mp4>] [--fps 4] [--scenes 2,5]

Video mặc định: bản FFmpeg đầy đủ "2-xuat/<title> (giong ke).mp4" (cùng timeline với project CapCut).
Ảnh ra: projects/<slug>/narration/build/sfx_frames/scene_XX.jpg
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--video")
    ap.add_argument("--fps", type=float, default=4.0)
    ap.add_argument("--scenes", help="chỉ các cảnh này, vd 2,5")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = json.loads(sp.read_text(encoding="utf-8"))
    sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
    video = Path(a.video) if a.video else proj / "2-xuat" / f"{story.get('title', proj.name)} (giong ke).mp4"
    if not video.exists():
        sys.exit(f"Không thấy video {video}. Chạy story_render.py trước (hoặc --video).")
    only = {int(x) for x in a.scenes.split(",")} if a.scenes else None
    out = proj / "narration" / "build" / "sfx_frames"
    out.mkdir(parents=True, exist_ok=True)

    # drawtext needs a font path without a drive colon → copy a font next to the work dir
    work = Path(tempfile.mkdtemp(prefix="sfxf_"))
    font = next((f for f in (Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
                 if f.exists()), None)
    if font:
        shutil.copy(font, work / "f.ttf")
    shutil.copy(video, work / "v.mp4")
    for s in sync["scenes"]:
        if only and s["id"] not in only:
            continue
        a0, a1 = s["slot"]
        a0 = max(0.0, a0 - 0.25)
        dur = a1 - a0 + 0.25
        n = max(1, int(math.ceil(dur * a.fps)))
        cols = 12
        rows = int(math.ceil(n / cols))
        label = (f",drawtext=fontfile=f.ttf:text='%{{pts\\:flt}}':x=3:y=3:fontsize=18:fontcolor=red:"
                 f"box=1:boxcolor=white") if font else ""
        vf = f"setpts=PTS+{a0}/TB,fps={a.fps},scale=150:-1{label},tile={cols}x{rows}"
        dst = out / f"scene_{s['id']:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a0:.3f}", "-t", f"{dur:.3f}", "-i", "v.mp4",
                        "-vf", vf, "-frames:v", "1", "out.jpg"], cwd=work, check=True)
        shutil.move(str(work / "out.jpg"), dst)
        print(f"Cảnh {s['id']}: {s['slot'][0]:.2f}–{s['slot'][1]:.2f}s → {dst}")
    shutil.rmtree(work, ignore_errors=True)
    print("Xem từng ảnh, ghi scene.sfx[i].at = giây hành động BẮT ĐẦU, .end = giây hành động KẾT THÚC (số đỏ trên ô).")


if __name__ == "__main__":
    main()
