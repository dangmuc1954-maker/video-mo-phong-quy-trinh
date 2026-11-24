"""Tạo project nháp CapCut từ danh sách clip + phụ đề.

Cách dùng:
    python build_capcut_draft.py storyboard.json [--clips-dir DIR] [--force]

storyboard.json cần có:
    "title": tên project CapCut
    "scenes": [{"id": 1, "clip": "scene_01.mp4", "subtitle": "..."} ...]
    (tuỳ chọn) "transition": true/false — thêm chuyển cảnh giữa các cảnh

Script không tự nghĩ ra cấu trúc JSON của CapCut: nó lấy mẫu từ các project
có sẵn của anh (một project có video + chữ, một project có chuyển cảnh),
nhân bản các phần đó rồi thay đường dẫn, thời lượng, nội dung chữ.
CapCut phải được TẮT khi chạy, vì lúc thoát CapCut ghi đè danh sách project.
"""
import argparse
import copy
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

ROOT = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "User Data", "Projects", "com.lveditor.draft")
ROOT_FWD = ROOT.replace("\\", "/")
MARKER = ".tao_boi_skill_video_hoat_hinh"  # đánh dấu project do skill tạo
SKIP_FILES = {"draft_content.json.bak", "template.tmp", "template-2.tmp", "project.json.bak"}


def new_id():
    u = str(uuid.uuid4()).upper()
    # CapCut dùng kiểu XXXXXXXX-XXXX-4xxx-xxxx-XXXXXXXXXXXX (2 nhóm giữa viết thường)
    p = u.split("-")
    return "-".join([p[0], p[1], p[2].lower(), p[3].lower(), p[4]])


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def capcut_running():
    out = subprocess.run(["tasklist"], capture_output=True, text=True, errors="ignore").stdout
    return "CapCut.exe" in out


def probe(path):
    ff = shutil.which("ffprobe")
    if not ff:
        sys.exit("Không tìm thấy ffprobe trong PATH.")
    r = subprocess.run([ff, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    info = json.loads(r.stdout)
    st = info["streams"][0]
    has_audio = bool(json.loads(subprocess.run(
        [ff, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "json", path],
        capture_output=True, text=True).stdout).get("streams"))
    return {"w": st["width"], "h": st["height"],
            "us": int(float(info["format"]["duration"]) * 1_000_000), "audio": has_audio}


SKILL_TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "capcut_templates")


def all_drafts(root=ROOT):
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, "draft_content.json")
        if os.path.isfile(p) and not os.path.isfile(os.path.join(root, name, MARKER)):
            try:
                yield os.path.join(root, name), load(p)
            except Exception:
                continue


def find_templates():
    """Tìm project mẫu mới nhất có video+chữ, và một project có chuyển cảnh."""
    base = trans = None
    for name, d in list(all_drafts()) + list(all_drafts(SKILL_TEMPLATES)):
        types = [t["type"] for t in d["tracks"]]
        ver = tuple(int(x) for x in d.get("new_version", "0").split("."))
        if "video" in types and "text" in types and (base is None or ver >= base[2]):
            base = (name, d, ver)
        if d["materials"].get("transitions") and (trans is None or ver >= trans[2]):
            trans = (name, d, ver)
    if not base:
        sys.exit("Cần ít nhất 1 project CapCut có video và chữ để làm mẫu. "
                 "Mở CapCut, kéo 1 video vào, thêm 1 dòng chữ, lưu lại rồi chạy lại.")
    return base, trans


class Cloner:
    """Nhân bản segment kèm toàn bộ material nó tham chiếu, đổi sang ID mới."""

    def __init__(self, src_doc, out_materials):
        self.index = {}
        for key, lst in src_doc["materials"].items():
            if isinstance(lst, list):
                for m in lst:
                    if isinstance(m, dict) and "id" in m:
                        self.index[m["id"]] = (key, m)
        self.out = out_materials

    def material(self, mid):
        key, m = self.index[mid]
        c = copy.deepcopy(m)
        c["id"] = new_id()
        self.out.setdefault(key, []).append(c)
        return c

    def segment(self, seg):
        s = copy.deepcopy(seg)
        s["id"] = new_id()
        main = self.material(seg["material_id"])
        s["material_id"] = main["id"]
        refs, extras = [], {}
        for r in seg.get("extra_material_refs", []):
            if r in self.index:
                key = self.index[r][0]
                if key == "transitions":  # bỏ chuyển cảnh cũ, sẽ gắn lại sau
                    continue
                c = self.material(r)
                refs.append(c["id"])
                extras[key] = c
        s["extra_material_refs"] = refs
        return s, main, extras


