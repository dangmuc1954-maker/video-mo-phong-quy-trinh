"""Render a tao-video storyboard + ElevenLabs narration straight to MP4 with FFmpeg (no CapCut needed).

Uses 1-canh/ clips, edit_plan.json trims and narration/sync.json. Each clip is trimmed or slowed down
to fill its narration slot; subtitles follow the spoken words; scene.graphic becomes a motion graphic.

Usage:
  python story_render.py projects/<slug>/storyboard.json [--preview] [--preset keyword] [--min-speed 0.5]
Output: projects/<slug>/2-xuat/<title> (giong ke).mp4  (or narration/build/preview.mp4 with --preview)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from vse_common import load_words, probe_duration  # noqa: E402


XFADE = {"fade", "fadeblack", "fadewhite", "dissolve", "smoothleft", "smoothright", "smoothup", "smoothdown",
         "circleopen", "circleclose", "radial", "wipeleft", "wiperight", "slideleft", "slideright", "zoomin",
         "distance", "fadegrays", "hblur", "pixelize"}


def xfade_of(sc: dict, i: int) -> dict:
    """Scene transition for the FFmpeg render. scene["transition_in"] may be an FFmpeg xfade name (fade, dissolve,
    smoothleft…) or a CapCut name (used by capcut_post.py) — a CapCut name is rendered here as a gentle "fade"."""
    t = (sc.get("transition_in") or "").strip()
    if i == 0 or not t:
        return {}
    name = t if t in XFADE else "fade"
    return {"xfade": name, "xfade_dur": float(sc.get("transition_dur", 0.5))}


def capcut_text_spans(story: dict, words: list[dict]) -> list[dict]:
    """Subtitle phrases handed to CapCut for special text effects (shouting, key selling points…).
    storyboard["capcut_text"] (or scene["capcut_text"]) = [{"cue": "chỉ còn 99k", "style": "...", "why": "..."}]"""
    from vse_common import normalize_token
    items = list(story.get("capcut_text") or [])
    for sc in story.get("scenes", []):
        items += sc.get("capcut_text") or []
    norm = [normalize_token(w["text"]) for w in words]
    out = []
    for it in items:
        k = [normalize_token(x) for x in it["cue"].split() if normalize_token(x)]
        hit = next((i for i in range(len(norm) - len(k) + 1) if k and norm[i:i + len(k)] == k), None)
        if hit is None:
            print(f"CẢNH BÁO: không thấy câu '{it['cue']}' trong lời đọc — bỏ qua hiệu ứng chữ CapCut cho câu này")
            continue
        j = hit + len(k) - 1
        end = words[j]["end"] + 0.35
        if j + 1 < len(words):
            end = min(end, max(words[j]["end"], words[j + 1]["start"]))
        out.append({"start": round(max(0.0, words[hit]["start"] - 0.05), 3), "end": round(end, 3),
                    "text": " ".join(w["text"] for w in words[hit:j + 1]),
                    "style": it.get("style", ""), "why": it.get("why", "")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--preset", help="clean|box|karaoke|pop_word|keyword|cinematic|story_pop (mặc định: storyboard.subtitle_preset hoặc story_pop)")
    ap.add_argument("--min-speed", type=float, default=0.5)
    ap.add_argument("--max-speed", type=float, default=1.6)
    ap.add_argument("--bgm")
    ap.add_argument("--capcut-layers", action="store_true", help="chỉ xuất cảnh đã cắt + lớp chữ trong suốt cho hậu kỳ CapCut")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    ndir = proj / "narration"
    story = json.loads(sp.read_text(encoding="utf-8"))
    sync = json.loads((ndir / "sync.json").read_text(encoding="utf-8"))
    plan = json.loads((proj / "edit_plan.json").read_text(encoding="utf-8")) if (proj / "edit_plan.json").exists() else {}
    W, H = story.get("canvas", [1080, 1920])
    words = load_words(ndir / "words.json")
    dur = sync["duration"]
    slot = {s["id"]: s for s in sync["scenes"]}

    kept = [sc for sc in story["scenes"] if not plan.get(str(sc["id"]), {}).get("drop")]
    spans = {}
    for sc in story["scenes"]:
        s = slot[sc["id"]]["slot"]
        tgt = sc["id"] if sc in kept else max((k for k in kept if story["scenes"].index(k) < story["scenes"].index(sc)),
                                              key=story["scenes"].index, default=kept[0])["id"]
        lo, hi = spans.get(tgt, tuple(s))
        spans[tgt] = (min(lo, s[0]), max(hi, s[1]))

    assets, layers, beats = [], [], []
    for i, sc in enumerate(kept):
        lo, hi = spans[sc["id"]]
        clip = proj / "1-canh" / sc["clip"]
        if not clip.exists():
            sys.exit(f"Thiếu clip cảnh {sc['id']}: {clip}")
        p = plan.get(str(sc["id"]), {})
        s0 = float(p.get("trim_start", 0))
        end_avail = probe_duration(clip) - float(p.get("trim_end", 0))
        if sc.get("keep"):
            s0, end_avail = max(s0, sc["keep"][0]), sc["keep"][1]
        avail, need = end_avail - s0, hi - lo
        if avail >= need:
            speed = 1.0 if sc.get("fit") == "trim" else min(a.max_speed, avail / need)
        else:
            speed = max(a.min_speed, avail / need)
        if avail / need < a.min_speed:
            print(f"CẢNH BÁO: cảnh {sc['id']} clip ngắn ({avail:.1f}s cho {need:.1f}s lời kể), làm chậm {a.min_speed}x và giữ khung cuối.")
        aid = f"c{sc['id']}"
        assets.append({"id": aid, "kind": "video", "file": f"../1-canh/{sc['clip']}", "prompt": sc.get("prompt"),
                       "license": "AI-generated (tool/Muse)", "status": "ready"})
        bid = f"b{sc['id']}"
        layers.append({"id": f"L{sc['id']}", "type": "scene", "start": round(lo, 3), "end": round(hi, 3), "asset_id": aid,
                       "motion": "static", "beat_id": bid, "source_start": round(s0, 3), "speed": round(speed, 4),
                       **xfade_of(sc, i)})
        beats.append({"id": bid, "start": round(lo, 3), "end": round(hi, 3), "spoken_text": sc.get("narration") or sc.get("dialogue", ""),
                      "meaning": sc.get("action", ""), "visual_type": "scene", "rationale": "cảnh tạo theo storyboard",
                      "asset_ids": [aid], "visual_cue_word_ids": [], "keywords": sc.get("keywords", [])})
        print(f"Cảnh {sc['id']}: {lo:6.2f}→{hi:6.2f}s, cắt đầu {s0:.2f}s, tốc độ {speed:.2f}x")
    # caption on top: ONE layer when every scene has the same caption (animates in once, then stays still)
    caps = [(sc.get("subtitle") or "").strip() for sc in kept]
    if story.get("caption_top") and any(caps):
        if len(set(caps)) == 1:
            layers.append({"id": "T0", "type": "mograph", "start": 0.0, "end": round(dur, 3), "beat_id": beats[0]["id"],
                           "template": "kinetic_text", "anchor": "top",
                           "data": {"lines": [caps[0]], "emphasis_index": 0, "style": "word_pop", "glow": False}})
        else:
            for sc, cap in zip(kept, caps):
                if cap:
                    lo, hi = spans[sc["id"]]
                    layers.append({"id": f"T{sc['id']}", "type": "mograph", "start": round(lo, 3), "end": round(hi, 3),
                                   "beat_id": f"b{sc['id']}", "template": "kinetic_text", "anchor": "top",
                                   "data": {"lines": [cap], "emphasis_index": 0, "style": "word_pop", "glow": False}})
    for s in sync["scenes"]:
        g = s.get("graphic")
        if g:
            bid =f"b{s['id']}" if any(b["id"] == f"b{s['id']}" for b in beats) else beats[-1]["id"]
            layers.append({"id": f"G{s['id']}", "type": "mograph", "start": g["start"], "end": g["end"], "beat_id": bid,
                           "template": g["template"], "anchor": g.get("anchor", "center"), "data": g.get("data", {})})

    bgm = a.bgm or story.get("bgm")
    tl = {"version": "2.0", "mode": "STORYTELLING",
          "project": {"title": story.get("title", proj.name), "language": "vi", "fps": 30, "width": W, "height": H,
                      "duration_seconds": dur, "voice_audio": sync["voice"], "source_video": None,
                      "bgm": (str(Path(bgm).resolve()) if bgm else None), "bgm_volume": 0.15, "transcript_timing": sync["timing"]},
          "style_bible": {"palette": story.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"], "font": story.get("font", "Roboto"),
                          "subtitle_preset": a.preset or story.get("subtitle_preset", "story_pop"), "subtitle_uppercase": False,
                          "visual_style": story.get("style", "")},
          "words": words, "beats": beats, "assets": assets, "layers": layers,
          "qa": {"subtitle_alignment_status": sync["timing"], "visual_alignment_status": "planned"},
          "capcut_text": capcut_text_spans(story, words)}
    tpath = ndir / "timeline.json"
    tpath.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.preview:
        out = ndir / "build" / "preview.mp4"
    else:
        (proj / "2-xuat").mkdir(exist_ok=True)
        out = proj / "2-xuat" / f"{story.get('title', proj.name)} (giong ke).mp4"
    cmd = [sys.executable, str(HERE / "render.py"), str(tpath), "-o", str(out)] + (["--preview"] if a.preview else []) \
        + (["--capcut-layers"] if a.capcut_layers else [])
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
