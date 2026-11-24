"""Làm đẹp project CapCut đã dựng: kiểu chữ vietsub rõ ràng + hiệu ứng chữ + bộ lọc màu toàn video.

python polish_draft.py "<tên project CapCut>" [--filter-intensity 0.6] [--no-filter]

Dùng bộ kiểu dáng đã học từ giao diện CapCut: assets/capcut_style_pack.json
(chữ trắng viền đen, hiệu ứng vào "Bóng mờ", bộ lọc "Rực sáng").
CapCut phải TẮT khi chạy. Sửa mọi bản draft_content (gốc + Timelines + bản sao lưu) để CapCut không khôi phục bản cũ.
"""
import argparse
import copy
import glob
import json
import os
import subprocess
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "User Data", "Projects", "com.lveditor.draft")
PACK = json.load(open(os.path.join(HERE, "..", "assets", "capcut_style_pack.json"), encoding="utf-8"))


def nid():
    p = str(uuid.uuid4()).upper().split("-")
    return "-".join([p[0], p[1], p[2].lower(), p[3].lower(), p[4]])


def style_texts(d, size=None):
    st = dict(PACK["text_style"])
    cv = d.get("canvas_config", {})
    st["size"] = size or (8 if cv.get("height", 0) > cv.get("width", 1) else st["size"])  # video dọc cần chữ to hơn
    anim_ids = {a["id"] for a in d["materials"].get("material_animations", [])}
    for t in d["materials"].get("texts", []):
        c = json.loads(t["content"])
        n = len(c["text"].encode("utf-16-le")) // 2
        for s in c.get("styles", []) or [{}]:
            s["range"] = [0, n]
            s["size"] = st["size"]
            s["fill"] = {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": st["fill"]}}}
            s["strokes"] = [{"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": st["stroke"]}},
                             "mode": 0, "width": st["stroke_width"]}]
            s["useLetterColor"] = True
        t["content"] = json.dumps(c, ensure_ascii=False)
        t.update({"text_color": "#ffffff", "border_color": "#000000", "border_width": st["stroke_width"],
                  "font_size": float(st["size"]), "has_shadow": True, "shadow_alpha": 0.6})
    # hiệu ứng vào cho từng dòng chữ (thay animation cũ nếu có)
    anims = d["materials"].setdefault("material_animations", [])
    for tr in d["tracks"]:
        if tr["type"] != "text":
            continue
        for seg in tr["segments"]:
            refs = [r for r in seg["extra_material_refs"] if r not in anim_ids]
            a = copy.deepcopy(PACK["text_in_animation"]); a["id"] = nid()
            dur = seg["target_timerange"]["duration"]
            for x in a["animations"]:
                x["duration"] = min(x["duration"], dur // 3)
            anims.append(a)
            seg["extra_material_refs"] = refs + [a["id"]]
    used = {r for tr in d["tracks"] for s in tr["segments"] for r in s.get("extra_material_refs", [])}
    d["materials"]["material_animations"] = [a for a in anims if a["id"] in used]


def add_filter(d, intensity):
    f = PACK["filter"]
    key = f["materials_key"]
    d["tracks"] = [t for t in d["tracks"] if t["type"] != "filter"]
    d["materials"][key] = [m for m in d["materials"].get(key, []) if m.get("type") != "filter"]
    mat = copy.deepcopy(f["material"]); mat["id"] = nid(); mat["value"] = intensity
    seg = copy.deepcopy(f["segment"]); seg["id"] = nid(); seg["material_id"] = mat["id"]
    seg["target_timerange"] = {"start": 0, "duration": d["duration"]}
    tr = copy.deepcopy(f["track"]); tr["id"] = nid(); tr["segments"] = [seg]
    d["materials"][key].append(mat)
    d["tracks"].append(tr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--filter-intensity", type=float, default=PACK["filter"]["intensity"])
    ap.add_argument("--no-filter", action="store_true")
    ap.add_argument("--size", type=float, help="cỡ chữ (mặc định 5 ngang, 8 dọc)")
    a = ap.parse_args()
    if "CapCut.exe" in subprocess.run(["tasklist"], capture_output=True, text=True, errors="ignore").stdout:
        sys.exit("CapCut đang mở. Tắt CapCut rồi chạy lại.")
    folder = os.path.join(ROOT, a.name)
    files = glob.glob(os.path.join(folder, "**", "draft_content.json*"), recursive=True) + \
        glob.glob(os.path.join(folder, "**", "template*.tmp"), recursive=True)
    n = 0
    for fpath in files:
        try:
            d = json.load(open(fpath, encoding="utf-8"))
        except Exception:
            continue
        if "tracks" not in d:
            continue
        style_texts(d, a.size)
        if not a.no_filter:
            add_filter(d, a.filter_intensity)
        json.dump(d, open(fpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        n += 1
    print(f"Đã làm đẹp \"{a.name}\": {n} file — chữ trắng viền đen + hiệu ứng {PACK['text_in_animation']['animations'][0]['name']}"
          + ("" if a.no_filter else f" + bộ lọc {PACK['filter']['material']['name']} {a.filter_intensity:.0%}"))


if __name__ == "__main__":
    main()
