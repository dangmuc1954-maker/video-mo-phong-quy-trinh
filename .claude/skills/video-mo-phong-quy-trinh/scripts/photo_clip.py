"""Clip cho cảnh ảnh thật + xoá logo Gemini trên clip Studio Kịch Bản.

  python photo_clip.py projects/<slug>/storyboard.json            # cảnh có "real_photo": tải ảnh Commons → 1-canh/scene_XX.mp4 (zoom chậm 1080x1920, 10s)
  python photo_clip.py projects/<slug>/storyboard.json --delogo   # xoá ngôi sao Gemini góc phải dưới của mọi clip 720x1280 (bản gốc → 1-canh/_goc/)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "video-mo-phong/1.0 (educational video tool)"}


def commons(title: str, out: Path) -> str:
    q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                                "iiprop": "url|extmetadata", "iiurlwidth": 2400})
    pg = next(iter(json.loads(urllib.request.urlopen(urllib.request.Request(f"https://commons.wikimedia.org/w/api.php?{q}", headers=UA), timeout=60).read())["query"]["pages"].values()))
    if not pg.get("imageinfo"):
        sys.exit(f"STOP: không có '{title}' trên Commons — tìm đúng tên: python .claude/skills/video-tai-lieu/scripts/find_photo.py \"<tên công trình>\"")
    ii = pg["imageinfo"][0]
    out.write_bytes(urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=120).read())
    md = ii.get("extmetadata", {})
    import re
    art = re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()[:50]
    lic = (md.get("LicenseShortName") or {}).get("value", "")
    return f"{art} · {lic} · Wikimedia Commons"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--delogo", action="store_true")
    a = ap.parse_args()
    sbp = Path(a.storyboard).resolve()
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    cd = sbp.parent / "1-canh"
    cd.mkdir(exist_ok=True)
    if a.delogo:
        (cd / "_goc").mkdir(exist_ok=True)
        n = 0
        for s in sb["scenes"]:
            if s.get("real_photo"):
                continue
            f = cd / s["clip"]
            if not f.exists():
                continue
            g = cd / "_goc" / s["clip"]
            if not g.exists():
                shutil.copy2(f, g)
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(g)], capture_output=True, text=True)
            w, h = map(int, r.stdout.strip().split(","))
            x, y, bw = round(574 * w / 720), round(1134 * h / 1280), round(54 * w / 720)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(g), "-vf", f"delogo=x={x}:y={y}:w={bw}:h={bw}", "-c:v", "libx264", "-crf", "14",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", str(f)], check=True)
            n += 1
        print(f"OK: xoá logo {n} clip (bản gốc trong 1-canh/_goc/)")
        return
    done = 0
    for s in sb["scenes"]:
        if not s.get("real_photo"):
            continue
        img = cd / f"_photo_{s['id']}.jpg"
        credit = commons(s["real_photo"], img)
        W, H = sb.get("canvas", [1080, 1920])
        sec, fps = s.get("seconds", 10), sb.get("fps", 30)
        vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
              f"zoompan=z='min(1+0.0009*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={sec * fps}:s={W}x{H}:fps={fps},format=yuv420p")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(img), "-vf", vf, "-t", str(sec), "-c:v", "libx264", "-crf", "16",
                        str(cd / s["clip"])], check=True)
        s["source"] = s.get("source") or credit
        done += 1
        print(f"  cảnh {s['id']}: {s['real_photo']} → {s['clip']} ({credit})")
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {done} cảnh ảnh thật. Ghi nguồn ảnh vào mô tả video.")


if __name__ == "__main__":
    main()
