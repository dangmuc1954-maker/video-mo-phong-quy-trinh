"""Ảnh AI (Banana/Gemini) còn logo ngôi sao góc dưới phải → tự xử lý sau khi lấy ảnh về. Chỉ ĐỌC dữ liệu của tool.

  python gemini_wm.py projects/<slug>/storyboard.json            # các ảnh trong storyboard["image_jobs"]
  python gemini_wm.py --files a.jpg b.png [--force]                # file bất kỳ (--force: xử lý không cần tra job)

Cách làm: tra job trong queue-state.json theo prompt; nếu job KHÔNG bật xoá watermark (payload.removeWatermark khác true)
mà nền tảng là Gemini/Banana → cắt khung 88% từ góc trên trái (đẩy ngôi sao ra ngoài) rồi phóng lại đúng kích thước gốc.
Bản gốc giữ ở <tên>.orig.<đuôi>. Đồng thời cảnh báo nếu tỉ lệ ảnh khác storyboard["aspect"] (vd ảnh 9:16 cho video 16:9).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(os.environ.get("APPDATA", "")) / "AI_VIDEO_LIBRARY_DATA"
KEEP = 0.88


def norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def fix(f: Path) -> None:
    from PIL import Image
    im = Image.open(f)
    w, h = im.size
    bak = f.with_name(f.stem + ".orig" + f.suffix)
    if not bak.exists():
        shutil.copy2(f, bak)
    im = Image.open(bak).convert("RGB")
    im.crop((0, 0, round(w * KEEP), round(h * KEEP))).resize((w, h), Image.LANCZOS).save(f, quality=95)
    print(f"  ✂ {f.name}: đã đẩy logo ra khỏi khung (bản gốc: {bak.name})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard", nargs="?")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.files:
        for f in a.files:
            fix(Path(f))
        return
    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    sb = json.loads(sp.read_text(encoding="utf-8"))
    want = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0, "4:3": 4 / 3, "3:4": 3 / 4}.get(sb.get("aspect") or ("16:9" if (sb.get("canvas") or [1080, 1920])[0] > (sb.get("canvas") or [1080, 1920])[1] else "9:16"))
    q = json.loads((DATA / "queue-state.json").read_text(encoding="utf-8")) if (DATA / "queue-state.json").exists() else {}
    jobs = [j for j in q.get("jobs", []) if j.get("type") == "Image"]
    from PIL import Image
    for t in sb.get("image_jobs", []):
        f = proj / t["dest"]
        if not f.exists():
            continue
        j = next((j for j in sorted(jobs, key=lambda j: j.get("createdAt", ""), reverse=True) if norm(j.get("payload", {}).get("prompt")) == norm(t["prompt"])), None)
        pl = (j or {}).get("payload", {})
        prov = norm((j or {}).get("provider")) + norm(pl.get("model"))
        w, h = Image.open(f).size
        if want and abs(w / h - want) > 0.05:
            print(f"  ⚠ {t['dest']}: tỉ lệ ảnh {w}x{h} khác video ({sb.get('aspect')}) — đổi tỉ lệ dòng đó trong tool rồi tạo lại.")
        if f.with_name(f.stem + ".orig" + f.suffix).exists():
            continue
        if a.force or (j and not pl.get("removeWatermark") and any(k in prov for k in ("banana", "gemini", "imagen"))):
            fix(f)
        else:
            print(f"  ✓ {t['dest']}: job đã bật xoá watermark hoặc không phải Gemini")


if __name__ == "__main__":
    main()
