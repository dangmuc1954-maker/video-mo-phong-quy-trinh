"""One-shot run of the tao-video macros: load prompts → OCR-check the button → generate → (collect).

Replaces the "Claude takes a screenshot and zooms on the button" step between the two macro phases,
which cost tens of seconds and many tokens each time. The check is done with Windows OCR instead:
the number on the button must equal the number of scenes, otherwise it STOPS without clicking.

  python auto_tool.py video projects/<slug>/storyboard.json [--model omni] [--dur 10] [--collect] [--wait 1500]
  python auto_tool.py story projects/<slug>/storyboard.json [--provider veo3] [--model omni] [--dur 10] [--collect]

video = Video AI page (tool_macro.py, independent scenes, upscale 1080p + remove watermark)
story = Studio Kịch Bản (tool_story_macro.py, chained scenes)
The tao-video scripts are only called, never modified.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAO = HERE.parent.parent / "tao-video" / "scripts"
sys.path.insert(0, str(TAO))
sys.path.insert(0, str(HERE))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import tool_macro as T  # noqa: E402
from screen_ocr import button_shows  # noqa: E402

BOX = {"video": (1490, 14, 1568, 32), "story": (1440, 72, 1556, 92)}
MACRO = {"video": "tool_macro.py", "story": "tool_story_macro.py"}


def run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip())
    return r.returncode, out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["video", "story"])
    ap.add_argument("storyboard")
    ap.add_argument("--model", default="omni")
    ap.add_argument("--dur", default="10")
    ap.add_argument("--provider", default="veo3")
    ap.add_argument("--collect", action="store_true", help="chờ và lấy clip về 1-canh/ sau khi tạo")
    ap.add_argument("--wait", type=int, default=1500)
    ap.add_argument("--frames", action="store_true", help="video: ảnh của cảnh (first_last) làm KHUNG ĐẦU — cho ảnh chuyển động")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    n = len(json.loads(sp.read_text(encoding="utf-8"))["scenes"])
    macro = str(TAO / MACRO[a.kind])
    extra = ["--model", a.model, "--dur", str(a.dur)] + (["--provider", a.provider] if a.kind == "story" else []) + (["--frames"] if a.frames and a.kind == "video" else [])

    t0 = time.time()
    code, out = run([macro, str(sp), *extra])
    if code != 0 or "STOP" in out:
        sys.exit("STOP: macro nạp prompt dừng — xem ảnh trong _macro/ rồi xử lý.")

    T.SHOTS = str(sp.parent / "_macro")
    T.focus_app(topmost=True)
    try:
        time.sleep(0.6)
        ok, text = button_shows(BOX[a.kind], n, save=str(sp.parent / "_macro" / "ocr_button.png"))
    finally:
        T.release_topmost()
    print(f"OCR nút: {text!r} → cần {n}: {'KHỚP' if ok else 'KHÔNG KHỚP'}")
    if not ok:
        sys.exit("STOP: số trên nút khác số cảnh (có thể đang tích dòng lạ) — không bấm tạo. Xem _macro/ocr_button.png.")

    code, out = run([macro, str(sp), "--only-generate"])
    if code != 0 or "STOP" in out:
        sys.exit("STOP: bước bấm tạo dừng — xem _macro/.")
    print(f"Đã gửi tạo {n} cảnh sau {time.time() - t0:.0f}s, không cần Claude chụp màn hình.")

    if a.collect:
        code, _ = run([str(TAO / "tool_jobs.py"), "collect", str(sp), "--wait", str(a.wait)])
        sys.exit(code)
    print(f"Lấy clip: python {TAO / 'tool_jobs.py'} collect {sp} --wait {a.wait}")


if __name__ == "__main__":
    main()
