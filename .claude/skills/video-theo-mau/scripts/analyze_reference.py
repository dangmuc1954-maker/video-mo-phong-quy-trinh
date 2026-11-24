"""Tải + phân tích một video mẫu (link TikTok/YouTube/Facebook/Instagram… hoặc file có sẵn).

python analyze_reference.py <link hoặc đường dẫn file> projects/<slug> [--max-shots 24] [--no-transcribe]

Ghi vào projects/<slug>/0-mau/:
  video.mp4          video mẫu
  info.json          tiêu đề, mô tả, kênh, lượt xem… (nếu tải từ link)
  analysis.json      số liệu: tỉ lệ khung, thời lượng, danh sách cảnh (shot), nhịp cắt, lời thoại
  keyframes.jpg      ảnh tổng hợp khung giữa mỗi cảnh, có số thứ tự + mốc giây → để Claude xem bằng mắt
Sau đó Claude đọc 3 file này, viết 0-mau/phan_tich.md và storyboard theo skill tao-video.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
FF, FP = shutil.which("ffmpeg"), shutil.which("ffprobe")


def run(a):
    return subprocess.run(a, capture_output=True, text=True, errors="ignore")


def download(src, out_dir, cookies=None):
    dst = os.path.join(out_dir, "video.mp4")
    if os.path.isfile(src):
        shutil.copy2(src, dst)
        return dst, {"source": os.path.abspath(src)}
    import yt_dlp
    opts = {"outtmpl": os.path.join(out_dir, "video.%(ext)s"), "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
            "merge_output_format": "mp4", "quiet": True, "no_warnings": True, "noplaylist": True}
    if cookies:  # chỉ dùng khi anh đồng ý (video cần đăng nhập)
        opts["cookiesfrombrowser"] = (cookies,)
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(src, download=True)
    keep = ["title", "description", "uploader", "channel", "duration", "view_count", "like_count", "comment_count",
            "upload_date", "tags", "webpage_url", "extractor", "width", "height", "fps"]
    meta = {k: info.get(k) for k in keep if info.get(k) is not None}
    if not os.path.isfile(dst):  # đôi khi ra .webm/.mkv
        for f in os.listdir(out_dir):
            if f.startswith("video."):
                run([FF, "-y", "-v", "error", "-i", os.path.join(out_dir, f), "-c", "copy", dst])
                break
    return dst, meta


def probe(p):
    j = json.loads(run([FP, "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", p]).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    n, d = v["r_frame_rate"].split("/")
    return {"width": v["width"], "height": v["height"], "fps": round(int(n) / max(int(d), 1), 2),
            "duration": round(float(j["format"]["duration"]), 2),
            "has_audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def shots(p, dur):
    """Dò điểm cắt cảnh. Ưu tiên PySceneDetect (bắt cả chuyển cảnh mềm), không có thì dùng ffmpeg."""
    try:
        from scenedetect import detect, AdaptiveDetector
        sc = detect(p, AdaptiveDetector(min_scene_len=15))
        cuts = [0.0] + [round(s.get_seconds(), 2) for s, _ in sc[1:]] + [round(dur, 2)]
    except Exception:
        err = run([FF, "-hide_banner", "-nostats", "-i", p, "-vf", "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"]).stderr
        raw = sorted(float(x) for x in re.findall(r"pts_time:([\d.]+)", err))
        cuts = [0.0]
        for c in raw:
            if c - cuts[-1] >= 0.5 and dur - c >= 0.4:
                cuts.append(round(c, 2))
        cuts.append(round(dur, 2))
    return [{"i": k + 1, "start": a, "end": b, "dur": round(b - a, 2)} for k, (a, b) in enumerate(zip(cuts, cuts[1:]))]


def keyframes(p, sh, out_jpg, w, h, max_n):
    step = max(1, len(sh) // max_n + (len(sh) % max_n > 0))
    pick = sh[::step][:max_n]
    tw = 360 if w >= h else 200
    tmp = []
    for s in pick:
        t = (s["start"] + s["end"]) / 2
        f = out_jpg + f".{s['i']}.jpg"
        label = f"{s['i']}  {s['start']:.1f}s ({s['dur']:.1f}s)"
        run([FF, "-y", "-v", "error", "-ss", str(t), "-i", p, "-frames:v", "1", "-vf",
             f"scale={tw}:-2,drawbox=y=0:w=iw:h=26:color=black@0.6:t=fill,"
             f"drawtext=text='{label}':x=6:y=5:fontsize=16:fontcolor=yellow:fontfile=C\\\\:/Windows/Fonts/arial.ttf", f])
        if os.path.exists(f):
            tmp.append(f)
    cols = 4 if w >= h else 6
    rows = (len(tmp) + cols - 1) // cols
    inputs = sum([["-i", f] for f in tmp], [])
    layout = "|".join(("0" if k % cols == 0 else "+".join(["w0"] * (k % cols))) + "_" +
                      ("0" if k // cols == 0 else "+".join(["h0"] * (k // cols))) for k in range(len(tmp)))
    if len(tmp) == 1:
        shutil.copy2(tmp[0], out_jpg)
    else:
        run([FF, "-y", "-v", "error", *inputs, "-filter_complex",
             f"{''.join(f'[{k}]' for k in range(len(tmp)))}xstack=inputs={len(tmp)}:layout={layout}:fill=black", out_jpg])
    for f in tmp:
        os.remove(f)
    return [s["i"] for s in pick]


def transcribe(p):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"language": None, "segments": [], "note": "chưa cài faster-whisper"}
    try:
        m = WhisperModel("small", device="cuda", compute_type="float16")
        segs, info = m.transcribe(p, vad_filter=True)
        segs = list(segs)
    except Exception:
        m = WhisperModel("small", device="cpu", compute_type="int8")
        segs, info = m.transcribe(p, vad_filter=True)
        segs = list(segs)
    return {"language": info.language, "segments": [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segs if s.no_speech_prob < 0.6 and s.text.strip()]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("project_dir")
    ap.add_argument("--max-shots", type=int, default=24)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--cookies-from", help="tên trình duyệt (chrome/edge) để mượn đăng nhập — chỉ khi anh cho phép")
    a = ap.parse_args()
    out = os.path.join(a.project_dir, "0-mau")
    os.makedirs(out, exist_ok=True)

    print("Tải video mẫu…")
    vid, meta = download(a.source, out, a.cookies_from)
    json.dump(meta, open(os.path.join(out, "info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    pr = probe(vid)
    aspect = "9:16" if pr["height"] > pr["width"] * 1.2 else ("16:9" if pr["width"] > pr["height"] * 1.2 else "1:1")
    sh = shots(vid, pr["duration"])
    lens = sorted(s["dur"] for s in sh)
    pick = keyframes(vid, sh, os.path.join(out, "keyframes.jpg"), pr["width"], pr["height"], a.max_shots)
    tr = {"language": None, "segments": []} if a.no_transcribe or not pr["has_audio"] else transcribe(vid)
    speech = sum(s["end"] - s["start"] for s in tr["segments"])

    res = {"source": a.source, "meta": meta, **pr, "aspect": aspect,
           "shot_count": len(sh), "avg_shot": round(sum(lens) / len(lens), 2) if lens else None,
           "median_shot": lens[len(lens) // 2] if lens else None, "keyframe_shots": pick, "shots": sh,
           "speech_ratio": round(speech / pr["duration"], 2) if pr["duration"] else 0, "transcript": tr}
    json.dump(res, open(os.path.join(out, "analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"Video mẫu: {meta.get('title', os.path.basename(a.source))}")
    print(f"{pr['width']}x{pr['height']} ({aspect}), {pr['duration']}s, {pr['fps']}fps, âm thanh: {pr['has_audio']}")
    print(f"{len(sh)} cảnh, trung bình {res['avg_shot']}s/cảnh (trung vị {res['median_shot']}s)")
    print(f"Lời nói chiếm {res['speech_ratio']:.0%} thời lượng, ngôn ngữ: {tr.get('language')}")
    for s in tr["segments"][:12]:
        print(f"  {s['start']:>6.1f}s  {s['text']}")
    print(f"→ {out}\\analysis.json, keyframes.jpg")


if __name__ == "__main__":
    main()
