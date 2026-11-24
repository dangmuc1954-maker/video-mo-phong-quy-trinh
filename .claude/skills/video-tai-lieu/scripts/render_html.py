"""render/timeline.json → render/video.mp4 (không tiếng) bằng engine HTML + Chromium chạy ngầm.

  python render_html.py projects/<slug>            # bản đầy đủ 30fps
  python render_html.py projects/<slug> --preview  # nửa độ phân giải, 15fps — xem nhanh
  python render_html.py projects/<slug> --stills 2.5 7 12.3   # chỉ chụp khung tại các giây → render/still_*.jpg (QA)
  python render_html.py projects/<slug> --from 10 --to 20      # chỉ một đoạn
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ENGINE = (SKILL / "templates" / "engine.html").as_uri()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float)
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--out")
    ap.add_argument("--jobs", type=int, default=4, help="số luồng render song song (mặc định 4)")
    a = ap.parse_args()
    if a.stills is None and a.jobs > 1 and a.out is None:
        return parallel(a)
    proj = Path(a.project).resolve()
    rd = proj / "render"
    tl = json.loads((rd / "timeline.json").read_text(encoding="utf-8"))
    W, H = tl["W"], tl["H"]
    fps = 15 if a.preview else tl.get("fps", 30)
    scale = 0.5 if a.preview else 1.0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security", "--force-color-profile=srgb",
                                      "--disable-gpu-vsync", "--hide-scrollbars"])
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
        msgs = []
        pg.on("console", lambda m: msgs.append(m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: msgs.append(str(e)))
        overlay = needs_overlay(tl) and a.stills is None
        if needs_overlay(tl):
            tl["overlay_mode"] = a.stills is None
            tl["brand"] = {**tl.get("brand", {}), "bg": "transparent"} if overlay else tl.get("brand", {})
        pg.goto(ENGINE)
        info = pg.evaluate("tl => window.init(tl)", tl)
        if msgs:
            print("Cảnh báo engine:", *msgs[:8], sep="\n  ")
        clip = {"x": 0, "y": 0, "width": W, "height": H}
        if a.stills is not None:
            for t in a.stills:
                pg.evaluate("t => window.renderAtAsync(t)", t)
                f = rd / f"still_{t:06.2f}.jpg"
                pg.screenshot(path=str(f), type="jpeg", quality=90, clip=clip)
                print(f)
            br.close()
            return
        t1 = a.t1 if a.t1 is not None else tl["duration"]
        n = int(round((t1 - a.t0) * fps))
        out = Path(a.out) if a.out else rd / ("preview.mp4" if a.preview else "video.mp4")
        if overlay:
            basef = rd / "base.mp4"
            if not basef.exists():
                build_base(tl, rd)
            ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a.t0:.6f}", "-t", f"{(t1 - a.t0):.6f}", "-i", str(basef),
                                   "-f", "image2pipe", "-c:v", "png", "-framerate", str(fps), "-i", "-",
                                   "-filter_complex", f"[1:v]scale={W}:{H}[o];[0:v][o]overlay=0:0:shortest=1,format=yuv420p",
                                   "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(fps), str(out)], stdin=subprocess.PIPE)
        else:
            ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "18" if not a.preview else "24", "-pix_fmt", "yuv420p",
                               "-vf", f"scale={W}:{H}" if a.preview else "null", "-r", str(fps), str(out)], stdin=subprocess.PIPE)
        t_start = time.time()
        for i in range(n):
            t = a.t0 + i / fps
            pg.evaluate("t => window.renderAtAsync(t)", t)
            ff.stdin.write(pg.screenshot(type="png", omit_background=True, clip=clip) if overlay else pg.screenshot(type="jpeg", quality=a.quality, clip=clip))
            if i % (fps * 5) == 0:
                el = time.time() - t_start
                print(f"  {t:6.1f}s / {t1:.1f}s  ({i}/{n} khung, {el:.0f}s)", flush=True)
        ff.stdin.close()
        ff.wait()
        br.close()
        if msgs:
            print("Cảnh báo engine:", *msgs[:8], sep="\n  ")
        print(f"Xong: {out}  ({n} khung, {time.time() - t_start:.0f}s, {info})")


def needs_overlay(tl) -> bool:
    return any(sc.get("module") == "letterbox" for sc in tl["scenes"])


def build_base(tl, rd: Path) -> Path:
    """Lớp nền: clip của các cảnh letterbox đặt vào khung giữa (FFmpeg, chính xác từng khung), còn lại màu đen."""
    W, H, fps = tl["W"], tl["H"], tl.get("fps", 30)
    vh = round(W * 9 / 16)
    segs = []
    for i, sc in enumerate(tl["scenes"]):
        d = sc["end"] - sc["start"]
        f = rd / f"_base{i:02d}.mp4"
        p = sc.get("p") or {}
        if sc.get("module") == "letterbox" and p.get("video"):
            src = p["video"].replace("file:///", "").replace("%20", " ")
            from urllib.parse import unquote
            src = unquote(p["video"][8:] if p["video"].startswith("file:///") else p["video"])
            r_ = float(p.get("rate", 1)); cs = float(p.get("clip_start", 0))
            top = round((H - vh) / 2 + float(p.get("offset_y", 0)) * H)
            z = float(p.get("zoom_to", 1.09))
            vf = (f"trim=start={cs}:duration={d * r_ + 0.2},setpts=(PTS-STARTPTS)/{r_},fps={fps},"
                  f"scale={round(W * z / 2) * 2}:-2,crop={W}:{vh},tpad=stop_mode=clone:stop_duration=3,trim=duration={d},"
                  f"pad={W}:{H}:0:{top}:black")
            tr = sc.get("transition_in")
            if tr in ("fade", "black", "zoom", "whip") and i:
                vf += f",fade=t=in:st=0:d={0.6 if tr == 'black' else 0.38}"
            cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                   "-pix_fmt", "yuv420p", "-r", str(fps), str(f)]
        else:
            cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={fps}:d={d}", "-c:v", "libx264",
                   "-preset", "veryfast", "-pix_fmt", "yuv420p", str(f)]
        subprocess.run(cmd, check=True)
        segs.append(f)
    lst = rd / "_base.txt"
    lst.write_text("".join(f"file '{x.as_posix()}'\n" for x in segs), encoding="utf-8")
    out = rd / "base.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    for x in segs:
        x.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    return out


def parallel(a) -> None:
    """Chia video thành a.jobs đoạn, mỗi đoạn một Chromium riêng chạy cùng lúc, rồi nối lại (không nén lại)."""
    proj = Path(a.project).resolve()
    rd = proj / "render"
    tl = json.loads((rd / "timeline.json").read_text(encoding="utf-8"))
    fps = 15 if a.preview else tl.get("fps", 30)
    t1 = a.t1 if a.t1 is not None else tl["duration"]
    n = int(round((t1 - a.t0) * fps))
    cuts = [a.t0 + round(n * i / a.jobs) / fps for i in range(a.jobs + 1)]
    parts, procs = [], []
    t_start = time.time()
    if needs_overlay(tl):
        build_base(tl, rd)
    for i in range(a.jobs):
        part = rd / f"_part{i}.mp4"
        parts.append(part)
        cmd = [sys.executable, __file__, str(proj), "--from", f"{cuts[i]:.6f}", "--to", f"{cuts[i + 1]:.6f}", "--out", str(part),
               "--jobs", "1", "--quality", str(a.quality)] + (["--preview"] if a.preview else [])
        procs.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"))
    print(f"Render {a.jobs} luồng song song: {n} khung…", flush=True)
    bad = [p.communicate()[1][-400:] for p in procs if p.wait() != 0]
    if bad:
        sys.exit("Lỗi render:\n" + "\n".join(bad))
    lst = rd / "_parts.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = rd / ("preview.mp4" if a.preview else "video.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    for p in parts:
        p.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    (rd / "base.mp4").unlink(missing_ok=True)
    print(f"Xong: {out}  ({n} khung, {time.time() - t_start:.0f}s, {a.jobs} luồng)")


if __name__ == "__main__":
    main()
