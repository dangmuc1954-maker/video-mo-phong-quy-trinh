"""MỘT lệnh chạy cả chuỗi dựng video tài liệu, tự dừng ở cổng kiểm (in STOP + việc cần làm).

  python pipeline.py projects/<slug> check     # timeline + qa_layout + rule_check (nhanh, chạy sau MỖI lần sửa storyboard)
  python pipeline.py projects/<slug> stills 12.5 40 88   # ảnh khung để tự xem (Read) trước khi render
  python pipeline.py projects/<slug> render    # check → render full → bản FFmpeg 2-xuat/  (lâu: chạy nền)
  python pipeline.py projects/<slug> capcut    # draft hậu kỳ + SFX + nhạc + kiểm SFX (CapCut phải TẮT)
  python pipeline.py projects/<slug> review    # tờ ảnh kiểm cuối → giao agent MỚI soát (kiem-cuoi.md)
  python pipeline.py projects/<slug> finish    # sau khi xuất CapCut: chặn đỉnh âm → 2-xuat/<title> (hau ky).mp4

Mọi bước in một dòng cuối: "OK: …" (đi tiếp) hoặc "STOP: …" (sửa theo hướng dẫn rồi chạy lại đúng bước đó).
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
V = Path(__file__).resolve().parent
A = V.parents[1] / "ai-semantic-video-editor" / "scripts"
PY = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def sh(args: list, tail: int = 25) -> tuple[int, str]:
    r = subprocess.run([PY, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    out = (r.stdout or "") + (r.stderr or "")
    print("\n".join(out.strip().splitlines()[-tail:]))
    return r.returncode, out


def stop(msg: str) -> None:
    print(f"\nSTOP: {msg}")
    sys.exit(1)


def check(proj: Path) -> None:
    print("== 1/3 plan_timeline")
    rc, out = sh([V / "plan_timeline.py", proj / "storyboard.json"], 40)
    if rc:
        stop("plan_timeline lỗi — đọc lỗi ở trên, sửa storyboard.json.")
    print("== 2/3 qa_layout (chữ đè / tràn / nhỏ / che bằng chứng)")
    rc, out = sh([V / "qa_layout.py", proj])
    if rc:
        stop("qa_layout báo lỗi bố cục — xem ảnh render/qa_*.jpg, sửa pos/x/w/size/side trong storyboard rồi chạy lại 'check'.")
    print("== 3/3 rule_check (bộ luật dựng)")
    rc, out = sh([V / "rule_check.py", proj], 40)
    bad = [l for l in out.splitlines() if "✗" in l and "P2" not in l]
    if bad:
        stop("vi phạm luật dựng: " + "; ".join(b.strip("- *") for b in bad) + " — sửa storyboard (hoặc ghi lý do vào rule_notes) rồi chạy lại 'check'.")
    print("(P2 'kiểm cuối độc lập' luôn ✗ ở bước này — bình thường, làm ở bước 'review'.)")
    print("\nOK: check xong — được render.")


def capcut_running() -> bool:
    if os.name != "nt":
        return False
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True, errors="replace")
    return "CapCut.exe" in r.stdout


def title_of(proj: Path) -> str:
    tl = json.loads((proj / "render" / "timeline.json").read_text(encoding="utf-8"))
    return tl.get("title") or proj.name


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    proj, stage, rest = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3:]
    if not (proj / "storyboard.json").exists():
        stop(f"không thấy {proj / 'storyboard.json'}")
    if stage == "check":
        check(proj)
    elif stage == "stills":
        rc, _ = sh([V / "render_html.py", proj, "--stills", *rest], 30)
        print("\nOK: xem các ảnh render/still_*.jpg bằng Read." if not rc else "\nSTOP: render ảnh lỗi.")
    elif stage == "render":
        check(proj)
        print("== render full (lâu: ~4–5 giây máy cho 1 giây video)")
        rc, _ = sh([V / "render_html.py", proj, "--jobs", "4"], 5)
        if rc:
            stop("render_html lỗi.")
        rc, _ = sh([V / "compose.py", proj], 5)
        if rc:
            stop("compose lỗi.")
        print("\nOK: render xong (render/video.mp4 + bản FFmpeg trong 2-xuat/). Bước sau: 'capcut'.")
    elif stage == "capcut":
        if capcut_running():
            stop("CapCut đang mở — HỎI ANH cho tắt (không tự tắt), rồi chạy lại 'capcut'.")
        rc, _ = sh([V / "compose.py", proj, "--capcut"], 6)
        if rc:
            stop("compose --capcut lỗi.")
        rc, _ = sh([V / "capcut_sfx_auto.py", proj], 4)
        if rc:
            stop("capcut_sfx_auto dừng — đọc lý do ở trên.")
        rc, out = sh([A / "capcut_sfx_check.py", proj / "storyboard.json", "--title", f"{title_of(proj)} (hau ky)"], 6)
        last = out.strip().splitlines()[-1] if out.strip() else ""
        if not last.startswith("OK"):
            stop("capcut_sfx_check chưa OK — xem danh sách lệch ở trên.")
        print(f"\nOK: draft '{title_of(proj)} (hau ky)' sẵn sàng. Bước sau: 'review', rồi mở CapCut xuất (Xuất → Xuất, 1080p).")
    elif stage == "review":
        rc, _ = sh([V / "review_sheet.py", proj], 5)
        rp = proj / "render" / "review_report.md"
        if rp.exists():
            rp.rename(rp.with_name("review_report_old.md"))
        print(f"""
