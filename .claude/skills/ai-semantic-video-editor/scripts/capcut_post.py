"""CapCut post-production project: FFmpeg-made base + CapCut for transitions / SFX / effects.

Run after `story_render.py <sb> --capcut-layers` (cut scenes + transparent text layer). CapCut must be closed.

  python capcut_post.py projects/<slug>/storyboard.json [--title "..."]

Builds a CapCut draft (only drafts marked by the skill are ever replaced):
  - video track: the cut scenes (segments/seg_*.mp4), clip sound off
  - transitions ONLY where a scene has "transition_in": "<CapCut transition name>" (others = straight cut);
    the transition material is copied from one of your existing CapCut projects that already used it
  - overlay track: text_layer.mov (word-by-word subtitles, kinetic text, caption)
  - audio track: the narration voice
  - narration/sfx_cues.md + .json: when to add which sound effect in CapCut (from scene "sfx", times converted
    to the timeline), to be added through the CapCut UI (references/capcut-post.md)
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAO = HERE.parent.parent / "tao-video"
sys.path.insert(0, str(TAO / "scripts"))
sys.path.insert(0, str(HERE))
import build_capcut_draft as B  # noqa: E402  (tao-video, not modified)
from vse_common import probe_duration  # noqa: E402

US = 1_000_000


def find_transition(name: str):
    """Transition material with this name from any CapCut draft (yours or the skill templates)."""
    pats = [os.path.join(B.ROOT, "*", "draft_content.json"), str(TAO / "assets" / "capcut_templates" / "*" / "draft_content.json")]
    for pat in pats:
        for f in glob.glob(pat):
            try:
                d = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            for m in d.get("materials", {}).get("transitions", []) or []:
                if (m.get("name") or "").strip().lower() == name.strip().lower():
                    return m
    return None


def tc(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}:{s:05.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--title")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = json.loads(sp.read_text(encoding="utf-8"))
    final = proj / "narration" / "build" / "final"
    layers = json.loads((final / "capcut_layers.json").read_text(encoding="utf-8"))
    tl = json.loads((proj / "narration" / "timeline.json").read_text(encoding="utf-8"))
    voice = proj / "narration" / tl["project"]["voice_audio"]
    segs = [Path(p) for p in layers["segments"]]
    scene_layers = sorted([L for L in tl["layers"] if L["type"] == "scene"], key=lambda L: L["start"])
    if len(segs) != len(scene_layers):
        sys.exit("Số cảnh đã cắt khác timeline. Chạy lại story_render.py --capcut-layers.")
    if B.capcut_running() and not a.force:
        sys.exit("CapCut đang mở. Tắt CapCut rồi chạy lại.")

    title = a.title or f"{story.get('title', proj.name)} (hau ky)"
    tmp_sb = final / "_capcut_post_storyboard.json"
    tmp_sb.write_text(json.dumps({"title": title, "canvas": story.get("canvas", [1080, 1920]), "transition": False,
                                  "scenes": [{"id": i + 1, "clip": s.name} for i, s in enumerate(segs)]},
                                 ensure_ascii=False), encoding="utf-8")
    B.build(str(tmp_sb), str(segs[0].parent), a.force, True)
    draft = Path(B.ROOT) / title
    doc = B.load(draft / "draft_content.json")

    vtrack = next(t for t in doc["tracks"] if t["type"] == "video" and t["segments"])
    vsegs = vtrack["segments"]
    for sg in vsegs:
        sg["volume"] = 0.0

    # ----- transitions only where asked -----
    scenes_by_id = {sc["id"]: sc for sc in story["scenes"]}
    sid_of = lambda a: (int(a) if a.isdigit() else a)  # mã cảnh có thể là "5b", "8b"…
    ids = [sid_of(L["asset_id"][1:]) if L["asset_id"].startswith("c") else None for L in scene_layers]
    scenes_by_id.update({str(k): v for k, v in list(scenes_by_id.items())})
    scenes_by_id.update({int(k): v for k, v in list(scenes_by_id.items()) if str(k).isdigit()})
    report = []
    for k in range(1, len(vsegs)):
        sc = (scenes_by_id.get(ids[k]) or scenes_by_id.get(str(ids[k]))) if ids[k] else None
        name = (sc or {}).get("transition_in")
        if not name:
            continue
        m = find_transition(name)
        if not m:
            report.append(f"  ! Không có chuyển cảnh '{name}' trong project nào của anh — cảnh {ids[k]} cắt thẳng")
            continue
        c = copy.deepcopy(m)
        c["id"] = B.new_id()
        doc["materials"].setdefault("transitions", []).append(c)
        vsegs[k - 1].setdefault("extra_material_refs", []).append(c["id"])
        report.append(f"  Chuyển cảnh '{name}' trước cảnh {ids[k]}")

    total = doc["duration"]

    # ----- text layer overlay track -----
    vcl = B.Cloner(copy.deepcopy(doc), doc["materials"])
    gseg, gmat, _ = vcl.segment(vsegs[0])
    lay = Path(layers["text_layer"])
    lus = int(probe_duration(lay) * US)
    W, H = doc["canvas_config"]["width"], doc["canvas_config"]["height"]
    gmat.update({"path": str(lay).replace("\\", "/"), "duration": lus, "width": W, "height": H,
                 "material_name": lay.name, "has_audio": False, "local_material_id": B.new_id().lower()})
    d = min(lus, total)
    gseg.update({"source_timerange": {"start": 0, "duration": d}, "target_timerange": {"start": 0, "duration": d},
                 "speed": 1.0, "volume": 0.0, "render_index": 11000})
    gseg["clip"]["scale"] = {"x": 1.0, "y": 1.0}
    gseg["clip"]["transform"] = {"x": 0.0, "y": 0.0}
    gtrack = copy.deepcopy(vtrack)
    gtrack["id"] = B.new_id()
    gtrack["segments"] = [gseg]

    # ----- voice track (local mp3 clip from the 0724 template) -----
    atpl = B.load(TAO / "assets" / "capcut_templates" / "0724" / "draft_content.json")
    atrack_t = next(t for t in atpl["tracks"] if t["type"] == "audio" and t["segments"])
    aseg, amat, aextra = B.Cloner(atpl, doc["materials"]).segment(atrack_t["segments"][0])
    vdur = int(probe_duration(voice) * US)
    amat.update({"path": str(voice).replace("\\", "/"), "duration": vdur, "name": voice.name, "type": "extract_music",
                 "category_name": "local", "music_id": B.new_id().lower(), "local_material_id": B.new_id().lower(),
                 "wave_points": []})
    aseg.update({"source_timerange": {"start": 0, "duration": min(vdur, total)},
                 "target_timerange": {"start": 0, "duration": min(vdur, total)}, "speed": 1.0, "volume": 1.0})
    if "speeds" in aextra:
        aextra["speeds"]["speed"] = 1.0
    atrack = copy.deepcopy(atrack_t)
    atrack["id"] = B.new_id()
    atrack["segments"] = [aseg]

    doc["tracks"] = [vtrack, gtrack, atrack]
    B.dump(doc, draft / "draft_content.json")
    tl_file = draft / "Timelines" / doc["id"] / "draft_content.json"
    if tl_file.parent.exists():
        B.dump(doc, tl_file)

    # ----- SFX / effect cue sheet -----
    cues = []
    for L in scene_layers:
        sid = sid_of(L["asset_id"][1:])
        sc = scenes_by_id[sid]
        s0, sp_ = float(L.get("source_start", 0)), float(L.get("speed", 1.0))
        for kind in ("sfx", "effect", "highlight"):
            items = sc.get(kind) or []
            items = [items] if isinstance(items, dict) else items
            for it in items:
                # start: "at" = timeline second measured on the rendered video (sfx_frames.py), or "at_clip" = clip second
                if "at" in it:
                    t = float(it["at"])
                elif "at_clip" in it:
                    t = L["start"] + (float(it["at_clip"]) - s0) / sp_
                else:
                    report.append(f"  ! {kind} cảnh {sid} '{it.get('sound') or it.get('what', '')}' thiếu mốc 'at' / 'at_clip' — bỏ qua")
                    continue
                if not (L["start"] - 0.05 <= t <= L["end"] + 0.05):
                    report.append(f"  ! {kind} cảnh {sid} ở giây {t:.2f} nằm ngoài cảnh ({L['start']:.2f}–{L['end']:.2f}) — bỏ qua")
                    continue
                # end: the sound must stop when the action stops
                e = None
                if "end" in it:
                    e = float(it["end"])
                elif "end_clip" in it:
                    e = L["start"] + (float(it["end_clip"]) - s0) / sp_
                if kind == "sfx":
                    if e is None:
                        report.append(f"  ! SFX cảnh {sid} '{it.get('sound', '')}' thiếu mốc KẾT THÚC ('end'/'end_clip') — "
                                      "tiếng sẽ kêu lố sau hành động; soi khung bằng sfx_frames.py rồi ghi thêm")
                    elif e > L["end"] + 0.05 and not it.get("cross_scene"):
                        report.append(f"  ! SFX cảnh {sid} '{it.get('sound', '')}' kết thúc {e:.2f}s lố sang cảnh sau — cắt về {L['end']:.2f}s")
                        e = L["end"]
                cues.append({"kind": kind, "scene": sid, "time": round(t, 2), "timecode": tc(t),
                             **({"end": round(e, 2), "end_tc": tc(e)} if e is not None else {}),
                             **{k: v for k, v in it.items() if k not in ("at_clip", "at", "end", "end_clip")}})
    # emphasis text left to CapCut (storyboard "emphasis_text": "capcut"): one cue per kinetic_text graphic
    if story.get("emphasis_text") == "capcut":
        sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
        for s in sync["scenes"]:
            g = s.get("graphic")
            if g and g.get("template") == "kinetic_text":
                lines = (g.get("data") or {}).get("lines", [])
                cues.append({"kind": "text", "scene": s["id"], "time": round(g["start"], 2), "timecode": tc(g["start"]),
                             "name": " / ".join(lines), "search": "mẫu chữ / hiệu ứng chữ (Pro) hợp cảm xúc",
                             "volume": "", "why": f"chữ nhấn mạnh {g['end'] - g['start']:.1f}s, đặt ở giữa khung"})
    for c in tl.get("capcut_text") or []:
        cues.append({"kind": "text", "scene": "", "time": c["start"], "timecode": tc(c["start"]),
                     "name": f"SUB: {c['text']}  ({c['end'] - c['start']:.1f}s, đến {tc(c['end'])})",
                     "search": c.get("style") or "hiệu ứng chữ hợp nội dung", "volume": "",
                     "why": c.get("why", "")})
    cues.sort(key=lambda c: c["time"])
    (proj / "narration" / "sfx_cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# Âm thanh / hiệu ứng thêm trong CapCut", "", f"Project: **{title}** · {total / US:.2f}s", "",
          "| Bắt đầu | Kết thúc | Cảnh | Loại | Âm thanh / hiệu ứng | Từ khóa tìm | Âm lượng | Vì sao |", "|---|---|---|---|---|---|---|---|"]
    for c in cues:
        md.append(f"| {c['timecode']} | {c.get('end_tc', '')} | {c['scene']} | {c['kind']} | {c.get('sound') or c.get('name') or c.get('what', '')} | "
                  f"{c.get('search') or c.get('effect', '')} | {c.get('volume', '')} | {c.get('why', '')} |")
    (proj / "narration" / "sfx_cues.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Project CapCut hậu kỳ: \"{title}\" — {len(vsegs)} cảnh, {total / US:.2f}s, lớp chữ + giọng kể")
    print("\n".join(report) if report else "  (không có chuyển cảnh nào — cắt thẳng toàn bộ)")
    print(f"  {len(cues)} gợi ý SFX/hiệu ứng → {proj / 'narration' / 'sfx_cues.md'}")


if __name__ == "__main__":
    main()
