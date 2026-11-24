"""Validate timeline.json (v2) against references/timeline-schema.md.

Usage: python validate_timeline.py timeline.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vse_common  # noqa: E402,F401  (utf-8 console)

MODES = {"KOC_REVIEW", "STORYTELLING"}
LAYER_TYPES = {"scene", "mograph", "overlay", "broll"}
TEMPLATES = {"counter", "bar_chart", "checklist", "callout", "compare", "kinetic_text"}
MOTIONS = {"push_in", "pull_out", "pan_left", "pan_right", "pan_up", "pan_down", "static", None}
PRESETS = {"clean", "box", "karaoke", "pop_word", "keyword", "cinematic", "story_pop"}


def validate(tl: dict, base: Path) -> tuple[list[str], list[str]]:
    E, W = [], []
    mode = tl.get("mode")
    if mode not in MODES:
        E.append(f"mode phải là một trong {sorted(MODES)}")
    pr = tl.get("project", {})
    dur = pr.get("duration_seconds")
    if not isinstance(dur, (int, float)) or dur <= 0:
        E.append("project.duration_seconds phải > 0")
        dur = 1e9
    for k in ("fps", "width", "height"):
        if not isinstance(pr.get(k), int) or pr[k] <= 0:
            E.append(f"project.{k} phải là số nguyên dương")
    if mode == "KOC_REVIEW":
        if not pr.get("source_video"):
            E.append("KOC_REVIEW cần project.source_video")
        elif not (base / pr["source_video"]).exists():
            E.append(f"Không thấy source_video: {pr['source_video']}")
    if mode == "STORYTELLING":
        if not pr.get("voice_audio"):
            E.append("STORYTELLING cần project.voice_audio")
        elif not (base / pr["voice_audio"]).exists():
            E.append(f"Không thấy voice_audio: {pr['voice_audio']}")
    if pr.get("bgm") and not (base / pr["bgm"]).exists():
        E.append(f"Không thấy bgm: {pr['bgm']}")
    if pr.get("transcript_timing") == "provisional":
        W.append("Timing đang là provisional (tạm tính), chưa khớp giọng thật")
    preset = tl.get("style_bible", {}).get("subtitle_preset", "clean")
    if preset not in PRESETS:
        E.append(f"style_bible.subtitle_preset không hợp lệ: {preset}")

    def span(obj, label):
        s, e = obj.get("start"), obj.get("end")
        if not isinstance(s, (int, float)) or not isinstance(e, (int, float)):
            E.append(f"{label}: thiếu start/end")
            return False
        if s < 0 or e <= s or e > dur + 1e-6:
            E.append(f"{label}: thời gian sai ({s}→{e}, duration {dur})")
            return False
        return True

    words = tl.get("words", [])
    wids = set()
    prev_end = 0.0
    for w in words:
        wids.add(w.get("id"))
        if span(w, f"word {w.get('id')}") and w["start"] < prev_end - 0.05:
            W.append(f"word {w['id']} chồng lên từ trước")
        prev_end = max(prev_end, w.get("end", 0) or 0)

    assets = {a.get("id"): a for a in tl.get("assets", [])}
    for a in assets.values():
        st = a.get("status")
        if st not in ("ready", "missing", "needs_verification"):
            E.append(f"asset {a.get('id')}: status không hợp lệ")
        if st == "ready" and (not a.get("file") or not (base / a["file"]).exists()):
            E.append(f"asset {a['id']}: status ready nhưng không thấy file {a.get('file')}")
        if st == "missing":
            W.append(f"asset {a['id']} còn thiếu → sẽ dùng placeholder")
        if st == "needs_verification":
            W.append(f"asset {a['id']} cần kiểm tra bản quyền/nội dung")

    beats = {b.get("id"): b for b in tl.get("beats", [])}
    for b in beats.values():
        span(b, f"beat {b.get('id')}")
        for wid in b.get("visual_cue_word_ids", []):
            if wid not in wids:
                E.append(f"beat {b['id']}: visual_cue_word_ids trỏ tới từ không tồn tại: {wid}")
        for aid in b.get("asset_ids", []):
            if aid not in assets:
                E.append(f"beat {b['id']}: asset_ids trỏ tới asset không tồn tại: {aid}")

    scenes, mographs = [], []
    for L in tl.get("layers", []):
        lid = L.get("id")
        t = L.get("type")
        if t not in LAYER_TYPES:
            E.append(f"layer {lid}: type không hợp lệ {t}")
            continue
        span(L, f"layer {lid}")
        if L.get("beat_id") and L["beat_id"] not in beats:
            E.append(f"layer {lid}: beat_id không tồn tại {L['beat_id']}")
        if t in ("scene", "overlay", "broll"):
            if L.get("asset_id") not in assets:
                E.append(f"layer {lid}: asset_id không tồn tại {L.get('asset_id')}")
        if t == "scene":
            scenes.append(L)
            if L.get("motion") not in MOTIONS:
                E.append(f"layer {lid}: motion không hợp lệ {L.get('motion')}")
        if t == "mograph":
            mographs.append(L)
            tpl = L.get("template")
            d = L.get("data", {})
            if tpl not in TEMPLATES:
                E.append(f"layer {lid}: template không hợp lệ {tpl}")
            if tpl in ("counter", "bar_chart") and not (d.get("source") or d.get("illustrative")):
                E.append(f"layer {lid}: {tpl} cần data.source hoặc data.illustrative=true (không bịa số liệu)")
            if tpl == "counter" and not isinstance(d.get("value"), (int, float)):
                E.append(f"layer {lid}: counter cần data.value là số")
            if tpl == "bar_chart" and not d.get("items"):
                E.append(f"layer {lid}: bar_chart cần data.items")
            if tpl == "checklist" and not d.get("items"):
                E.append(f"layer {lid}: checklist cần data.items")
            if tpl == "checklist" and d.get("times") and len(d["times"]) != len(d.get("items", [])):
                E.append(f"layer {lid}: checklist times phải có cùng số phần tử với items")
            if tpl == "kinetic_text" and not d.get("lines"):
                E.append(f"layer {lid}: kinetic_text cần data.lines")
            if tpl == "callout" and not d.get("text"):
                E.append(f"layer {lid}: callout cần data.text")
            if tpl == "compare" and not (d.get("left") and d.get("right")):
                E.append(f"layer {lid}: compare cần data.left và data.right")

    if mode == "STORYTELLING":
        scenes.sort(key=lambda x: x.get("start", 0))
        if not scenes:
            E.append("STORYTELLING cần ít nhất một layer scene")
        else:
            if scenes[0]["start"] > 0.05:
                E.append(f"Cảnh đầu tiên phải bắt đầu ở 0 (đang là {scenes[0]['start']})")
            for a, b in zip(scenes, scenes[1:]):
                if abs(b["start"] - a["end"]) > 0.05:
                    E.append(f"Cảnh {a['id']}→{b['id']} bị hở/chồng ({a['end']} vs {b['start']})")
            if dur - scenes[-1]["end"] > 0.05:
                E.append(f"Cảnh cuối phải kéo tới hết video ({scenes[-1]['end']} < {dur})")
    mographs.sort(key=lambda x: x.get("start", 0))
    for a, b in zip(mographs, mographs[1:]):
        if b["start"] < a["end"] - 0.01:
            W.append(f"Graphic {a['id']} và {b['id']} chồng thời gian, kiểm tra bố cục")
    return E, W


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: validate_timeline.py timeline.json")
    p = Path(sys.argv[1])
    tl = json.loads(p.read_text(encoding="utf-8"))
    E, W = validate(tl, p.parent)
    for w in W:
        print(f"CẢNH BÁO: {w}")
    for e in E:
        print(f"LỖI: {e}")
    print(f"\n{len(E)} lỗi, {len(W)} cảnh báo")
    sys.exit(1 if E else 0)


if __name__ == "__main__":
    main()
