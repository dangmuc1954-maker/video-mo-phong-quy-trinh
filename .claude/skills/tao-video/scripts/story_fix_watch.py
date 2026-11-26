"""Theo dõi chuỗi Studio Kịch Bản: sửa file cảnh vừa xong có HÌNH NGẮN HƠN TIẾNG (lỗi tool 26/11/2026:
bản xoá WM / upscale 1080p làm video kết thúc trước audio → 'assets:extractLastFrame' lỗi → cảnh sau không nối được,
bấm Tạo lại cũng không gửi). Cắt tiếng bằng hình (hình giữ nguyên), sao lưu bản gốc vào <proj>/_backup_asset/.
Anh cho phép chép đè file asset của cảnh trong chuỗi (26/11/2026).

python story_fix_watch.py "<Dự Án Kịch Bản N>" <số cảnh> <thư mục dự án>
In 1 dòng mỗi sự kiện: FIXED / OK / STALL (cảnh trước xong >90s mà cảnh sau chưa có job → Claude bấm Tạo lại) / DONE.
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
proj_name, n, proj = sys.argv[1], int(sys.argv[2]), sys.argv[3]
D = os.path.join(os.environ["APPDATA"], "AI_VIDEO_LIBRARY_DATA")
BK = os.path.join(proj, "_backup_asset")
os.makedirs(BK, exist_ok=True)
seen, stalled = set(), set()


def load(f):
    for _ in range(5):
        try:
            return json.load(open(os.path.join(D, f), encoding="utf-8"))
        except Exception:  # noqa: BLE001  (tool đang ghi file)
            time.sleep(0.3)
    return {}


def durs(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        t, v = (line.split(",") + [""])[:2]
        try:
            d[t] = float(v)
        except ValueError:
            pass
    return d


def scene_no(title):
    try:
        return int(title.split("Cảnh")[-1].strip().split()[0])
    except (ValueError, IndexError):
        return None


t_start = time.time()
done_at = {}
while True:
    jobs = [j for j in load("queue-state.json").get("jobs", []) if (j.get("title") or "").startswith(f"[{proj_name}]")
            and j.get("createdAt", "") >= time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t_start - 3 * 3600))]
    by = {}
    for j in jobs:
        k = scene_no(j["title"])
        if k and (k not in by or j.get("createdAt", "") > by[k].get("createdAt", "")):
            by[k] = j
    assets = load("asset-state.json").get("assets", [])
    for k, j in sorted(by.items()):
        if j.get("status") != "Completed" or (k, j["id"]) in seen:
            continue
        for a in assets:
            if j["id"] in json.dumps(a) and (a.get("localPath") or "").endswith(".mp4") and os.path.exists(a["localPath"]):
                p = a["localPath"]
                d = durs(p)
                v, au = d.get("video"), d.get("audio")
                if v and au and au - v > 0.03:
                    shutil.copy2(p, os.path.join(BK, f"canh{k}_{os.path.basename(p)}"))
                    tmp = os.path.join(os.environ["TEMP"], f"fix_story_{k}.mp4")
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p, "-map", "0", "-c:v", "copy", "-c:a", "aac",
                                    "-b:a", "192k", "-t", f"{v:.3f}", tmp], check=True)
                    shutil.copy2(tmp, p)
                    print(f"FIXED cảnh {k}: hình {v:.3f}s < tiếng {au:.3f}s → cắt tiếng bằng hình", flush=True)
                else:
                    print(f"OK cảnh {k} (hình {v}s, tiếng {au}s)", flush=True)
                seen.add((k, j["id"]))
                done_at[k] = time.time()
                break
    for k, t in done_at.items():
        if k < n and k + 1 not in by and k + 1 not in stalled and time.time() - t > 90:
            stalled.add(k + 1)
            print(f"STALL cảnh {k + 1}: chưa gửi sau 90s — bấm Tạo lại ở thẻ Cảnh {k + 1}", flush=True)
        if k + 1 in by:
            stalled.discard(k + 1)
    if sum(1 for j in by.values() if j.get("status") == "Completed") >= n:
        print("DONE", flush=True)
        break
    failed = [k for k, j in by.items() if j.get("status") == "Failed" and (k, "F") not in seen]
    for k in failed:
        seen.add((k, "F"))
        print(f"FAILED cảnh {k}: {by[k].get('providerErrorCode')} {(by[k].get('statusText') or '')[:120]}", flush=True)
    time.sleep(0.5)
