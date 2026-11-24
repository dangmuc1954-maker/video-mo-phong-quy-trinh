"""Chuẩn bị đầu vào cho kiểm cuối độc lập (references/kiem-cuoi.md) → render/review/

  python review_sheet.py projects/<slug> [--video 2-xuat/<file>.mp4] [--per 8]

Mỗi cảnh 3 khung (vừa vào · giữa · sắp hết) → sheet_XX.jpg (ghi giây, cảnh, lời thoại) + brief.md (tóm tắt storyboard).
Mặc định lấy render/video.mp4 (bản graphic); truyền --video để soát bản CapCut đã xuất.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]


def font(sz):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def grab(video: Path, t: float, w: int) -> Image.Image:
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{max(0, t):.3f}", "-i", str(video), "-frames:v", "1", "-vf", f"scale={w}:-2",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB") if r.stdout else Image.new("RGB", (w, w * 9 // 16), (60, 0, 0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video")
    ap.add_argument("--per", type=int, default=8)
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    tl = json.loads((proj / "render" / "timeline.json").read_text(encoding="utf-8"))
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    video = (proj / a.video) if a.video else proj / "render" / "video.mp4"
    out = proj / "render" / "review"
    out.mkdir(parents=True, exist_ok=True)
    txt = {s["id"]: s.get("text") or s.get("narration") or "" for s in sb["scenes"]}
    tw = 420 if tl["W"] >= tl["H"] else 220
    th = round(tw * tl["H"] / tl["W"])
    f1, f2 = font(18), font(15)
    sc = tl["scenes"]
    for n in range(0, len(sc), a.per):
        grp = sc[n:n + a.per]
        rowh = th + 52
        img = Image.new("RGB", (tw * 3 + 40, rowh * len(grp) + 10), (18, 18, 22))
        d = ImageDraw.Draw(img)
        for r, s in enumerate(grp):
            st, en = s["start"], s["end"]
            ts = [st + .35, (st + en) / 2, en - .2]
            y = r * rowh + 8
            d.text((10, y), f"Cảnh {s['id']} · {s['module']} · {st:.1f}–{en:.1f}s", fill=(250, 204, 21), font=f1)
            d.text((10, y + 22), txt.get(s["id"], "")[:150], fill=(220, 220, 220), font=f2)
            for c, t in enumerate(ts):
                im = grab(video, t, tw)
                img.paste(im, (10 + c * (tw + 10), y + 46))
                d.text((14 + c * (tw + 10), y + 48), f"{t:.1f}s", fill=(255, 255, 255), font=f2)
        img.save(out / f"sheet_{n // a.per + 1:02d}.jpg", quality=85)
    md = [f"# Tóm tắt để kiểm: {sb.get('title', proj.name)}", f"Video soát: {video.name} · {tl['duration']:.1f}s · {tl['W']}x{tl['H']}", ""]
    for s, raw in zip(tl["scenes"], sb["scenes"]):
        p = raw.get("p") or {}
        md.append(f"## Cảnh {s['id']} ({s['start']:.1f}–{s['end']:.1f}s) · {s['module']}" + (" · có nhịp then: " + ", ".join(b.get("module", "") for b in p.get("then") or []) if p.get("then") else ""))
        md.append(f"- Lời: {txt.get(s['id'], '')}")
        if raw.get("keywords"):
            md.append("- Chữ chốt: " + "; ".join(f"{k.get('text')} ({k.get('effect', '')})" for k in raw["keywords"]))
        if raw.get("callouts"):
            md.append("- Logo/ảnh: " + "; ".join(i.get("name", "?") for g in raw["callouts"] for i in (g.get("items") or [g])))
        if p.get("source"):
            md.append(f"- Nguồn: {p['source']}")
        md.append("")
    rr = proj / "render" / "rule_report.md"
    if rr.exists():
        md += ["---", rr.read_text(encoding="utf-8")]
    (out / "brief.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Xong: {len(list(out.glob('sheet_*.jpg')))} tờ ảnh + brief.md → {out}")


if __name__ == "__main__":
    main()
