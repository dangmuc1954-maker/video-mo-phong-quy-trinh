"""timeline.json -> final video with FFmpeg.

Usage:
  python render.py timeline.json [--preview] [--no-subs] [--no-mograph] [-o build/final.mp4]
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_subs import build_subs  # noqa: E402
from mograph import render_mograph  # noqa: E402
from validate_timeline import validate  # noqa: E402
from vse_common import find_font, need, run  # noqa: E402


def even(x):
    return int(x) // 2 * 2


def placeholder(asset: dict, W: int, H: int, out: Path, font_path: str) -> Path:
    img = Image.new("RGB", (W, H), (18, 22, 34))
    d = ImageDraw.Draw(img)
    for y in range(H):  # soft vertical gradient
        c = int(18 + 30 * y / H)
        d.line((0, y, W, y), fill=(c, c + 4, c + 18))
    k = W / 1080
    f1 = ImageFont.truetype(font_path, int(64 * k))
    f2 = ImageFont.truetype(font_path, int(36 * k))
    d.text((W // 2, int(H * 0.30)), f"THIẾU ẢNH: {asset['id']}", font=f1, fill=(250, 204, 21), anchor="mm")
    prompt = asset.get("prompt") or "(chưa có prompt)"
    y = int(H * 0.38)
    for line in textwrap.wrap(prompt, width=38)[:16]:
        d.text((int(80 * k), y), line, font=f2, fill=(220, 225, 235))
        y += int(50 * k)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def resolve_asset(asset, base, build, W, H, font_path, report) -> tuple[Path, str]:
    f = asset.get("file")
    if f and (base / f).exists():
        p = base / f
        kind = asset.get("kind") or ("video" if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv") else "image")
        return p, kind
    # try assets/<id>.* automatically
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm"):
        p = base / "assets" / f"{asset['id']}{ext}"
        if p.exists():
            return p, ("video" if ext in (".mp4", ".mov", ".webm") else "image")
    report["placeholders"].append(asset["id"])
    return placeholder(asset, W, H, build / "placeholders" / f"{asset['id']}.png", font_path), "image"


def scene_segment(src: Path, kind: str, motion: str, frames: int, W, H, fps, out: Path, enc: list, up: float,
                  source_start: float = 0.0, speed: float = 1.0):
    d = frames / fps
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    if kind == "video":
        # speed < 1 = slow motion so a short clip fills the narration slot; tpad freezes the last frame if still short
        vf = f"setpts=(PTS-STARTPTS)/{speed:.5f},{cover},fps={fps},tpad=stop_mode=clone:stop_duration={d:.3f},format=yuv420p"
        loop = [] if speed != 1.0 or source_start else ["-stream_loop", "-1"]
        run(["ffmpeg", "-y", *loop, "-ss", f"{source_start:.3f}", "-i", src, "-an", "-vf", vf,
             "-frames:v", frames, *enc, out])
        return
    bw, bh = even(W * up), even(H * up)
    N = max(frames, 1)
    z0, z1 = 1.0, 1.0
    x = "iw/2-(iw/zoom/2)"
    y = "ih/2-(ih/zoom/2)"
    if motion == "push_in":
        z0, z1 = 1.0, 1.18
    elif motion == "pull_out":
        z0, z1 = 1.18, 1.0
    elif motion in ("pan_left", "pan_right", "pan_up", "pan_down"):
        z0 = z1 = 1.15
        prog = f"(on/{N})"
        if motion == "pan_left":
            x = f"(iw-iw/zoom)*(1-{prog})"
        elif motion == "pan_right":
            x = f"(iw-iw/zoom)*{prog}"
        elif motion == "pan_up":
            y = f"(ih-ih/zoom)*(1-{prog})"
        else:
            y = f"(ih-ih/zoom)*{prog}"
    z = f"{z0}+({z1 - z0})*on/{N}"
    vf = (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},setsar=1,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={N}:s={W}x{H}:fps={fps},format=yuv420p")
    run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-frames:v", frames, *enc, out])


def anchor_xy(anchor: str, w: int, h: int, W: int, H: int) -> tuple[int, int]:
    mx = int(W * 0.05)
    a = anchor or "top"
    if a == "top":
        return (W - w) // 2, int(H * 0.08)
    if a == "center":
        return (W - w) // 2, (H - h) // 2
    if a == "upper_left":
        return mx, int(H * 0.08)
    if a == "upper_right":
        return W - w - mx, int(H * 0.08)
    if a == "middle_left":
        return mx, max(0, int(H * 0.45) - h // 2)
    if a == "middle_right":
        return W - w - mx, max(0, int(H * 0.45) - h // 2)
    if a == "lower_third":
        return (W - w) // 2, max(0, min(int(H * 0.50), int(H * 0.70) - h))
    return (W - w) // 2, int(H * 0.08)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("-o", "--out")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--no-mograph", action="store_true")
    ap.add_argument("--capcut-layers", action="store_true",
                    help="cho hậu kỳ CapCut: chỉ xuất các cảnh đã cắt (segments/) + LỚP CHỮ trong suốt (sub + graphic), không ghép")
    args = ap.parse_args()
    need("ffmpeg")

    tl_path = Path(args.timeline).resolve()
    base = tl_path.parent
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    E, Wn = validate(tl, base)
    for w in Wn:
        print(f"CẢNH BÁO: {w}")
    if E:
        for e in E:
            print(f"LỖI: {e}")
        sys.exit("Timeline có lỗi, hãy sửa trước khi render (validate_timeline.py).")

    pr, sb = tl["project"], tl.get("style_bible", {})
    mode = tl["mode"]
    sf = 0.5 if args.preview else 1.0
    W, H, fps = even(pr["width"] * sf), even(pr["height"] * sf), pr["fps"]
    dur = float(pr["duration_seconds"])
    total_frames = int(round(dur * fps))
    palette = sb.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"]
    font_name = sb.get("font", "Roboto")
    font_path = str(find_font(font_name))
    build = base / "build" / ("preview" if args.preview else "final")
    build.mkdir(parents=True, exist_ok=True)
    out = Path(args.out).resolve() if args.out else base / "build" / ("preview.mp4" if args.preview else "final.mp4")
    enc = (["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p", "-r", str(fps)]
           if args.preview else
           ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps)])
    report = {"placeholders": [], "graphics": [], "output": str(out)}
    assets = {a["id"]: a for a in tl.get("assets", [])}
    layers = tl.get("layers", [])

    # ---------- 1. base video ----------
    base_mp4 = build / "base.mp4"
    if mode == "STORYTELLING":
        scenes = sorted([L for L in layers if L["type"] == "scene"], key=lambda L: L["start"])
        seg_dir = build / "segments"
        seg_dir.mkdir(exist_ok=True)
        segs = []
        # soft transition INTO scene i+1 (FFmpeg xfade). The outgoing segment is rendered XF frames longer and the
        # transition starts exactly at the scene boundary, so total length and voice sync stay unchanged.
        xf = [None] + [(sc.get("xfade") or None) for sc in scenes[1:]]
        XF = [int(round(float(sc.get("xfade_dur", 0.5)) * fps)) if sc.get("xfade") else 0 for sc in scenes]
        for i, L in enumerate(scenes):
            f0 = int(round(L["start"] * fps))
            f1 = total_frames if i == len(scenes) - 1 else int(round(scenes[i + 1]["start"] * fps))
            if i + 1 < len(scenes) and not args.capcut_layers:
                f1 += XF[i + 1]
            src, kind = resolve_asset(assets[L["asset_id"]], base, build, W, H, font_path, report)
            seg = seg_dir / f"seg_{i:03d}.mp4"
            print(f"Cảnh {i + 1}/{len(scenes)}: {L['id']} ({kind}, {L.get('motion', 'static')}, {(f1 - f0) / fps:.2f}s)")
            scene_segment(src, kind, L.get("motion") or "static", f1 - f0, W, H, fps, seg, enc,
                          1.5 if args.preview else 2.0, float(L.get("source_start", 0)), float(L.get("speed", 1.0)))
            segs.append(seg)
        lst = build / "segments.txt"
        lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
        if not args.capcut_layers and not any(xf):
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base_mp4])
        elif not args.capcut_layers:
            lens = []
            for i, L in enumerate(scenes):
                f0 = int(round(L["start"] * fps))
                f1 = total_frames if i == len(scenes) - 1 else int(round(scenes[i + 1]["start"] * fps))
                lens.append((f1 - f0) / fps)
            # same timebase for every input, otherwise xfade refuses to link after a concat
            parts = [f"[{i}:v]fps={fps},settb=AVTB,setpts=PTS-STARTPTS[s{i}]" for i in range(len(segs))]
            cur, acc = "[s0]", 0.0
            for i in range(1, len(segs)):
                acc += lens[i - 1]
                if xf[i]:
                    parts.append(f"{cur}[s{i}]xfade=transition={xf[i]}:duration={XF[i] / fps:.3f}:offset={acc:.3f}[x{i}]")
                else:   # straight cut
                    parts.append(f"{cur}[s{i}]concat=n=2:v=1:a=0,settb=AVTB[x{i}]")
                cur = f"[x{i}]"
            parts.append(f"{cur}format=yuv420p[vb]")
            graph = build / "filter_graph_xfade.txt"
            graph.write_text((";" + chr(10)).join(parts), encoding="utf-8")
            cmd = ["ffmpeg", "-y"]
            for sg in segs:
                cmd += ["-i", sg]
            cmd += ["-/filter_complex", graph.name, "-map", "[vb]", *enc, base_mp4]
            print(f"Ghép cảnh có {sum(1 for x in xf if x)} chuyển cảnh mềm…")
            run(cmd, cwd=build)
    else:
        src = base / pr["source_video"]
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps},format=yuv420p"
        print("Chuẩn hóa video gốc…")
        run(["ffmpeg", "-y", "-i", src, "-t", f"{dur:.4f}", "-an", "-vf", vf, *enc, base_mp4])

    # ---------- 2. overlays (broll, mograph, overlay) ----------
    inputs: list[list] = ([["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={fps}:d={dur:.4f},format=rgba"]]
                          if args.capcut_layers else [["-i", base_mp4]])
    chain, last = [], "[0:v]"
    idx = 1

    def add_overlay(inp_args, prep, x, y, s, e, tag):
        nonlocal idx, last
        inputs.append(inp_args)
        chain.append(f"[{idx}:v]{prep}setpts=PTS-STARTPTS+{s:.4f}/TB[ov{idx}]")
        chain.append(f"{last}[ov{idx}]overlay=x={x}:y={y}:enable='between(t,{s:.4f},{e:.4f})':eof_action=pass[v{idx}]")
        last = f"[v{idx}]"
        idx += 1

    for L in sorted(layers, key=lambda L: L["start"]):
        s, e = float(L["start"]), float(L["end"])
        if L["type"] == "broll" and args.capcut_layers:
            continue
        if L["type"] == "broll":
            src, kind = resolve_asset(assets[L["asset_id"]], base, build, W, H, font_path, report)
            cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps},format=yuva420p,"
            if kind == "video":
                add_overlay(["-stream_loop", "-1", "-t", f"{e - s:.4f}", "-i", src], cover, 0, 0, s, e, L["id"])
            else:
                add_overlay(["-loop", "1", "-t", f"{e - s:.4f}", "-i", src], cover, 0, 0, s, e, L["id"])
        elif L["type"] == "overlay":
            src, kind = resolve_asset(assets[L["asset_id"]], base, build, W, H, font_path, report)
            ow = even(W * float(L.get("scale", 0.4)))
            cx, cy = float(L.get("x", 0.5)) * W, float(L.get("y", 0.3)) * H
            prep = f"scale={ow}:-2,format=yuva420p,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0, e - s - 0.25):.3f}:d=0.25:alpha=1,"
            loop = ["-stream_loop", "-1"] if kind == "video" else ["-loop", "1"]
            add_overlay([*loop, "-t", f"{e - s:.4f}", "-i", src], prep, f"{cx:.0f}-overlay_w/2", f"{cy:.0f}-overlay_h/2", s, e, L["id"])
        elif L["type"] == "mograph" and not args.no_mograph:
            gpath = build / "graphics" / f"{L['id']}.mov"
            spec = {"template": L["template"], "data": L.get("data", {}), "duration": e - s, "width": W,
                    "height": H, "fps": fps, "palette": palette, "font": font_name, "time_offset": s}
            print(f"Graphic {L['id']} ({L['template']}, {e - s:.2f}s)")
            info = render_mograph(spec, gpath)
            x, y = (0, 0) if info["full_frame"] else anchor_xy(L.get("anchor"), info["width"], info["height"], W, H)
            report["graphics"].append({"id": L["id"], "file": str(gpath), "start": s, "end": e, "x": x, "y": y})
            add_overlay(["-i", gpath], "", x, y, s, e, L["id"])

    # ---------- 3. subtitles ----------
    if not args.no_subs and tl.get("words"):
        kws = sorted({k for b in tl.get("beats", []) for k in b.get("keywords", [])})
        build_subs(tl["words"], build / "subs", sb.get("subtitle_preset", "clean"), W, H, font_name,
                   palette[2] if len(palette) > 2 else "#FACC15", kws, bool(sb.get("subtitle_uppercase")))
        chain.append(f"{last}ass=subs.ass:fontsdir=fonts{':alpha=1' if args.capcut_layers else ''}[vsub]")
        last = "[vsub]"

    if args.capcut_layers:
        chain.append(f"{last}format=yuva444p10le[vout]")
        layer = build / "text_layer.mov"
        graph = build / "filter_graph_layer.txt"
        graph.write_text((";" + chr(10)).join(chain), encoding="utf-8")
        cmd = ["ffmpeg", "-y"]
        for inp in inputs:
            cmd += inp
        cmd += ["-/filter_complex", graph.name, "-map", "[vout]", "-t", f"{dur:.4f}", "-c:v", "prores_ks",
                "-profile:v", "4444", "-qscale:v", "12", "-pix_fmt", "yuva444p10le", "-vendor", "apl0", layer]
        print("Xuất lớp chữ trong suốt…")
        run(cmd, cwd=build)
        info = {"segments": [str(x) for x in sorted((build / "segments").glob("seg_*.mp4"))], "text_layer": str(layer),
                "duration": dur, "fps": fps, "width": W, "height": H}
        (build / "capcut_layers.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Xong lớp cho CapCut: {build / 'capcut_layers.json'}")
        return
    chain.append(f"{last}fade=t=in:st=0:d=0.3,fade=t=out:st={max(0, dur - 0.4):.3f}:d=0.4,format=yuv420p[vout]")

    # ---------- 4. audio ----------
    if mode == "STORYTELLING":
        inputs.append(["-i", base / pr["voice_audio"]])
    else:
        inputs.append(["-i", base / (pr.get("voice_audio") or pr["source_video"])])
    vi = idx
    idx += 1
    if pr.get("bgm"):
        inputs.append(["-stream_loop", "-1", "-i", base / pr["bgm"]])
        bi = idx
        idx += 1
        vol = float(pr.get("bgm_volume", 0.18))
        chain.append(f"[{vi}:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[voice][sc]")
        chain.append(f"[{bi}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={vol}[bgm]")
        chain.append("[bgm][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[duck]")
        chain.append(f"[voice][duck]amix=inputs=2:duration=first:normalize=0,atrim=0:{dur:.4f},"
                     f"afade=t=out:st={max(0, dur - 1):.3f}:d=1[aout]")
    else:
        chain.append(f"[{vi}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{dur:.4f}[aout]")

    graph = build / "filter_graph.txt"
    graph.write_text(";\n".join(chain), encoding="utf-8")
    cmd = ["ffmpeg", "-y"]
    for inp in inputs:
        cmd += inp
    cmd += ["-/filter_complex", graph.name, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{dur:.4f}", *enc, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print("Ghép video cuối…")
    out.parent.mkdir(parents=True, exist_ok=True)
    run(cmd, cwd=build)
    (build / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nXong: {out}")
    if report["placeholders"]:
        print(f"Còn {len(report['placeholders'])} asset dùng placeholder: {', '.join(report['placeholders'])}")


if __name__ == "__main__":
    main()