OK: tờ ảnh sẵn sàng. Giao một agent MỚI (Agent tool, chạy nền) với lời nhắn:
  "Bạn là người kiểm cuối độc lập. Đọc {V.parent / 'references' / 'kiem-cuoi.md'} và {V.parent / 'references' / 'luat-dung.md'},
   rồi {proj / 'render' / 'review' / 'brief.md'} và mọi sheet_*.jpg trong thư mục đó (Read). Ghi báo cáo tiếng Việt vào
   {rp}: lỗi chắc kèm cảnh/giây, mục cần xem video, dòng cuối đúng một trong hai: 'KẾT LUẬN: ĐẠT' / 'KẾT LUẬN: CẦN SỬA'. Không sửa file nào khác."
CẦN SỬA → sửa storyboard → 'render' → 'capcut' → 'review' lại (agent mới).""")
    elif stage == "finish":
        rp = proj / "render" / "review_report.md"
        if not rp.exists() or "KẾT LUẬN: ĐẠT" not in rp.read_text(encoding="utf-8"):
            stop("kiểm cuối chưa ĐẠT — chạy 'review' và sửa đến khi ĐẠT.")
        t = title_of(proj)
        cands = sorted(glob.glob(str(Path.home() / "Downloads" / f"{glob.escape(t)} (hau ky)*.mp4")), key=os.path.getmtime)
        if not cands:
            stop(f"chưa thấy file xuất '{t} (hau ky)*.mp4' trong Downloads — mở CapCut, mở project '{t} (hau ky)', bấm Xuất → Xuất, chờ xong.")
        src, dst = cands[-1], proj / "2-xuat" / f"{t} (hau ky).mp4"
        dst.parent.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "copy", "-af",
                        "alimiter=limit=0.89:level=disabled:attack=5:release=80,aresample=48000", "-c:a", "aac", "-b:a", "256k",
                        "-movflags", "+faststart", str(dst)], check=True)
        r = subprocess.run(["ffmpeg", "-i", str(dst), "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True, errors="replace")
        vol = [l.split("] ")[-1] for l in r.stderr.splitlines() if "mean_volume" in l or "max_volume" in l]
        print(f"\nOK: {dst}  ({', '.join(vol)}). Gửi anh file này + 2-xuat/thumbnail_*.jpg (SendUserFile).")
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
