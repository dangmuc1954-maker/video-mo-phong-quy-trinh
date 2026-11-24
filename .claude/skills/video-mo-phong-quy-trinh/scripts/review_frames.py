"""Tờ ảnh kiểm cuối cho video mô phỏng: mỗi cảnh 4 khung (đầu / 35% / 70% / cuối) trích TỪ VIDEO THẬT + lời kể + beats.

  python review_frames.py projects/<slug> [--video <file.mp4>]

Ra projects/<slug>/render/review/sheet_XX.jpg (6 cảnh / tờ) + brief.md (lời kể và beats từng cảnh, đối chiếu hình).
Agent soát đọc brief.md + các sheet, rồi trích thêm khung nếu cần. (review_sheet.py của video-tai-lieu KHÔNG dùng cho video này.)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
    vid = Path(a.video) if a.video else next(iter(sorted((proj / "2-xuat").glob("*giong ke*.mp4"))), None)
    if not vid or not vid.exists():
        sys.exit("STOP: không thấy video để soát (--video <file.mp4>)")
    out = proj / "render" / "review"
    out.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    slots = {str(s["id"]): s["slot"] for s in sync["scenes"]}
    brief = [f"# Brief kiểm cuối — {sb.get('title', proj.name)}", "", f"Video: {vid.name}. Mỗi cảnh 4 khung theo thứ tự thời gian (đầu, 35%, 70%, cuối).", ""]
    rows = []
    for sc in sb["scenes"]:
        sid = str(sc["id"])
        st, en = slots[sid]
        ts = [st + 0.15, st + (en - st) * .35, st + (en - st) * .70, en - 0.2]
        tiles = []
        for t in ts:
            f = out / f"_t_{sid}_{int(t * 10)}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(vid), "-frames:v", "1", "-vf", "scale=270:-1", str(f)], check=True)
            tiles.append(Image.open(f).convert("RGB"))
            f.unlink()
        w, h = tiles[0].size
        row = Image.new("RGB", (w * 4 + 90, h), (20, 20, 20))
        ImageDraw.Draw(row).text((6, 6), f"{sid}", fill=(250, 204, 21), font=font)
        for i, t in enumerate(tiles):
            row.paste(t, (90 + i * w, 0))
        rows.append(row)
        brief.append(f"## Cảnh {sid} ({st:.1f}–{en:.1f}s)\nLời kể: {sc['narration']}")
        if sc.get("graphic"):
            brief.append(f"Chữ lớn: {sc['graphic']['data']['lines']} (cue '{sc['graphic']['cue']}')")
        for b in sc.get("beats", []):
            brief.append(f"- {b[0]}: {b[1]}")
        brief.append("")
    for k in range(0, len(rows), 6):
        grp = rows[k:k + 6]
        sheet = Image.new("RGB", (grp[0].width, sum(r.height for r in grp)), (0, 0, 0))
        y = 0
        for r in grp:
            sheet.paste(r, (0, y)); y += r.height
        sheet.save(out / f"sheet_{k // 6 + 1:02d}.jpg", quality=88)
    (out / "brief.md").write_text("\n".join(brief), encoding="utf-8")
    print(f"OK: {len(rows)} cảnh → {out} (sheet_*.jpg + brief.md)")


if __name__ == "__main__":
    main()