def set_text(mat, text, size=5.0):
    content = json.loads(mat["content"])
    content["text"] = text
    for st in content.get("styles", []):
        st["range"] = [0, len(text.encode("utf-16-le")) // 2]
        st["fill"] = {"content": {"render_type": "solid", "solid": {"color": [1, 1, 1]}}}
        st["size"] = size
    mat["content"] = json.dumps(content, ensure_ascii=False)
    mat["text_color"] = "#ffffff"
    mat["font_size"] = float(size)
    mat["border_color"] = "#000000"


def remove_old(name):
    """Xoá project cũ cùng tên NẾU do skill này tạo (có file đánh dấu)."""
    d = os.path.join(ROOT, name)
    if not os.path.isfile(os.path.join(d, MARKER)):
        return False
    shutil.rmtree(d)
    rpath = os.path.join(ROOT, "root_meta_info.json")
    root = load(rpath)
    root["all_draft_store"] = [e for e in root["all_draft_store"]
                               if not e.get("draft_fold_path", "").endswith("/" + name)]
    dump(root, rpath)
    print(f"Đã thay project cũ \"{name}\"")
    return True


def build(story_path, clips_dir, force, replace=False):
    story = load(story_path)
    clips_dir = clips_dir or os.path.join(os.path.dirname(os.path.abspath(story_path)), "1-canh")
    if capcut_running() and not force:
        sys.exit("CapCut đang mở. Tắt CapCut rồi chạy lại (CapCut ghi đè danh sách project khi thoát).")

    (base_name, base, _), trans_t = find_templates()
    print(f"Mẫu video+chữ: {os.path.basename(base_name)}" + (f" | mẫu chuyển cảnh: {os.path.basename(trans_t[0])}" if trans_t else " | không có mẫu chuyển cảnh"))

    vtrack = next(t for t in base["tracks"] if t["type"] == "video" and t["segments"])
    ttrack = next(t for t in base["tracks"] if t["type"] == "text" and t["segments"])
    vseg_t, tseg_t = vtrack["segments"][0], ttrack["segments"][0]

    doc = copy.deepcopy(base)
    for k, v in doc["materials"].items():
        if isinstance(v, list):
            doc["materials"][k] = []
    cl = Cloner(base, doc["materials"])
    tcl = Cloner(trans_t[1], doc["materials"]) if trans_t else None
    trans_src = trans_t[1]["materials"]["transitions"][0] if trans_t else None

    plan_path = os.path.join(os.path.dirname(os.path.abspath(story_path)), "edit_plan.json")
    plan = load(plan_path) if os.path.isfile(plan_path) else {}
    scenes = [sc for sc in story["scenes"] if not plan.get(str(sc["id"]), {}).get("drop")]
    dropped = len(story["scenes"]) - len(scenes)
    size = story.get("subtitle_size", 5)

    def add_text(text, start_us, dur_us, y):
        ts, tmat, _ = cl.segment(tseg_t)
        set_text(tmat, text, size)
        ts["target_timerange"] = {"start": start_us, "duration": dur_us}
        ts["clip"]["transform"] = {"x": 0.0, "y": y}
        ts["clip"]["scale"] = {"x": 1.0, "y": 1.0}
        tsegs.append(ts)

    vsegs, tsegs, meta_mats = [], [], []
    t = 0
    first_size = None
    for i, sc in enumerate(scenes):
        path = os.path.abspath(os.path.join(clips_dir, sc["clip"]))
        if not os.path.isfile(path):
            sys.exit(f"Thiếu clip cảnh {sc.get('id', i + 1)}: {path}")
        info = probe(path)
        first_size = first_size or (info["w"], info["h"])
        fpath = path.replace("\\", "/")
        p = plan.get(str(sc["id"]), {})
        cut_a = int(p.get("trim_start", 0) * 1e6)
        cut_b = int(p.get("trim_end", 0) * 1e6)
        if sc.get("keep"):  # [giây bắt đầu, giây kết thúc] lấy từ clip → nhịp cắt nhanh như video mẫu
            ka, kb = sc["keep"]
            cut_a = max(cut_a, int(ka * 1e6))
            cut_b = max(cut_b, info["us"] - int(kb * 1e6))
        dur = info["us"] - cut_a - cut_b

        seg, mat, _ = cl.segment(vseg_t)
        mat.update({"path": fpath, "duration": info["us"], "width": info["w"], "height": info["h"],
                    "material_name": os.path.basename(path), "has_audio": info["audio"],
                    "local_material_id": new_id().lower()})
        seg["source_timerange"] = {"start": cut_a, "duration": dur}
        seg["target_timerange"] = {"start": t, "duration": dur}
        seg["clip"]["scale"] = {"x": 1.0, "y": 1.0}
        seg["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        seg["render_index"] = 0
        nxt = scenes[i + 1] if i < len(scenes) - 1 else None
        # cảnh sau nối liền khung hình → cắt thẳng, không chuyển cảnh
        if tcl and story.get("transition", True) and nxt and not nxt.get("continue_from_previous"):
            tr = tcl.material(trans_src["id"])
            seg["extra_material_refs"].append(tr["id"])
        vsegs.append(seg)

        lines = sc.get("lines") or []
        if story.get("caption_top") and (sc.get("subtitle") or "").strip():
            # chú thích kiểu TikTok ở PHÍA TRÊN suốt cảnh (công thức video mẫu), vietsub vẫn ở dưới
            add_text(sc["subtitle"].strip(), t, dur, 0.72)
        if lines:  # vietsub theo đúng lúc nhân vật nói
            for ln in lines:
                a = max(int(ln["start"] * 1e6) - cut_a, 0)
                b = min(int(ln["end"] * 1e6) - cut_a, dur)
                if b - a > 300_000 and ln["text"].strip():
                    add_text(ln["text"].strip(), t + a, b - a, -0.8)
        elif (sc.get("subtitle") or "").strip() and not story.get("caption_top"):  # không thoại → chú thích cốt truyện
            add_text(sc["subtitle"].strip(), t, dur, -0.8)

        meta_mats.append({"ai_group_type": "", "create_time": int(time.time()), "duration": info["us"],
                          "enter_from": 0, "extra_info": os.path.basename(path), "file_Path": fpath,
                          "height": info["h"], "id": str(uuid.uuid4()), "import_time": int(time.time()),
                          "import_time_ms": int(time.time() * 1e6), "item_source": 1, "md5": "",
                          "metetype": "video", "roughcut_time_range": {"duration": info["us"], "start": 0},
                          "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": info["w"]})
        t += dur

    timeline_id = new_id()
    vt = copy.deepcopy(vtrack); vt["id"] = new_id(); vt["segments"] = vsegs
    doc["tracks"] = [vt]
    if tsegs:
        tt = copy.deepcopy(ttrack); tt["id"] = new_id(); tt["segments"] = tsegs
        doc["tracks"].append(tt)
    doc["id"] = timeline_id
    doc["duration"] = t
    doc["name"] = ""
    w, h = story.get("canvas", first_size)
    doc["canvas_config"] = {"ratio": "original", "width": w, "height": h, "background": None}
    doc["keyframes"] = {k: [] for k in doc.get("keyframes", {})}
    doc["relationships"] = []
    doc["time_marks"] = None

    # --- tạo thư mục project ---
    title = story.get("title") or datetime.datetime.now().strftime("%m%d")
    if replace:
        remove_old(title)
    name, n = title, 1
    while os.path.exists(os.path.join(ROOT, name)):
        name = f"{title} ({n})"; n += 1
    os.makedirs(ROOT, exist_ok=True)
    dst = os.path.join(ROOT, name)
    src = base_name  # đường dẫn đầy đủ tới project mẫu
    project = load(os.path.join(src, "Timelines", "project.json"))
    main_tl = project["main_timeline_id"]

    def ignore(d, files):
        skip = [f for f in files if f in SKIP_FILES or f == MARKER]
        if os.path.basename(d) == "Timelines":
            skip += [f for f in files if os.path.isdir(os.path.join(d, f)) and f != main_tl]
        return skip

    shutil.copytree(src, dst, ignore=ignore)
    open(os.path.join(dst, MARKER), "w").close()
    tl_dir = os.path.join(dst, "Timelines", timeline_id)
    os.rename(os.path.join(dst, "Timelines", main_tl), tl_dir)
    for f in ("template.tmp", "template-2.tmp", "draft_content.json.bak"):
        p = os.path.join(tl_dir, f)
        if os.path.exists(p):
            os.remove(p)
    dump(doc, os.path.join(dst, "draft_content.json"))
    dump(doc, os.path.join(tl_dir, "draft_content.json"))

    now_us = int(time.time() * 1e6)
    project.update({"id": new_id(), "main_timeline_id": timeline_id, "create_time": now_us, "update_time": now_us,
                    "timelines": [{"create_time": now_us, "id": timeline_id, "is_marked_delete": False,
                                   "name": "Dòng thời gian 01", "update_time": now_us}]})
    dump(project, os.path.join(dst, "Timelines", "project.json"))
    dump({"dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [timeline_id],
                         "timelineNames": ["Dòng thời gian 01"]}], "layoutOrientation": 1},
         os.path.join(dst, "timeline_layout.json"))

    # ảnh bìa = khung hình đầu của cảnh 1
    ff = shutil.which("ffmpeg")
    first_clip = os.path.abspath(os.path.join(clips_dir, scenes[0]["clip"]))
    for cover in (os.path.join(dst, "draft_cover.jpg"), os.path.join(tl_dir, "draft_cover.jpg")):
        if ff:
            subprocess.run([ff, "-y", "-v", "error", "-ss", "1", "-i", first_clip, "-frames:v", "1", cover])

    meta = load(os.path.join(dst, "draft_meta_info.json"))
    draft_id = new_id()
    fold = f"{ROOT_FWD}/{name}"
    meta.update({"draft_id": draft_id, "draft_name": name, "draft_fold_path": fold,
                 "draft_root_path": ROOT, "tm_duration": t, "tm_draft_create": now_us,
                 "tm_draft_modified": now_us, "draft_timeline_materials_size_": 0,
                 "draft_segment_extra_info": [], "draft_materials_copied_info": []})
    meta["draft_materials"] = [{"type": 0, "value": meta_mats}] + [
        {"type": k, "value": []} for k in (1, 2, 3, 6, 7, 8)]
    dump(meta, os.path.join(dst, "draft_meta_info.json"))

    # đăng ký vào danh sách project của CapCut
    rpath = os.path.join(ROOT, "root_meta_info.json")
    if os.path.isfile(rpath):
        shutil.copy2(rpath, rpath + ".before_skill.bak")
        root = load(rpath)
    else:  # CapCut mới cài, chưa có danh sách project
        root = {"all_draft_store": [], "draft_ids": 0, "root_path": ROOT_FWD}
    store = root["all_draft_store"]
    tmpl = next((e for e in store if e.get("draft_fold_path", "").endswith("/" + os.path.basename(base_name))), store[0] if store else {})
    e = copy.deepcopy(tmpl)
    e.update({"draft_id": draft_id, "draft_name": name, "draft_fold_path": fold,
              "draft_cover": f"{fold}\\draft_cover.jpg", "draft_json_file": f"{fold}\\draft_content.json",
              "tm_duration": t, "tm_draft_create": now_us, "tm_draft_modified": now_us,
              "draft_timeline_materials_size": 0})
    store.insert(0, e)
    if isinstance(root.get("draft_ids"), int):
        root["draft_ids"] += 1
    dump(root, rpath)

    print(f"Xong: project CapCut \"{name}\" — {len(scenes)} cảnh" + (f" (bỏ {dropped} cảnh trùng)" if dropped else "")
          + f", {t / 1e6:.1f}s, {len(tsegs)} dòng chữ.")
    print(f"Thư mục: {dst}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--clips-dir")
    ap.add_argument("--replace", action="store_true", help="thay project cũ cùng tên (chỉ project do skill tạo)")
    ap.add_argument("--force", action="store_true", help="chạy cả khi CapCut đang mở (không khuyên dùng)")
    a = ap.parse_args()
    build(a.storyboard, a.clips_dir, a.force, a.replace)
