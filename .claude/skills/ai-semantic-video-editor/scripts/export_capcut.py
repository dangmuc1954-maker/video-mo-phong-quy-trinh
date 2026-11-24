"""Package a timeline for finishing in CapCut.

Creates: video_base.mp4 (no subtitles), voice, subs.srt (+ .ass), graphics/*.mov (alpha),
scenes/ in order, cue_sheet.csv + cue_sheet.md.

Usage:
  python export_capcut.py timeline.json [-o build/capcut_package] [--separate-graphics]
  --separate-graphics: video_base has no graphics; place graphics/*.mov yourself using the cue sheet.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_subs import build_subs  # noqa: E402
from mograph import render_mograph  # noqa: E402
from render import anchor_xy  # noqa: E402


def tc(t: float, fps: int) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{int(s):02d}.{min(fps - 1, int(round((s % 1) * fps))):02d}f"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("-o", "--out")
    ap.add_argument("--separate-graphics", action="store_true")
    a = ap.parse_args()

    tl_path = Path(a.timeline).resolve()
    base = tl_path.parent
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    pr, sb = tl["project"], tl.get("style_bible", {})
    W, H, fps = pr["width"], pr["height"], pr["fps"]
    pkg = Path(a.out).resolve() if a.out else base / "build" / "capcut_package"
    (pkg / "graphics").mkdir(parents=True, exist_ok=True)
    (pkg / "scenes").mkdir(exist_ok=True)

    # 1. base video without subtitles
    cmd = [sys.executable, str(Path(__file__).with_name("render.py")), str(tl_path), "--no-subs",
           "-o", str(pkg / "video_base.mp4")]
    if a.separate_graphics:
        cmd.append("--no-mograph")
    print("Render video nền (không phụ đề)…")
    if subprocess.run(cmd).returncode != 0:
        sys.exit("Render video nền thất bại.")

    # 2. voice + subtitles
    voice = pr.get("voice_audio")
    if voice:
        shutil.copy2(base / voice, pkg / f"voice{Path(voice).suffix}")
    palette = sb.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"]
    if tl.get("words"):
        kws = sorted({k for b in tl.get("beats", []) for k in b.get("keywords", [])})
        build_subs(tl["words"], pkg / "subs", sb.get("subtitle_preset", "clean"), W, H, sb.get("font", "Roboto"),
                   palette[2], kws, bool(sb.get("subtitle_uppercase")))

    # 3. graphics + scenes + cue sheet
    rows = []
    assets = {x["id"]: x for x in tl.get("assets", [])}
    for L in sorted(tl.get("layers", []), key=lambda L: L["start"]):
        s, e = L["start"], L["end"]
        row = {"start": tc(s, fps), "end": tc(e, fps), "start_s": s, "end_s": e, "track": L["type"],
               "id": L["id"], "beat": L.get("beat_id", ""), "file": "", "position": "", "note": ""}
        if L["type"] == "mograph":
            g = pkg / "graphics" / f"{L['id']}_{L['template']}.mov"
            info = render_mograph({"template": L["template"], "data": L.get("data", {}), "duration": e - s,
                                   "width": W, "height": H, "fps": fps, "palette": palette,
                                   "font": sb.get("font", "Roboto"), "time_offset": s}, g)
            x, y = (0, 0) if info["full_frame"] else anchor_xy(L.get("anchor"), info["width"], info["height"], W, H)
            row.update(file=f"graphics/{g.name}", position=f"x={x}px y={y}px (góc trên trái, khung {W}x{H})",
                       note=L["template"])
        elif L["type"] in ("scene", "overlay", "broll"):
            asset = assets.get(L.get("asset_id"), {})
            src = base / asset["file"] if asset.get("file") and (base / asset["file"]).exists() else None
            if src:
                dst = pkg / "scenes" / f"{len(rows) + 1:03d}_{L['id']}_{src.name}"
                shutil.copy2(src, dst)
                row["file"] = f"scenes/{dst.name}"
            else:
                row["note"] = f"THIẾU ASSET {asset.get('id')} — prompt: {asset.get('prompt', '')[:120]}"
            if L["type"] == "scene":
                row["note"] = (row["note"] + f" motion={L.get('motion', 'static')}").strip()
        rows.append(row)

    with open(pkg / "cue_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["start"])
        w.writeheader()
        w.writerows(rows)
    md = ["# Cue sheet", "", f"Khung hình {W}x{H}, {fps}fps. Thời gian dạng phút:giây.frame.", "",
          "| Bắt đầu | Kết thúc | Track | ID | File | Vị trí / ghi chú |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['start']} | {r['end']} | {r['track']} | {r['id']} | {r['file']} | {r['position']} {r['note']} |")
    md += ["", "## Cách dựng trong CapCut",
           "1. Kéo `video_base.mp4` vào track chính (đã có cảnh, chuyển động máy"
           + ("" if a.separate_graphics else ", graphic") + " và âm thanh).",
           "2. Text → Phụ đề → Nhập (Import) `subs.srt`, rồi chọn mẫu chữ/hiệu ứng của CapCut.",
           "3. " + ("Kéo từng file trong `graphics/` lên track phủ theo thời gian ở bảng trên." if a.separate_graphics
                    else "Muốn chỉnh riêng graphic thì xuất lại với `--separate-graphics`."),
           "4. Xuất 1080x1920, 30fps."]
    (pkg / "cue_sheet.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nGói CapCut: {pkg}")


if __name__ == "__main__":
    main()
