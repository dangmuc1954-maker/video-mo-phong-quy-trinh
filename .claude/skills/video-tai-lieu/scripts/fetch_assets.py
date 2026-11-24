"""Tự tìm tư liệu cho video-tai-lieu: toạ độ, ảnh vệ tinh nhiều mức zoom, địa cầu, icon, ảnh thật (Wikimedia Commons).

  python fetch_assets.py projects/<slug>/storyboard.json

Đọc storyboard.json, ghi vào projects/<slug>/assets/ và assets/assets.json:
  - scene module "map": p.places = [{"name": "Cần Giờ, TP.HCM"} | {"lat":..,"lon":..}, "zoom": 12, "label": "..", "cue": ".."}]
      → toạ độ (OpenStreetMap Nominatim), ảnh vệ tinh Esri World Imagery ở các mức zoom cần cho cú bay,
        p.from_space → thêm địa cầu (globe.jpg)
  - mọi "icon": "<tên lucide>" trong p → assets/icons/<tên>.svg (Lucide, ISC)
  - mọi "photo_query": "..." trong p (hoặc trong left/right/items) → ảnh Wikimedia Commons + tác giả + giấy phép
      ("photo": "<file hoặc URL>" có sẵn thì giữ nguyên; URL được tải về)
Nguồn và giấy phép ghi vào assets/credits.json để hiện lên video và mô tả.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "video-tai-lieu-skill/1.0 (documentary renderer)"}
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
ESRI_CREDIT = "Ảnh vệ tinh: Esri, Maxar, Earthstar Geographics"
LUCIDE = "https://unpkg.com/lucide-static@0.460.0/icons/{name}.svg"
GRID = 8  # 8x8 tiles = 2048px per zoom level


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def geocode(name: str) -> tuple[float, float]:
    q = urllib.parse.urlencode({"q": name, "format": "json", "limit": 1})
    data = json.loads(get(f"https://nominatim.openstreetmap.org/search?{q}"))
    time.sleep(1.1)  # Nominatim: tối đa 1 yêu cầu/giây
    if not data:
        raise SystemExit(f"Không tìm được toạ độ cho '{name}'. Ghi lat/lon trực tiếp trong storyboard.")
    return float(data[0]["lat"]), float(data[0]["lon"])


def tile_xy(lat: float, lon: float, z: int) -> tuple[float, float]:
    n = 2 ** z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def tile_to_ll(x: float, y: float, z: int) -> tuple[float, float]:
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def stitch(lat: float, lon: float, z: int, out: Path) -> dict:
    from PIL import Image
    if out.exists():
        x0 = json.loads(out.with_suffix(".json").read_text())
        return x0
    n = 2 ** z
    cx, cy = tile_xy(lat, lon, z)
    g = min(GRID, n)
    x0 = int(math.floor(cx - g / 2)) if n > g else 0
    y0 = int(math.floor(cy - g / 2)) if n > g else 0
    y0 = max(0, min(n - g, y0))
    img = Image.new("RGB", (g * 256, g * 256))
    from concurrent.futures import ThreadPoolExecutor

    def one(ij):
        i, j = ij
        tx, ty = (x0 + i) % n, y0 + j
        for _ in range(3):
            try:
                return i, j, Image.open(io.BytesIO(get(ESRI.format(z=z, x=tx, y=ty)))).convert("RGB")
            except Exception:  # noqa: BLE001
                time.sleep(.5)
        print(f"  ! tile {z}/{ty}/{tx} lỗi")
        return i, j, None
    with ThreadPoolExecutor(12) as ex:
        for i, j, im in ex.map(one, [(i, j) for i in range(g) for j in range(g)]):
            if im:
                img.paste(im, (i * 256, j * 256))
    img.save(out, quality=88)
    clat, clon = tile_to_ll(x0 + g / 2, y0 + g / 2, z)
    meta = {"file": out.as_uri(), "z": z, "lat": clat, "lon": clon}
    out.with_suffix(".json").write_text(json.dumps(meta))
    return meta


GB = "https://github.com/wmgeolab/geoBoundaries/raw/main/releaseData/gbOpen/{iso}/ADM0/geoBoundaries-{iso}-ADM0_simplified.geojson"
GB_CREDIT = "Biên giới: geoBoundaries (CC BY 4.0) — geoboundaries.org"


def geo_rings(iso: str, out_dir: Path) -> str:
    """Viền quốc gia (ISO3, vd SGP, MYS, VNM) → danh sách vòng [[lon,lat],…] cho lớp phủ bản đồ v2."""
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{iso}.json"
    if not f.exists():
        d = json.loads(get(GB.format(iso=iso), timeout=120))
        rings = []
        for ft in d["features"]:
            g = ft["geometry"]
            for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
                if len(poly[0]) >= 4:
                    rings.append([[round(x, 4), round(y, 4)] for x, y in poly[0]])
        f.write_text(json.dumps(rings, separators=(",", ":")))
    return str(f)


def commons_photo(query: str, out_dir: Path) -> dict | None:
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
                                "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                                "iiurlwidth": 1400})
    data = json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q}"))
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("width", 0) < 500:
            continue
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName") or {}).get("value", "")
        art = (md.get("Artist") or {}).get("value", "")
        import re
        art = re.sub(r"<[^>]+>", "", art).strip()[:60]
        url = ii.get("thumburl") or ii.get("url")
        ext = ".jpg" if ".jp" in url.lower() else ".png"
        safe = "".join(c if c.isalnum() else "_" for c in query)[:40]
        f = out_dir / f"photo_{safe}{ext}"
        if not f.exists():
            f.write_bytes(get(url))
        return {"file": f.as_uri(), "credit": f"{art or 'Wikimedia Commons'} / {lic or 'Wikimedia Commons'}",
                "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(p.get("title", "")), "query": query}
    return None


def commons_file(title: str, out_dir: Path) -> dict:
    q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                                "iiprop": "url|extmetadata", "iiurlwidth": 2000})
    for k in range(5):
        try:
            data = json.loads(get(f"https://commons.wikimedia.org/w/api.php?{q}"))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(10 * (k + 1))
    pg = next(iter(data["query"]["pages"].values()))
    if not pg.get("imageinfo"):
        raise ValueError(f"không có file '{title}' trên Commons — tìm tên đúng: python .claude/skills/video-tai-lieu/scripts/find_photo.py \"từ khoá\"")
    ii = pg["imageinfo"][0]
    md = ii.get("extmetadata", {})
    import re
    art = re.sub(r"\s*\(talk.*$", "", re.sub(r"^Taken by\s+", "", re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()))[:40]
    lic = (md.get("LicenseShortName") or {}).get("value", "")
    url = ii.get("thumburl") or ii["url"]
    f = out_dir / ("commons_" + "".join(c if c.isalnum() else "_" for c in title[5:])[:60] + ".jpg")
    if not f.exists():
        for k in range(5):
            try:
                f.write_bytes(get(url, timeout=120))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(10 * (k + 1))
    return {"file": f.as_uri(), "credit": f"{art or 'Wikimedia Commons'} / {lic}",
            "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title)}


def social_video(url: str, out_dir: Path, credit: str | None) -> dict:
    """Video công khai trên mạng xã hội (Facebook, Instagram, Threads, TikTok, YouTube…) qua yt-dlp.
    Bản quyền thuộc người đăng: luôn ghi nguồn, liệt kê để anh duyệt trước khi đăng."""
    import subprocess
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "social_" + str(abs(hash(url)) % 10**8)
    f = out_dir / f"{name}.mp4"
    if not f.exists():
        r = subprocess.run([sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=1080][ext=mp4]+ba/b[ext=mp4]/b", "--merge-output-format", "mp4",
                            "-o", str(out_dir / f"{name}.%(ext)s"), "--no-playlist", url], capture_output=True, text=True)
        if r.returncode or not f.exists():
            raise RuntimeError((r.stderr or r.stdout)[-300:] + " (bài riêng tư / cần đăng nhập → nhờ anh tải hoặc dùng --cookies-from-browser)")
    host = urllib.parse.urlparse(url).netloc.replace("www.", "")
    return {"file": f.as_uri(), "credit": credit or host, "page": url, "social": True}


def walk(o, fn):
    if isinstance(o, dict):
        fn(o)
        for v in o.values():
            walk(v, fn)
    elif isinstance(o, list):
        for v in o:
            walk(v, fn)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    a = ap.parse_args()
    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    sb = json.loads(sp.read_text(encoding="utf-8"))
    ad = proj / "assets"
    (ad / "maps").mkdir(parents=True, exist_ok=True)
    (ad / "icons").mkdir(exist_ok=True)
    (ad / "photos").mkdir(exist_ok=True)
    manifest = {"maps": {}, "photos": {}, "globe": None, "credits": []}
    credits: set[str] = set()

    # ---- maps ----
    for sc in sb["scenes"]:
        p = sc.get("p") or {}
        if sc.get("module") != "map":
            continue
        stops = []
        for pl in p.get("places", []):
            if "lat" not in pl:
                pl["lat"], pl["lon"] = geocode(pl["name"])
                print(f"  toạ độ {pl['name']}: {pl['lat']:.4f}, {pl['lon']:.4f}")
            stops.append(pl)
        zs = sorted({4, 6, 8} | {int(z) for s in stops for z in range(8, int(s.get("zoom", 12)) + 2, 2)})
        levels = []
        for s in stops:
            for z in zs:
                if z > s.get("zoom", 12) + 1:
                    continue
                key = f"{z}_{s['lat']:.3f}_{s['lon']:.3f}"
                # low zooms are shared between nearby stops
                if z <= 6 and levels and any(L["z"] == z for L in levels):
                    continue
                print(f"  vệ tinh z{z} quanh {s.get('label') or s.get('name')}")
                levels.append(stitch(s["lat"], s["lon"], z, ad / "maps" / f"z{key}.jpg"))
        manifest["maps"][str(sc["id"])] = {"stops": stops, "levels": levels}
        credits.add(ESRI_CREDIT)
        if p.get("from_space") and not manifest["globe"]:
            print("  địa cầu (z3)")
            g = stitch(0, 105, 3, ad / "maps" / "globe_z3.jpg")
            manifest["globe"] = g["file"]

    # ---- viền quốc gia cho lớp phủ bản đồ (p.borders / p.split) ----
    isos: set[str] = set()
    for sc in sb["scenes"]:
        p = sc.get("p") or {}
        isos |= {b["iso"] for b in p.get("borders", []) if b.get("iso")}
        if (p.get("split") or {}).get("iso"):
            isos.add(p["split"]["iso"])
    manifest["geo"] = {}
    for iso in sorted(isos):
        try:
            manifest["geo"][iso] = geo_rings(iso, ad / "geo")
            print(f"  viền {iso}: geoBoundaries")
            credits.add(GB_CREDIT)
        except Exception as e:  # noqa: BLE001
            print(f"  ! viền {iso}: {e}")
    # ---- cờ quốc gia ("flag": "sg" → ảnh tròn trong module race) ----
    flags: set[str] = set()
    walk(sb, lambda d: flags.add(d["flag"]) if isinstance(d.get("flag"), str) and len(d["flag"]) == 2 else None)
    manifest["flags"] = {}
    for cc in sorted(flags):
        ff = ad / "flags" / f"{cc}.png"
        ff.parent.mkdir(exist_ok=True)
        try:
            if not ff.exists():
                ff.write_bytes(get(f"https://flagcdn.com/w160/{cc}.png"))
            manifest["flags"][cc] = ff.as_uri()
        except Exception as e:  # noqa: BLE001
            print(f"  ! cờ {cc}: {e}")

    # ---- icons ----
    icons: set[str] = set()
    walk(sb, lambda d: icons.add(d["icon"]) if isinstance(d.get("icon"), str) else None)
    for name in sorted(icons):
        f = ad / "icons" / f"{name}.svg"
        if not f.exists():
            try:
                f.write_bytes(get(LUCIDE.format(name=name)))
            except Exception as e:  # noqa: BLE001
                print(f"  ! icon {name}: {e} (dùng tên khác ở lucide.dev/icons)")
    manifest["icon_base"] = (ad / "icons").as_uri() + "/"

    # ---- photos ----
    def photo(d: dict):
        q = d.get("photo_query")
        if q and q not in manifest["photos"]:
            try:
                r = commons_photo(q, ad / "photos")
            except Exception as e:  # noqa: BLE001
                r = None
                print(f"  ! ảnh '{q}': {e}")
            manifest["photos"][q] = r
            print(f"  ảnh '{q}': {'có — ' + r['credit'] if r else 'KHÔNG tìm được (dùng ảnh khác hoặc bỏ)'}")
            if r:
                credits.add(f"{r['credit']} — {r['page']}")
        for key, credk in (("photo", "source"), ("bg_photo", "bg_source"), ("bg_video", "bg_source"), ("video", "source")):
            u = d.get(key)
            if not isinstance(u, str) or u in manifest["photos"] or u.startswith("file:"):
                continue
            try:
                if u.startswith("File:"):  # ảnh Wikimedia Commons theo tên file (đã chọn bằng mắt)
                    r = commons_file(u, ad / "photos")
                elif u.startswith("http") and key == "bg_video" and not u.lower().split("?")[0].endswith((".mp4", ".webm", ".mov")):
                    r = social_video(u, ad / "videos", d.get(credk))  # link mạng xã hội / YouTube / TikTok / FB…
                elif u.startswith("http"):
                    ext = ".mp4" if key == "bg_video" else ".jpg"
                    f = ad / ("videos" if key == "bg_video" else "photos") / ("url_" + str(abs(hash(u)) % 10**8) + ext)
                    f.parent.mkdir(exist_ok=True)
                    if not f.exists():
                        f.write_bytes(get(u, timeout=120))
                    r = {"file": f.as_uri(), "credit": d.get(credk) or urllib.parse.urlparse(u).netloc, "page": d.get("page", u)}
                elif (proj / u).is_file():  # ảnh/clip trong dự án (vd tranh Ảnh AI assets/img/x.jpg)
                    r = {"file": (proj / u).resolve().as_uri(), "credit": d.get(credk) or ("Quay màn hình thật" if key == "video" else "Tranh minh hoạ (AI)"), "page": ""}
                else:
                    continue
            except Exception as e:  # noqa: BLE001
                print(f"  ! không lấy được {key} '{u[:80]}': {e}")
                r = None
            manifest["photos"][u] = r
            if r:
                print(f"  {key}: {r['credit']}")
                credits.add(f"{r['credit']} — {r.get('page', '')}")
    walk(sb, photo)
    sp.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")  # toạ độ đã tra được ghi lại
    manifest["credits"] = sorted(credits)
    (ad / "assets.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Xong tư liệu → {ad / 'assets.json'}")


if __name__ == "__main__":
    main()
