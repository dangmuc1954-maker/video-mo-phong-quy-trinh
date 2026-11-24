"""Thumbnail YouTube 1280×720: dựng 2–3 phương án từ storyboard["thumbnails"], kèm ảnh kiểm tra cỡ nhỏ (như trên điện thoại).

  python thumbnail.py projects/<slug>/storyboard.json
  → projects/<slug>/2-xuat/thumbnail_1.jpg … + render/_thumbs_check.jpg (cỡ lớn + cỡ 246px như lưới gợi ý của YouTube)

storyboard["thumbnails"] = [
  {"layout": "split",   "image": "assets/img/a.jpg", "tags": ["1965","2024"], "top": "TỪ LÀNG CHÀI", "bottom": "GIÀU HƠN MỸ"},
  {"layout": "number",  "image": "...", "big": "725 KM²", "lines": ["KHÔNG TÀI NGUYÊN", "VẪN _GIÀU HƠN MỸ_"], "badge": "×183 LẦN", "ring": [770,150,420,400]},
  {"layout": "concept", "image": "...", "image_box": [170,-150,1664,936], "lines": ["PHẢI MUA", "NƯỚC ĐỂ UỐNG"], "bottom_lines": ["GIÀU", "HƠN MỸ?"],
   "ring": [850,300,300,230], "arrow": [600,210,840,380], "flag": "sg"}
]
Chữ: `_x_` = vàng, `*x*` = đỏ. Ảnh: đường dẫn trong dự án, URL file://, hoặc "File:<tên Wikimedia>" đã tải bằng fetch_assets.
Cờ: mã 2 chữ (sg, us, vn…) → flagcdn. Ảnh nền nên là ảnh Ảnh AI 16:9 (nhân vật / cảnh có cảm xúc mạnh) hoặc ảnh thật có quyền dùng.
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def uri(v: str, proj: Path, assets: dict) -> str:
    if v.startswith(("file:", "http")):
        return v
    if v.startswith("File:") and assets.get("photos", {}).get(v):
        return assets["photos"][v]["file"]
    return (proj / v).resolve().as_uri()


def main() -> None:
    sp = Path(sys.argv[1]).resolve()
    proj = sp.parent
    sb = json.loads(sp.read_text(encoding="utf-8"))
    specs = sb.get("thumbnails") or []
    if not specs:
        sys.exit("storyboard chưa có 'thumbnails' (xem đầu file này).")
    am = proj / "assets" / "assets.json"
    assets = json.loads(am.read_text(encoding="utf-8")) if am.exists() else {}
    out = proj / "2-xuat"
    out.mkdir(exist_ok=True)
    (proj / "render").mkdir(exist_ok=True)
    files = []
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.goto((SKILL / "templates" / "thumb.html").as_uri())
        for i, s in enumerate(specs, 1):
            s = dict(s)
            s["image"] = uri(s["image"], proj, assets)
            if s.get("flag") and len(s["flag"]) == 2:
                ff = proj / "assets" / "flags" / f"{s['flag']}.png"
                ff.parent.mkdir(parents=True, exist_ok=True)
                if not ff.exists():
                    ff.write_bytes(urllib.request.urlopen(urllib.request.Request(f"https://flagcdn.com/w160/{s['flag']}.png", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
                s["flag"] = ff.as_uri()
            pg.evaluate("s => window.build(s)", s)
            pg.wait_for_timeout(250)
            f = out / f"thumbnail_{i}.jpg"
            pg.screenshot(path=str(f), type="jpeg", quality=94)
            files.append(f)
            print(f"✓ {f.name}  ({s.get('layout', 'split')})")
        b.close()
    # ảnh kiểm tra: hàng trên cỡ 640, hàng dưới cỡ 246px (lưới gợi ý trên điện thoại) — chữ phải còn đọc được
    n = len(files)
    ins = sum([["-i", str(f)] for f in files], [])
    fc = "".join(f"[{k}]scale=640:360[a{k}];[{k}]scale=246:138[b{k}];" for k in range(n))
    fc += "".join(f"[a{k}]" for k in range(n)) + f"hstack={n}[top];" if n > 1 else "[a0]null[top];"
    fc += ("".join(f"[b{k}]" for k in range(n)) + f"hstack={n}," if n > 1 else "[b0]") + f"pad={640 * n}:200:0:30:0x111111[bot];[top][bot]vstack"
    chk = proj / "render" / "_thumbs_check.jpg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", str(chk)], check=True)
    print(f"Ảnh kiểm tra cỡ nhỏ: {chk}  → XEM (Read): chữ hàng dưới còn đọc được, chủ thể rõ, không đè mặt/chủ thể.")


if __name__ == "__main__":
    main()
