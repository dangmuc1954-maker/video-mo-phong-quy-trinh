"""Add the ElevenLabs narration to a CapCut draft built by tao-video (run AFTER build_capcut_draft.py).

What it does to the draft (only drafts created by the skill, i.e. with the marker file):
  - each scene lasts exactly as long as its narration slot (narration/sync.json); a clip that is too
    short is slowed down (down to --min-speed), a longer clip is sped up (up to --max-speed) so the whole
    action in "beats" stays, then trimmed; scene "keep": [a, b] picks the window, "fit": "trim" disables speed-up
  - adds the voice as an audio track, turns clip sound down (--clip-volume)
  - replaces the text track with subtitles timed to the spoken words (+ top caption if caption_top)
  - adds motion graphics (scene.graphic) as transparent full-frame .mov on an overlay track

Usage:
  python capcut_narration.py projects/<slug>/storyboard.json [--clip-volume 0.15] [--min-speed 0.5] [--no-graphics]
  python capcut_narration.py ... --draft-dir "<path to draft folder>"   # work on a specific folder (eg. a copy)
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TAO = HERE.parent.parent / "tao-video"
if not (TAO / "scripts" / "build_capcut_draft.py").exists():
    sys.exit(f"Không thấy skill tao-video ở {TAO}. Script này dùng trong dự án có skill tao-video.")
sys.path.insert(0, str(TAO / "scripts"))
import build_capcut_draft as B  # noqa: E402  (tao-video, not modified)
from mograph import render_mograph  # noqa: E402
from render import anchor_xy  # noqa: E402
from vse_common import probe_duration  # noqa: E402

US = 1_000_000


def find_draft(title: str) -> Path:
    cands = [Path(B.ROOT) / title] + sorted(Path(B.ROOT).glob(f"{title} (*)"), key=lambda p: p.stat().st_mtime)
    cands = [p for p in cands if (p / B.MARKER).exists()]
    if not cands:
        sys.exit(f"Không thấy project CapCut \"{title}\" do skill tạo. Chạy build_capcut_draft.py trước.")
    return max(cands, key=lambda p: p.stat().st_mtime)


def full_frame_graphic(card: Path, info: dict, x: int, y: int, W: int, H: int, fps: int, dur: float, out: Path):
    B_ff = B.shutil.which("ffmpeg")
    cmd = [B_ff, "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={fps}:d={dur:.3f},format=rgba",
           "-i", str(card), "-filter_complex", f"[0][1]overlay={x}:{y}:eof_action=pass,format=yuva444p10le",
           "-t", f"{dur:.3f}", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-vendor", "apl0", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Lỗi tạo graphic {out.name}: {r.stderr[-800:]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--draft-dir")
    ap.add_argument("--clip-volume", type=float, default=0.15)
    ap.add_argument("--min-speed", type=float, default=0.5)
    ap.add_argument("--max-speed", type=float, default=1.6,
                    help="clip dài hơn lời kể: tăng tốc tới mức này để giữ trọn hành động (scene \"fit\": \"trim\" để chỉ cắt)")
    ap.add_argument("--no-graphics", action="store_true")
    ap.add_argument("--force", action="store_true", help="chạy cả khi CapCut đang mở (không khuyên dùng)")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = B.load(sp)
    sync_path = proj / "narration" / "sync.json"
    if not sync_path.exists():
        sys.exit("Chưa có narration/sync.json. Chạy story_voice.py trước.")
    sync = B.load(sync_path)
    voice = proj / "narration" / sync["voice"]
    plan = B.load(proj / "edit_plan.json") if (proj / "edit_plan.json").exists() else {}

    if a.draft_dir:
        draft = Path(a.draft_dir).resolve()
    else:
        if B.capcut_running() and not a.force:
            sys.exit("CapCut đang mở. Tắt CapCut rồi chạy lại (CapCut ghi đè project khi thoát).")
        draft = find_draft(story.get("title"))
    if not (draft / B.MARKER).exists():
        sys.exit(f"{draft} không phải project do skill tạo, không sửa.")
    doc = B.load(draft / "draft_content.json")
    W, H = doc["canvas_config"]["width"], doc["canvas_config"]["height"]
    fps = int(round(doc.get("fps", 30) or 30))

    # ----- scene slots (dropped scenes give their time to the previous kept scene) -----
    slot = {s["id"]: s for s in sync["scenes"]}
    kept = [sc for sc in story["scenes"] if not plan.get(str(sc["id"]), {}).get("drop")]
    if not kept:
        sys.exit("Không còn cảnh nào.")
    order = [sc["id"] for sc in story["scenes"]]
    spans = {}
    for sc in story["scenes"]:
        s = slot.get(sc["id"])
        if not s:
            sys.exit(f"Cảnh {sc['id']} không có trong sync.json. Chạy lại story_voice.py.")
        target = sc["id"] if sc in kept else next((k["id"] for k in reversed(kept) if order.index(k["id"]) < order.index(sc["id"])), kept[0]["id"])
        lo, hi = spans.get(target, (s["slot"][0], s["slot"][1]))
        spans[target] = (min(lo, s["slot"][0]), max(hi, s["slot"][1]))

    vtrack = next(t for t in doc["tracks"] if t["type"] == "video" and t["segments"])
    vsegs = vtrack["segments"]
    if len(vsegs) != len(kept):
        sys.exit(f"Project có {len(vsegs)} đoạn video nhưng có {len(kept)} cảnh giữ lại. Dựng lại bằng build_capcut_draft.py --replace.")
    mats = {m["id"]: (k, m) for k, lst in doc["materials"].items() if isinstance(lst, list)
            for m in lst if isinstance(m, dict) and "id" in m}
    report = []
    t = 0
    for sc, seg in zip(kept, vsegs):
        lo, hi = spans[sc["id"]]
        D = int(round((hi - lo) * US))
        vm = mats[seg["material_id"]][1]
        p = plan.get(str(sc["id"]), {})
        src0 = seg["source_timerange"]["start"]
        avail = vm["duration"] - src0 - int(p.get("trim_end", 0) * US)
        if sc.get("keep"):
            avail = int(sc["keep"][1] * US) - src0
        speed = 1.0
        if avail > D and sc.get("fit") != "trim":
            speed = min(a.max_speed, avail / D)   # keep the whole action arc written in beats
        if avail < D:
            speed = max(a.min_speed, avail / D)
            if speed == a.min_speed and avail / D < a.min_speed:
                print(f"CẢNH BÁO: cảnh {sc['id']} clip quá ngắn so với lời kể ({avail / US:.1f}s cho {D / US:.1f}s), "
                      f"đã làm chậm tối đa {a.min_speed}x; nên tạo thêm cảnh hoặc rút gọn lời kể.")
                src0 = max(0, vm["duration"] - int(D * speed))
        src_d = int(D * speed)
        seg["source_timerange"] = {"start": src0, "duration": src_d}
        seg["target_timerange"] = {"start": t, "duration": D}
        seg["speed"] = speed
        seg["volume"] = a.clip_volume
        for r in seg.get("extra_material_refs", []):
            if r in mats and mats[r][0] == "speeds":
                mats[r][1]["speed"] = speed
        report.append(f"  Cảnh {sc['id']}: {D / US:5.2f}s, tốc độ clip {speed:.2f}x")
        t += D
    total = t

    # ----- subtitles -----
    ttrack = next((tr for tr in doc["tracks"] if tr["type"] == "text" and tr["segments"]), None)
    tsrc_doc = doc
    if ttrack is None:  # draft had no text: borrow the text segment from the skill's 1104 template
        tsrc_doc = B.load(TAO / "assets" / "capcut_templates" / "1104" / "draft_content.json")
        ttrack = next(tr for tr in tsrc_doc["tracks"] if tr["type"] == "text")
    tseg_t = copy.deepcopy(ttrack["segments"][0])
    old_text = {s["material_id"] for s in ttrack["segments"]} | {r for s in ttrack["segments"] for r in s.get("extra_material_refs", [])}
    cl = B.Cloner(copy.deepcopy(tsrc_doc), doc["materials"])
    size = story.get("subtitle_size", 5)
    tsegs = []

    def add_text(text, s, e, y):
        ts, tm, _ = cl.segment(tseg_t)
        B.set_text(tm, text, size)
        ts["target_timerange"] = {"start": int(s * US), "duration": int((e - s) * US)}
        ts["clip"]["transform"] = {"x": 0.0, "y": y}
        ts["clip"]["scale"] = {"x": 1.0, "y": 1.0}
        tsegs.append(ts)

    for sc in kept:
        lo, hi = spans[sc["id"]]
        if story.get("caption_top") and (sc.get("subtitle") or "").strip():
            add_text(sc["subtitle"].strip(), lo, hi, 0.72)
    for s in sync["scenes"]:
        for ln in s["lines"]:
            if ln["end"] - ln["start"] > 0.25:
                add_text(ln["text"], ln["start"], ln["end"], -0.8)
    if tsrc_doc is doc:
        for k, lst in doc["materials"].items():
            if isinstance(lst, list):
                doc["materials"][k] = [m for m in lst if not (isinstance(m, dict) and m.get("id") in old_text)]
    new_ttrack = copy.deepcopy(ttrack)
    new_ttrack["id"] = B.new_id()
    new_ttrack["segments"] = tsegs

    # ----- voice audio track (local mp3 clip from the 0724 template) -----
    atpl = B.load(TAO / "assets" / "capcut_templates" / "0724" / "draft_content.json")
    atrack_t = next(tr for tr in atpl["tracks"] if tr["type"] == "audio" and tr["segments"])
    acl = B.Cloner(atpl, doc["materials"])
    aseg, amat, aextra = acl.segment(atrack_t["segments"][0])
    vdur = int(probe_duration(voice) * US)
    amat.update({"path": str(voice).replace("\\", "/"), "duration": vdur, "name": voice.name,
                 "type": "extract_music", "category_name": "local", "music_id": B.new_id().lower(),
                 "local_material_id": B.new_id().lower(), "wave_points": []})
    aseg.update({"source_timerange": {"start": 0, "duration": min(vdur, total)},
                 "target_timerange": {"start": 0, "duration": min(vdur, total)},
                 "speed": 1.0, "volume": 1.0, "render_index": 0})
    if "speeds" in aextra:
        aextra["speeds"]["speed"] = 1.0
    atrack = copy.deepcopy(atrack_t)
    atrack["id"] = B.new_id()
    atrack["segments"] = [aseg]

    # ----- motion graphics overlay track -----
    gtrack = None
    gdir = proj / "narration" / "graphics"
    if not a.no_graphics and any(s.get("graphic") for s in sync["scenes"]):
        gdir.mkdir(parents=True, exist_ok=True)
        vcl = B.Cloner(copy.deepcopy(doc), doc["materials"])
        gsegs = []
        palette = story.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"]
        for i, s in enumerate([s for s in sync["scenes"] if s.get("graphic")]):
            g = s["graphic"]
            dur = g["end"] - g["start"]
            card = gdir / f"card_{s['id']}.mov"
            info = render_mograph({"template": g["template"], "data": g.get("data", {}), "duration": dur, "width": W,
                                   "height": H, "fps": fps, "palette": palette, "font": story.get("font", "Roboto"),
                                   "time_offset": g["start"]}, card)
            full = gdir / f"graphic_{s['id']}_{g['template']}.mov"
            if info["full_frame"]:
                card.replace(full)
            else:
                x, y = anchor_xy(g.get("anchor", "top"), info["width"], info["height"], W, H)
                full_frame_graphic(card, info, x, y, W, H, fps, dur, full)
                card.unlink()
            gseg, gmat, _ = vcl.segment(vsegs[0])
            gus = int(probe_duration(full) * US)
            gmat.update({"path": str(full).replace("\\", "/"), "duration": gus, "width": W, "height": H,
                         "material_name": full.name, "has_audio": False, "local_material_id": B.new_id().lower()})
            d = min(gus, int(dur * US))
            gseg.update({"source_timerange": {"start": 0, "duration": d},
                         "target_timerange": {"start": int(g["start"] * US), "duration": d},
                         "speed": 1.0, "volume": 0.0, "render_index": 11000 + i})
            gseg["clip"]["scale"] = {"x": 1.0, "y": 1.0}
            gseg["clip"]["transform"] = {"x": 0.0, "y": 0.0}
            gseg["extra_material_refs"] = [r for r in gseg["extra_material_refs"]
                                           if doc_mat_kind(doc, r) != "transitions"]
            for r in gseg["extra_material_refs"]:
                m = doc_mat(doc, r)
                if m and m.get("type") == "speed":
                    m["speed"] = 1.0
            gsegs.append(gseg)
            report.append(f"  Graphic cảnh {s['id']}: {g['template']} {g['start']:.2f}–{g['end']:.2f}s")
        gtrack = copy.deepcopy(vtrack)
        gtrack["id"] = B.new_id()
        gtrack["segments"] = gsegs

    doc["tracks"] = [vtrack] + ([gtrack] if gtrack else []) + ([new_ttrack] if tsegs else []) + [atrack]
    doc["duration"] = total

    tl_id = doc["id"]
    B.dump(doc, draft / "draft_content.json")
    tl_file = draft / "Timelines" / tl_id / "draft_content.json"
    if tl_file.parent.exists():
        B.dump(doc, tl_file)
    meta_p = draft / "draft_meta_info.json"
    if meta_p.exists():
        meta = B.load(meta_p)
        meta["tm_duration"] = total
        B.dump(meta, meta_p)
    rpath = Path(B.ROOT) / "root_meta_info.json"
    if not a.draft_dir and rpath.exists():
        root = B.load(rpath)
        for e in root.get("all_draft_store", []):
            if e.get("draft_fold_path", "").endswith("/" + draft.name):
                e["tm_duration"] = total
        B.dump(root, rpath)
    print(f"Đã gắn giọng kể vào project \"{draft.name}\": {total / US:.2f}s, {len(tsegs)} dòng chữ")
    print("\n".join(report))
    print("Tiếp theo: polish_draft.py để làm đẹp chữ, rồi mở CapCut xuất video như thường.")


def doc_mat(doc, mid):
    for lst in doc["materials"].values():
        if isinstance(lst, list):
            for m in lst:
                if isinstance(m, dict) and m.get("id") == mid:
                    return m
    return None


def doc_mat_kind(doc, mid):
    for k, lst in doc["materials"].items():
        if isinstance(lst, list) and any(isinstance(m, dict) and m.get("id") == mid for m in lst):
            return k
    return None


if __name__ == "__main__":
    main()
