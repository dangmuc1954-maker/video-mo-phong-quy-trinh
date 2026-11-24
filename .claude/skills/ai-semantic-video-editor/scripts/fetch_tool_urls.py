"""Dự phòng cho tool_jobs.py collect: cảnh đã "Completed" trong AI VIDEO LIBRARY nhưng tool chưa lưu file ra máy
(thường là bản chưa xoá logo) → tải thẳng bản 1080p từ link gốc trong queue-state.json (chỉ ĐỌC dữ liệu của tool).

  python fetch_tool_urls.py projects/<slug>/storyboard.json

Sau khi tải: kiểm tra góc dưới phải có logo ngôi sao Gemini không; có thì phóng khung 12% về trên trái để đẩy logo ra ngoài:
  ffmpeg -i in.mp4 -vf "crop=iw/1.12:ih/1.12:0:0,scale=W:H:flags=lanczos" out.mp4
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path


def jobs_in(o):
    if isinstance(o, dict):
        if str(o.get("id", "")).startswith("job-") and "result" in o:
            yield o
        for v in o.values():
            yield from jobs_in(v)
    elif isinstance(o, list):
        for v in o:
            yield from jobs_in(v)


def main() -> None:
    sp = Path(sys.argv[1]).resolve()
    proj = sp.parent
    tj = json.loads((proj / "tool_jobs.json").read_text(encoding="utf-8"))
    q = json.loads((Path(os.environ["APPDATA"]) / "AI_VIDEO_LIBRARY_DATA" / "queue-state.json").read_text(encoding="utf-8"))
    by = {j["id"]: j for j in jobs_in(q)}
    out = proj / "1-canh"
    out.mkdir(exist_ok=True)
    for sid, info in sorted(tj.items(), key=lambda x: int(x[0])):
        f = out / f"scene_{int(sid):02d}.mp4"
        if f.exists():
            continue
        job = by.get(info.get("job"))
        if not job or job.get("status") != "Completed":
            print(f"Cảnh {sid}: chưa xong ({job.get('status') if job else 'không thấy job'})")
            continue
        assets = [a for a in (job.get("result") or {}).get("assets", []) if a.get("type") == "video" and a.get("url")]
        if not assets:
            print(f"Cảnh {sid}: không có link")
            continue
        a = sorted(assets, key=lambda a: a.get("resolution") == "1080p", reverse=True)[0]
        data = urllib.request.urlopen(urllib.request.Request(a["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
        f.write_bytes(data)
        info.update({"file": str(f), "src": a["url"][:80] + "…", "resolution": a.get("resolution"), "via": "url"})
        print(f"✓ Cảnh {sid} → {f.name} ({len(data) // 1024} KB, {a.get('resolution')}) — KIỂM TRA logo góc dưới phải")
    (proj / "tool_jobs.json").write_text(json.dumps(tj, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
