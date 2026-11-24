"""Hậu kỳ ÂM THANH ĐẦY ĐỦ cho draft CapCut: SFX cho mọi hành động, ambient từng cảnh, chuyển cảnh, nhạc nền — đúng giây, có mốc bắt đầu + kết thúc.

  python rich_audio.py projects/<slug> [--title "<title> (hau ky)"] [--music-vol 0.10] [--dry]

Đầu vào: storyboard.json (beats/action/setting/narration + tuỳ chọn scene["sfx"]), narration/sync.json + words.json, edit_plan.json (trim),
         assets/sfx/*.wav (sfx_synth.py). CapCut phải TẮT, draft "<title> (hau ky)" đã có giọng kể (post_capcut bước 2).

Luật tự động (quét beats + action + setting, tiếng Anh; và lời kể tiếng Việt):
  mưa → rain (suốt nhịp) · gió/bão → wind · sấm/bão mây → thunder · đêm → crickets (ambient cả cảnh) · sáng/nắng/bình minh → birds
  lấp lánh/ánh nắng/phép → sparkle · co vào vỏ/chui/pop → pop · bò/leo/trượt → slide · thở dài/kiệt sức → heartbeat · chạm/tới nơi → ding + sparkle
  mỗi ranh giới cảnh: swish (liền mạch) hoặc whoosh (đổi bối cảnh); cảnh đầu: chime; câu chốt cuối: chime + ding; nhạc nền pad_warm suốt video.
Ghi đè/thêm tay: scene["sfx"] = [{"key": "thunder", "at": 3.2, "dur": 3.5, "vol": 0.5}] (at = giây trong CẢNH).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SK / "tao-video" / "scripts"))
import build_capcut_draft as B  # noqa: E402

US = 1_000_000
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "sfx"
ROOT = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
LEN = {"swish": .9, "whoosh": 1.4, "rain": 12, "wind": 12, "thunder": 3.5, "crickets": 12, "birds": 12, "pop": .14, "ding": 1.6, "sparkle": 1.0,
       "chime": 2.4, "hit": .7, "rise": 1.6, "heartbeat": 1.8, "step": .18, "slide": 1.2, "pad_warm": 80}
VOL = {"swish": .22, "whoosh": .30, "rain": .30, "wind": .22, "thunder": .45, "crickets": .12, "birds": .10, "pop": .30, "ding": .35,
       "sparkle": .32, "chime": .30, "hit": .35, "rise": .25, "heartbeat": .45, "step": .30, "slide": .28}
AMBIENT = {"rain", "wind", "crickets", "birds"}
# (nhóm từ khoá → âm) — quét chữ thường
RULES = [
    (("rain", "raindrop", "pour", "mưa"), "rain"),
    (("wind", "gust", "storm", "gió", "bão"), "wind"),
    (("thunder", "lightning", "storm clouds", "sấm", "sét"), "thunder"),
    (("sparkle", "glow", "sunbeam", "golden", "magic", "lấp lánh"), "sparkle"),
    (("pulls its whole body into", "tucked", "retract", "peeks out", "co vào", "thu mình"), "pop"),
    (("climb", "crawl", "slide", "creep", "bò", "leo"), "slide"),
    (("sigh", "exhaust", "tired", "give up", "turn back", "thở dài", "kiệt sức"), "heartbeat"),
    (("touches", "reaches", "arrives", "chạm", "tới nơi"), "ding"),
]


def norm(t):
    return re.sub(r"[^\w]+", " ", t.lower()).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--title")
    ap.add_argument("--music-vol", type=float, default=0.10)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
    words = json.loads((proj / "narration" / "words.json").read_text(encoding="utf-8"))
    words = words["words"] if isinstance(words, dict) else words
    ep_path = proj / "edit_plan.json"
    ep = json.loads(ep_path.read_text(encoding="utf-8")) if ep_path.exists() else {}
    slots = {str(s["id"]): s["slot"] for s in sync["scenes"]}
    title = a.title or f"{sb.get('title', proj.name)} (hau ky)"
    total = max(v[1] for v in slots.values())

    cues = []

    def add(t, key, dur, vol, why, sc):
        t = max(0.0, round(t, 2))
        dur = round(min(dur, total - t, LEN[key]), 2)
        if dur > 0.05:
            cues.append({"time": t, "end": round(t + dur, 2), "key": key, "vol": vol, "why": why, "scene": sc})

    def span_cue(t0, dur, key, vol, why, sc):
        """Âm dài hơn file mẫu → nối nhiều đoạn liên tiếp."""
        t = t0
        left = dur
        while left > 0.05:
            seg = min(left, LEN[key])
            add(t, key, seg, vol, why, sc)
            t += seg
            left -= seg

    scenes = sb["scenes"]
    prev_amb = set()
    for i, s in enumerate(scenes):
        sid = str(s["id"])
        st, en = slots[sid]
        slot = en - st
        plan = ep.get(sid, {})
        ts, te = float(plan.get("trim_start", 0)), float(plan.get("trim_end", 0))
        eff = max(1.0, float(s.get("seconds", 10)) - ts - te)
        speed = eff / slot if slot else 1.0

        def to_t(clip_t):               # giây trong clip → giây trên timeline
            return st + max(0.0, (clip_t - ts) / speed)

        beats = s.get("beats") or [["0-%ds" % int(s.get("seconds", 10)), s.get("action", "")]]
        amb_now = set()
        night = any(k in (s.get("setting", "") + " " + " ".join(b[1] for b in beats)).lower() for k in ("night", "moon", "firefl", "đêm"))
        day = any(k in (s.get("setting", "") + " " + " ".join(b[1] for b in beats)).lower() for k in ("morning", "sunny", "daylight", "dawn", "sunrise", "sáng"))
        if night:
            amb_now.add("crickets")
            span_cue(st, slot, "crickets", VOL["crickets"], "đêm: tiếng dế", sid)
        elif day:
            amb_now.add("birds")
            span_cue(st, slot, "birds", VOL["birds"], "ban ngày: tiếng chim", sid)
        for b in beats:
            m = re.match(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", str(b[0]))
            b0, b1 = (float(m.group(1)), float(m.group(2))) if m else (0.0, float(s.get("seconds", 10)))
            text = b[1].lower()
            t0, t1 = to_t(b0), to_t(b1)
            used = set()
            for kws, key in RULES:
                if key in used or not any(k in text for k in kws):
                    continue
                used.add(key)
                if key == "ding":
                    add(t0 + .6, "ding", 1.6, VOL["ding"], f"chạm đích ({b[0]})", sid)
                    add(t0 + .6, "sparkle", 1.0, VOL["sparkle"], "lấp lánh khi tới", sid)
                elif key in AMBIENT or key in ("thunder",):
                    span_cue(t0, max(t1 - t0, 1.0), key, VOL[key], f"{key} ({b[0]})", sid) if key in AMBIENT else add(t0 + .2, key, LEN[key], VOL[key], f"{key} ({b[0]})", sid)
                    if key in AMBIENT:
                        amb_now.add(key)
                elif key == "slide":
                    span_cue(t0, min(t1 - t0, 3.6), "slide", VOL["slide"], f"bò/leo ({b[0]})", sid)
                elif key == "heartbeat":
                    add(t0 + .3, "heartbeat", LEN["heartbeat"], VOL["heartbeat"], f"mệt/do dự ({b[0]})", sid)
                else:
                    add(t0 + .2, key, LEN[key], VOL[key], f"{key} ({b[0]})", sid)
        for x in s.get("sfx") or []:           # ghi đè / thêm tay
            k = x["key"]
            span_cue(st + float(x.get("at", 0)), float(x.get("dur", LEN[k])), k, float(x.get("vol", VOL[k])), x.get("why", "thêm tay"), sid)
        # ranh giới cảnh
        if i > 0:
            changed = (amb_now != prev_amb) or bool(s.get("transition_in"))
            add(st - 0.15, "whoosh" if changed else "swish", LEN["whoosh" if changed else "swish"], VOL["whoosh" if changed else "swish"],
                "đổi bối cảnh" if changed else "nối cảnh", sid)
        prev_amb = amb_now
    # mở đầu + chốt
    add(0.15, "chime", 2.4, VOL["chime"], "mở đầu", str(scenes[0]["id"]))
    lst = scenes[-1]
    st, en = slots[str(lst["id"])]
    lw = [w for w in words if st <= w["start"] <= en]
    t_end = (lw[-1]["start"] - 0.4) if lw else en - 1.5
    add(t_end, "chime", 2.4, VOL["chime"], "câu chốt", str(lst["id"]))
    add(t_end + .1, "ding", 1.6, VOL["ding"], "câu chốt", str(lst["id"]))
    cues.sort(key=lambda c: c["time"])
    print(f"Kế hoạch: {len(cues)} âm thanh (+ nhạc nền) cho {len(scenes)} cảnh, {total:.1f}s")
    for c in cues[:60]:
        print(f"  {c['time']:6.2f}–{c['end']:6.2f}  {c['key']:9s} {c['vol']:.2f}  cảnh {c['scene']}: {c['why']}")
    if a.dry:
        return

    draft = ROOT / title / "draft_content.json"
    if not draft.exists():
        sys.exit(f"STOP: chưa có draft '{title}' — chạy post_capcut.py trước (CapCut TẮT).")
    doc = json.load(open(draft, encoding="utf-8"))
    audio_tracks = [t for t in doc["tracks"] if t["type"] == "audio"]
    if not audio_tracks:
        sys.exit("STOP: draft không có track giọng kể")
    voice_track = audio_tracks[0]
    vseg = voice_track["segments"][0]
    doc["tracks"] = [t for t in doc["tracks"] if t["type"] != "audio" or t is voice_track]     # bỏ SFX/nhạc cũ, giữ giọng kể
    miss = sorted(({c["key"] for c in cues} | {"pad_warm"}) - {p.stem for p in ASSETS.glob("*.wav")})
    if miss:
        sys.exit(f"STOP: thiếu file âm thanh {miss} — chạy sfx_synth.py")

    lanes = []

    def place(key, at, dur, vol, music=False):
        seg, mat, _ = B.Cloner(doc, doc["materials"]).segment(vseg)
        f = ASSETS / f"{key}.wav"
        d = int(dur * US)
        mat.update({"name": f"{key}.wav", "path": str(f).replace("\\", "/"), "duration": int(LEN[key] * US), "type": "extract_music",
                    "category_name": "local", "local_material_id": str(uuid.uuid4()), "music_id": str(uuid.uuid4()), "wave_points": []})
        seg.update({"source_timerange": {"start": 0, "duration": d}, "target_timerange": {"start": int(at * US), "duration": d}, "speed": 1.0, "volume": vol})
        for lane in lanes:
            if lane["end"] <= at - 0.01:
                break
        else:
            lane = {"end": 0, "track": copy.deepcopy(voice_track)}
            lane["track"]["id"] = B.new_id()
            lane["track"]["segments"] = []
            lanes.append(lane)
        lane["track"]["segments"].append(seg)
        lane["end"] = at + dur

    for c in cues:
        place(c["key"], c["time"], c["end"] - c["time"], c["vol"])
    t = 0.0
    while t < total - 0.5:                                  # nhạc nền: lặp pad_warm nếu video dài hơn file
        seg_len = min(LEN["pad_warm"], total - t)
        place("pad_warm", t, seg_len, a.music_vol, music=True)
        t += seg_len
    doc["tracks"] += [ln["track"] for ln in lanes]
    B.dump(doc, draft)
    tl = ROOT / title / "Timelines" / doc["id"] / "draft_content.json"
    if tl.parent.exists():
        B.dump(doc, tl)
    out = [{"kind": "sfx", "scene": c["scene"], "time": c["time"], "end": c["end"], "timecode": f"{int(c['time'] // 60):02d}:{c['time'] % 60:05.2f}",
            "sound": c["why"], "search": f"{c['key']}.wav", "volume": c["vol"], "why": c["why"]} for c in cues]
    (proj / "narration").mkdir(exist_ok=True)
    (proj / "narration" / "sfx_cues.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: chèn {len(cues)} âm thanh ({len(lanes)} track) + nhạc nền vào '{title}'.")


if __name__ == "__main__":
    main()
