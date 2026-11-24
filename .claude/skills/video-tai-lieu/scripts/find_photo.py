"""Tìm ảnh THẬT trên Wikimedia Commons, xem trước bằng mắt rồi mới chọn (không đoán tên file).

  python find_photo.py "Ha Long Bay" [-n 12] [--out projects/<slug>/render/_find.jpg]
  python find_photo.py "UNESCO logo" --pick 1 --save brand/logos/unesco.png     # tải ảnh số 1 (logo → dùng "logo": "unesco")

In danh sách: số thứ tự · tên file (dùng nguyên văn "File:…" trong storyboard) · kích thước · giấy phép · tác giả,
và ghép ảnh xem trước có đánh số → Read ảnh đó, chọn ảnh đúng nơi / đúng người / không watermark.
Từ khoá tiếng Anh thường ra nhiều ảnh hơn. Logo tổ chức: thêm "logo" (vd "UNESCO logo") rồi lưu vào brand/logos/<tên>.png.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "video-tai-lieu/1.0 (documentary video tool)"}


def get(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-n", type=int, default=12)
    ap.add_argument("--out", default="_find_photo.jpg")
    ap.add_argument("--pick", type=int, help="tải ảnh số N (bản ~1600px, PNG/JPG)")
    ap.add_argument("--save", help="nơi lưu ảnh --pick")
    a = ap.parse_args()
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": a.query, "gsrnamespace": 6,
                                "gsrlimit": a.n, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 400})
    pages = sorted(json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q}")).get("query", {}).get("pages", {}).values(),
                   key=lambda p: p.get("index", 0))
    if not pages:
        sys.exit(f"STOP: không có ảnh nào cho '{a.query}' — thử từ khoá tiếng Anh / ngắn hơn.")
    from PIL import Image, ImageDraw
    if a.pick:
        p = pages[a.pick - 1]; ii = p["imageinfo"][0]
        q2 = urllib.parse.urlencode({"action": "query", "format": "json", "titles": p["title"], "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 1600})
        u = next(iter(json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q2}"))["query"]["pages"].values()))["imageinfo"][0]["thumburl"]
        im = Image.open(io.BytesIO(get(u)))
        dst = Path(a.save or f"{re.sub(r'[^a-z0-9]+', '_', a.query.lower())}.png"); dst.parent.mkdir(parents=True, exist_ok=True)
        (im.convert("RGBA") if dst.suffix.lower() == ".png" else im.convert("RGB")).save(dst)
        lic = (ii.get("extmetadata", {}).get("LicenseShortName") or {}).get("value", "?")
        print(f"OK: đã lưu {dst.resolve()} ← {p['title']} ({lic}). Ghi nguồn: Wikimedia Commons.")
        return
    thumbs = []
    for i, p in enumerate(pages, 1):
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName") or {}).get("value", "?")
        art = re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()[:40]
        print(f"{i:2d}. {p['title']}  ({ii.get('width')}x{ii.get('height')}, {lic}, {art})")
        try:
            im = Image.open(io.BytesIO(get(ii["thumburl"]))).convert("RGB")
            im.thumbnail((400, 300))
        except Exception:  # noqa: BLE001
            im = Image.new("RGB", (400, 300), (40, 40, 40))
        tile = Image.new("RGB", (400, 330), (20, 20, 20)); tile.paste(im, ((400 - im.width) // 2, 0))
        ImageDraw.Draw(tile).text((8, 306), f"{i}", fill=(250, 204, 21))
        thumbs.append(tile)
    cols = 4; rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 400, rows * 330), (0, 0, 0))
    for k, t in enumerate(thumbs):
        sheet.paste(t, ((k % cols) * 400, (k // cols) * 330))
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out, quality=85)
    print(f"\nOK: xem trước {out.resolve()} (Read) → ghi \"File:…\" của ảnh chọn vào photo / bg_photo.")


if __name__ == "__main__":
    main()
