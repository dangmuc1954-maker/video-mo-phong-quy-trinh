"""Ghép render/video.mp4 + giọng (+ nhạc nền) → 2-xuat/<title>.mp4, và chuẩn bị hậu kỳ CapCut.

  python compose.py projects/<slug> [--bgm nhac.mp3] [--bgm-db -20]
  python compose.py projects/<slug> --capcut     # thêm: cắt cảnh + lớp trống + timeline → chạy capcut_post.py
                                                 #   (CapCut phải đang TẮT; nếu đang mở thì HỎI anh, không tự tắt)
Bảng SFX gợi ý (theo từ khoá, chuyển cảnh, hành động) → narration/sfx_cues.md (capcut_post ghi) hoặc render/sfx_cues.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
POST = SKILL.parent / "ai-semantic-video-editor" / "scripts" / "capcut_post.py"


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(r.stderr[-1500:])


def tc(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--bgm")
    ap.add_argument("--bgm-db", type=float, default=-20)
    ap.add_argument("--capcut", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    rd = proj / "render"
    tl = json.loads((rd / "timeline.json").read_text(encoding="utf-8"))
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    video, voice = rd / "video.mp4", proj / "narration" / "voice.mp3"
    out_dir = proj / "2-xuat"
    out_dir.mkdir(exist_ok=True)
    title = tl.get("title") or proj.name
    final = out_dir / f"{title}.mp4"
    if a.bgm:
        fc = (f"[2:a]volume={a.bgm_db}dB,aloop=-1:size=2e9[m];[1:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
              f"[v][md]amix=inputs=2:duration=first:normalize=0[a]")
        run(["ffmpeg", "-y", "-i", str(video), "-i", str(voice), "-stream_loop", "-1", "-i", a.bgm, "-filter_complex", fc,
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    else:
        run(["ffmpeg", "-y", "-i", str(video), "-i", str(voice), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
             "-b:a", "192k", "-af", "apad", "-shortest", str(final)])
    print(f"Bản FFmpeg: {final}")

    sfx = json.loads((rd / "sfx_plan.json").read_text(encoding="utf-8"))
    md = ["# SFX gợi ý cho hậu kỳ CapCut", "", "| Thời điểm | Cảnh | Âm thanh | Từ khoá tìm (EN) | Âm lượng | Vì sao |", "|---|---|---|---|---|---|"]
    md += [f"| {tc(x['time'])} | {x['scene']} | {x.get('sound', '')} | {x.get('search', '')} | {x.get('volume', '')} | {x.get('why', '')} |" for x in sfx]
    (rd / "sfx_cues.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if not a.capcut:
        return

    # ---- chuẩn bị đầu vào cho capcut_post.py (dùng lại bước hậu kỳ có sẵn) ----
    fin = proj / "narration" / "build" / "final"
    (fin / "segments").mkdir(parents=True, exist_ok=True)
    segs, layers = [], []
    for i, s in enumerate(tl["scenes"]):
        f = fin / "segments" / f"seg_{i:03d}.mp4"
        run(["ffmpeg", "-y", "-ss", f"{s['start']:.3f}", "-to", f"{s['end']:.3f}", "-i", str(video), "-an", "-c:v", "libx264", "-crf", "16",
             "-pix_fmt", "yuv420p", str(f)])
        segs.append(str(f))
        layers.append({"type": "scene", "asset_id": f"c{s['id']}", "start": s["start"], "end": s["end"], "source_start": 0, "speed": 1.0})
    blank = fin / "text_layer.mov"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black@0.0:s={tl['W']}x{tl['H']}:r=5:d={tl['duration']:.2f},format=argb",
         "-c:v", "qtrle", str(blank)])
    (fin / "capcut_layers.json").write_text(json.dumps({"segments": segs, "text_layer": str(blank)}, ensure_ascii=False), encoding="utf-8")
    (proj / "narration" / "timeline.json").write_text(json.dumps({"project": {"voice_audio": "voice.mp3"}, "layers": layers},
                                                               ensure_ascii=False), encoding="utf-8")
    by = {}
    for x in sfx:
        s = next(s for s in tl["scenes"] if s["id"] == x["scene"])
        by.setdefault(x["scene"], []).append({"at_clip": round(x["time"] - s["start"], 3), "sound": x.get("sound", ""),
                                              "search": x.get("search", ""), "volume": x.get("volume", 0.4), "why": x.get("why", ""),
                                              **({"variant": x["variant"]} if x.get("variant") else {})})
    cs = {"title": f"{title} (hau ky)", "canvas": [tl["W"], tl["H"]],
          "scenes": [{"id": s["id"], "sfx": by.get(s["id"], []),
                      **({"transition_in": c} if (c := next((x.get("capcut_transition") for x in sb["scenes"] if x["id"] == s["id"]), None)) else {})}
                     for s in tl["scenes"]]}
    csp = proj / "_capcut_sb.json"
    csp.write_text(json.dumps(cs, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(POST), str(csp), "--title", cs["title"]], text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit("capcut_post.py dừng (CapCut đang mở? → hỏi anh cho tắt, KHÔNG tự tắt).")


if __name__ == "__main__":
    main()
