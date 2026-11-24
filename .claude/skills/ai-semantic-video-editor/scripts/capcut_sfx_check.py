"""Đọc project CapCut ĐANG MỞ (CapCut tự lưu draft_content.json sau mỗi thao tác) và so với kế hoạch SFX.

Không cần đóng CapCut. Chạy sau MỖI bước thao tác SFX trong giao diện để biết ngay:
  - từng SFX đang nằm ở đâu (bắt đầu–kết thúc, âm lượng) — không phải đoán bằng mắt trên timeline
  - lệch so với narration/sfx_cues.json (at/end) quá ±0,15s, SFX thiếu, SFX lạ
  - TRACK VIDEO CHÍNH còn đủ cảnh và đúng thời lượng không (bắt lỗi Ctrl+B / BackSpace nhầm làm mất cảnh)

  python capcut_sfx_check.py projects/<slug>/storyboard.json [--title "..."] [--tol 0.15]
Thoát mã 1 nếu có lỗi.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
US = 1_000_000
ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--title")
    ap.add_argument("--tol", type=float, default=0.15)
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = json.loads(sp.read_text(encoding="utf-8"))
    title = a.title or f"{story.get('title', proj.name)} (hau ky)"
    d = json.loads((ROOT / title / "draft_content.json").read_text(encoding="utf-8"))
    names = {}
    for v in d["materials"].values():
        if isinstance(v, list):
            for m in v:
                if isinstance(m, dict) and "id" in m:
                    names[m["id"]] = m.get("name") or Path(m.get("path", "")).name
    errors = []

    # 1) main video track must be intact
    layers = json.loads((proj / "narration" / "build" / "final" / "capcut_layers.json").read_text(encoding="utf-8"))
    n_scenes = len(layers["segments"])
    vtracks = [t for t in d["tracks"] if t["type"] == "video"]
    main = max(vtracks, key=lambda t: len(t["segments"])) if vtracks else {"segments": []}
    end = max((s["target_timerange"]["start"] + s["target_timerange"]["duration"] for s in main["segments"]), default=0) / US
    tl_dur = json.loads((proj / "narration" / "timeline.json").read_text(encoding="utf-8"))["project"].get("duration_seconds")
    if tl_dur is None:  # video-tai-lieu: không có duration_seconds → tổng độ dài các đoạn cảnh đã cắt
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from vse_common import probe_duration
        tl_dur = sum(probe_duration(Path(p)) for p in layers["segments"])
    print(f"Track video chính: {len(main['segments'])}/{n_scenes} cảnh, hết ở {end:.2f}s (timeline {tl_dur:.2f}s)")
    if len(main["segments"]) != n_scenes or abs(end - tl_dur) > 0.1:
        errors.append("TRACK VIDEO CHÍNH BỊ ĐỔI (mất/xê dịch cảnh) — bấm nút Hoàn tác trên thanh timeline ngay")

    # 2) SFX + effects currently in the project
    segs = []
    for t in d["tracks"]:
        if t["type"] not in ("audio", "effect"):
            continue
        for s in t["segments"]:
            n = str(names.get(s["material_id"], "?"))
            if n.startswith("voice"):
                continue
            st = s["target_timerange"]["start"] / US
            segs.append({"type": t["type"], "start": st, "end": st + s["target_timerange"]["duration"] / US,
                         "vol": s.get("volume", 1.0), "name": n})
    segs.sort(key=lambda x: x["start"])
    print("\nĐang có trong CapCut:")
    for s in segs:
        warn = "  ← âm lượng 1.0, chưa hạ" if s["type"] == "audio" and s["vol"] > 0.9 else ""
        print(f"  {s['type']:6} {s['start']:6.2f}–{s['end']:6.2f}s  vol={s['vol']:.2f}  {s['name'][:45]}{warn}")
        if warn:
            errors.append(f"SFX '{s['name'][:30]}' ở {s['start']:.2f}s chưa hạ âm lượng")

    # 3) compare with the plan
    cues_p = proj / "narration" / "sfx_cues.json"
    cues = [c for c in json.loads(cues_p.read_text(encoding="utf-8"))] if cues_p.exists() else []
    cues = [c for c in cues if c["kind"] == "sfx"]
    if cues:
        print("\nSo với kế hoạch (narration/sfx_cues.json):")
        pool = [s for s in segs if s["type"] == "audio"]
        for c in cues:
            same = [s for s in pool if c.get("search") and str(c["search"])[:24] in s["name"]]  # ưu tiên đúng tên âm thanh (nhiều tiếng cùng một giây)
            best = min(same or pool, key=lambda s: abs(s["start"] - c["time"]), default=None)
            if not best or abs(best["start"] - c["time"]) > 1.0:
                errors.append(f"THIẾU SFX '{c.get('sound', '')}' {c['time']:.2f}s")
                print(f"  ✗ {c['time']:6.2f}s  {c.get('sound', '')}: chưa có")
                continue
            pool.remove(best)
            ds = best["start"] - c["time"]
            de = (best["end"] - c["end"]) if "end" in c else None
            ok = abs(ds) <= a.tol and (de is None or abs(de) <= a.tol)
            msg = f"đầu {ds:+.2f}s" + (f", cuối {de:+.2f}s" if de is not None else ", (kế hoạch thiếu mốc kết thúc)")
            print(f"  {'✓' if ok else '✗'} {c['time']:6.2f}–{c.get('end', 0):6.2f}s  {c.get('sound', '')}: {msg}")
            if not ok:
                errors.append(f"SFX '{c.get('sound', '')}' lệch: {msg}")
        for s in pool:
            print(f"  ? SFX ngoài kế hoạch {s['start']:.2f}–{s['end']:.2f}s {s['name'][:40]}")
    print("\n" + ("LỖI:\n  - " + "\n  - ".join(errors) if errors else "OK: video nguyên vẹn, SFX khớp kế hoạch."))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
