"""Ảnh tĩnh → clip dọc 1080x1920 kiểu video bút chì "dải giữa": nền đen có ánh màu nhẹ, ảnh cắt dải giữa + zoom/pan chậm, tiêu đề cố định phía trên.

  python strip_clips.py projects/<slug>/storyboard.json [--strip 1080x810] [--y 560] [--zoom 0.06]

Đọc: scenes[i] (id), ảnh ref/sNN.jpg (hoặc scene["image"]), thời lượng từng cảnh từ narration/sync.json (slot).
Ghi:  1-canh/scene_NN.mp4 (1080x1920, đúng thời lượng slot) — story_render.py dùng các clip này (giọng + sub story_pop + chữ nhấn).
Tiêu đề: storyboard["top_title"] = {"line1": "...", "line2": "..."} (dòng 2 vàng #FACC15) vẽ thẳng lên nền (đứng yên suốt video, giống video mẫu).
Ánh màu nền theo cảnh: scene["tint"] = "red"|"blue"|"warm"|"none" (mặc định xen kẽ nhẹ theo mood_key).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa: E402

TINT = {"red": (120, 20, 25), "blue": (20, 40, 90), "warm": (130, 90, 25), "none": (0, 0, 0)}
FONTS = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/segoeuib.ttf"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def background(w, h, tint, title, sw, sh, sy) -> Image.Image:
    bg = Image.new("RGB", (w, h), (0, 0, 0))
    if tint != (0, 0, 0):                                   # ánh màu: elip mờ phía sau dải ảnh
        glow = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(glow)
        d.ellipse((-w * .25, sy - sh * .35, w * 1.25, sy + sh * 1.35), fill=tint)
        bg = glow.filter(ImageFilter.GaussianBlur(160))
    d = ImageDraw.Draw(bg)
    if title:
        f = font(86)
        y = 250
        for i, (txt, col) in enumerate(title):
            bb = d.textbbox((0, 0), txt, font=f)
            x = (w - (bb[2] - bb[0])) // 2
            d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0))
            d.text((x, y), txt, font=f, fill=col)
            y += 104
    return bg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--strip", default="1080x810")
    ap.add_argument("--y", type=int, default=560, help="y đầu dải ảnh trên canvas")
    ap.add_argument("--zoom", type=float, default=0.06, help="mức zoom thêm trong cảnh")
    a = ap.parse_args()
    sbp = Path(a.storyboard).resolve()
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    nd = sbp.parent / "narration"
    slots = {str(s["id"]): s["slot"] for s in json.loads((nd / "sync.json").read_text(encoding="utf-8"))["scenes"]}
    W, H = sb.get("canvas", [1080, 1920])
    sw, sh = map(int, a.strip.split("x"))
    tt = sb.get("top_title")
    title = [(tt["line1"], (255, 255, 255)), (tt["line2"], (250, 204, 21))] if tt else None
    cd = sbp.parent / "1-canh"
    cd.mkdir(exist_ok=True)
    tints = ["blue", "none", "red", "none", "warm", "blue"]
    fps = sb.get("fps", 30)
    for i, sc in enumerate(sb["scenes"]):
        sid = str(sc["id"])
        st, en = slots[sid]
        dur = round(en - st, 2)
        img = Path(sc["image"]) if sc.get("image") else sbp.parent / "ref" / f"s{int(sid):02d}.jpg"
        if not img.exists():
            sys.exit(f"STOP: thiếu ảnh {img}")
        tint = TINT[sc.get("tint") or tints[i % len(tints)]]
        bgp = cd / f"_bg_{sid}.png"
        background(W, H, tint, title, sw, sh, a.y).save(bgp)
        # ảnh: phủ kín dải (cắt giữa) rồi zoom chậm; xen kẽ phóng vào / lùi ra
        z = a.zoom
        zexpr = f"1+{z}*on/({int(dur * fps)})" if i % 2 == 0 else f"{1 + z}-{z}*on/({int(dur * fps)})"
        vf = (f"[1:v]scale={sw * 2}:{sh * 2}:force_original_aspect_ratio=increase,crop={sw * 2}:{sh * 2},"
              f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur * fps)}:s={sw}x{sh}:fps={fps}[s];"
              f"[0:v][s]overlay=0:{a.y},format=yuv420p")
        out = cd / f"scene_{int(sid):02d}.mp4"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(dur), "-framerate", str(fps), "-i", str(bgp), "-loop", "1", "-i", str(img),
                            "-filter_complex", vf, "-t", str(dur), "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", str(out)],
                           capture_output=True, text=True, errors="replace")
        if r.returncode:
            sys.exit(f"STOP: ffmpeg lỗi cảnh {sid}: {r.stderr[-300:]}")
        bgp.unlink()
        sc["clip"] = out.name
        print(f"  ✓ cảnh {sid}: {dur}s → {out.name}")
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")   # ghi "clip" cho story_render
    print(f"OK: {len(sb['scenes'])} clip dải giữa trong {cd}")


if __name__ == "__main__":
    main()
