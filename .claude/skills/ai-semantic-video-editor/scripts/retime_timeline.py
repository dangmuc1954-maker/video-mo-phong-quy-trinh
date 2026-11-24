"""Re-sync a timeline to a new voice recording (e.g. after ElevenLabs TTS).

Every time in the timeline (beats, scenes, graphics, checklist times, words) is mapped from the
old word timings to the new ones with a piecewise-linear map, so scenes and graphics stay locked
to the same spoken words when the voice speed or pauses change.

Usage:
  python retime_timeline.py timeline.json --words words.json --voice voice.mp3 [-o timeline.json]
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import load_words, normalize_token, probe_duration  # noqa: E402


def build_map(old: list[dict], new: list[dict], old_dur: float, new_dur: float):
    """Control points (old_t -> new_t) from matched words."""
    import difflib
    a = [normalize_token(w["text"]) for w in old]
    b = [normalize_token(w["text"]) for w in new]
    pts = [(0.0, 0.0)]
    pairs = {}
    for blk in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            o, n = old[blk.a + k], new[blk.b + k]
            pairs[o["id"]] = n["id"]
            pts += [(o["start"], n["start"]), (o["end"], n["end"])]
    pts.append((old_dur, new_dur))
    pts.sort()
    xs, ys = [], []
    for x, y in pts:  # keep strictly increasing
        if xs and (x <= xs[-1] or y < ys[-1]):
            continue
        xs.append(x)
        ys.append(y)
    matched = len(pairs) / max(1, len(old))

    def f(t: float) -> float:
        if t <= xs[0]:
            return ys[0]
        if t >= xs[-1]:
            return ys[-1] + (t - xs[-1])
        i = bisect.bisect_right(xs, t) - 1
        x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
        return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
    return f, pairs, matched


def retime(timeline: Path, words: Path, voice: Path, out: Path | None = None) -> None:
    tp = Path(timeline).resolve()
    base = tp.parent
    tl = json.loads(tp.read_text(encoding="utf-8"))
    old = tl.get("words", [])
    wpath = Path(words).resolve()
    wdata = json.loads(wpath.read_text(encoding="utf-8"))
    new = load_words(wpath)
    meta = wdata.get("meta", {}) if isinstance(wdata, dict) else {}
    voice = Path(voice).resolve()
    new_dur = round(probe_duration(voice), 3)
    old_dur = float(tl["project"]["duration_seconds"])
    f, pairs, matched = build_map(old, new, old_dur, new_dur)
    if matched < 0.8:
        print(f"CẢNH BÁO: chỉ khớp được {matched:.0%} số từ, kịch bản có thể đã bị đổi.")

    R = lambda t: round(min(max(f(float(t)), 0.0), new_dur), 3)  # noqa: E731
    for b in tl.get("beats", []):
        b["start"], b["end"] = R(b["start"]), R(b["end"])
        b["visual_cue_word_ids"] = [pairs[w] for w in b.get("visual_cue_word_ids", []) if w in pairs]
    for L in tl.get("layers", []):
        L["start"], L["end"] = R(L["start"]), R(L["end"])
        d = L.get("data") or {}
        if isinstance(d.get("times"), list):
            d["times"] = [R(t) for t in d["times"]]
        if L["end"] - L["start"] < 0.3:
            L["end"] = round(min(new_dur, L["start"] + 0.3), 3)

    # scenes: keep contiguous and covering the full new duration
    scenes = sorted([L for L in tl.get("layers", []) if L["type"] == "scene"], key=lambda L: L["start"])
    if scenes:
        scenes[0]["start"] = 0.0
        for x, y in zip(scenes, scenes[1:]):
            x["end"] = y["start"]
        scenes[-1]["end"] = new_dur
    beats = sorted(tl.get("beats", []), key=lambda b: b["start"])
    if beats:
        beats[0]["start"] = 0.0
        for x, y in zip(beats, beats[1:]):
            x["end"] = y["start"]
        beats[-1]["end"] = new_dur

    tl["words"] = new
    pr = tl["project"]
    pr["duration_seconds"] = new_dur
    try:
        pr["voice_audio"] = voice.relative_to(base).as_posix()
    except ValueError:
        pr["voice_audio"] = str(voice)
    pr["transcript_timing"] = meta.get("timing", "verified")
    qa = tl.setdefault("qa", {})
    qa["subtitle_alignment_status"] = pr["transcript_timing"]
    qa["notes"] = [n for n in qa.get("notes", []) if "tạm tính" not in n]
    out = Path(out).resolve() if out else tp
    out.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Đã khớp lại timeline: {old_dur:.2f}s → {new_dur:.2f}s, khớp {matched:.0%} số từ → {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("--words", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    retime(Path(a.timeline), Path(a.words), Path(a.voice), Path(a.out) if a.out else None)


if __name__ == "__main__":
    main()
