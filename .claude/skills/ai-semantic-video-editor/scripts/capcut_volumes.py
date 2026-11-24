"""Set the audio levels of a CapCut post-production draft (run with CapCut CLOSED, after adding SFX in CapCut).

Typing a volume into CapCut's panel through UI automation is unreliable (values were ignored or became
+11 dB), so levels are written into the draft instead:
  - narration voice → --voice (default 1.6 = about +4 dB, the ElevenLabs voice is quiet)
  - every other audio clip (SFX added in CapCut) → the "volume" of the nearest cue in narration/sfx_cues.json
    (within 1.5 s of its start), otherwise --sfx (default 0.35)

  python capcut_volumes.py projects/<slug>/storyboard.json [--title "..."] [--voice 1.6] [--sfx 0.35]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tao-video" / "scripts"))
sys.path.insert(0, str(HERE))
import build_capcut_draft as B  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--title")
    ap.add_argument("--voice", type=float, default=1.6)
    ap.add_argument("--sfx", type=float, default=0.35)
    a = ap.parse_args()
    if B.capcut_running():
        sys.exit("CapCut đang mở. Đóng CapCut (để nó lưu project) rồi chạy lại.")
    sp = Path(a.storyboard).resolve()
    story = json.loads(sp.read_text(encoding="utf-8"))
    title = a.title or f"{story.get('title', sp.parent.name)} (hau ky)"
    draft = Path(B.ROOT) / title
    if not (draft / B.MARKER).exists():
        sys.exit(f"Không thấy project do skill tạo: {draft}")
    cues_p = sp.parent / "narration" / "sfx_cues.json"
    cues = [c for c in (json.loads(cues_p.read_text(encoding="utf-8")) if cues_p.exists() else []) if c.get("kind") == "sfx"]
    files = [draft / "draft_content.json"] + [Path(p) for p in glob.glob(str(draft / "Timelines" / "*" / "draft_content.json"))]
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        mats = {m["id"]: m for m in d["materials"].get("audios", [])}
        lines = []
        for t in d["tracks"]:
            if t["type"] != "audio":
                continue
            for s in t["segments"]:
                name = mats.get(s["material_id"], {}).get("name", "")
                start = s["target_timerange"]["start"] / 1e6
                if name.startswith("voice"):
                    v = a.voice
                else:
                    near = min(cues, key=lambda c: abs(c["time"] - start), default=None)
                    v = float(near["volume"]) if near and abs(near["time"] - start) <= 1.5 and near.get("volume") else a.sfx
                s["volume"] = v
                s["last_nonzero_volume"] = v
                lines.append(f"  {start:6.2f}s  {v:4.2f}  {name[:50]}")
        f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Đã đặt âm lượng cho \"{title}\":")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
