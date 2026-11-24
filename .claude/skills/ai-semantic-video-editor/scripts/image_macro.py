"""Macro: create images on the "Ảnh AI" page of AI VIDEO LIBRARY in one go (character sheet, product, first frames).

  python image_macro.py projects/<slug>/storyboard.json [--auto] [--collect] [--wait 300]

storyboard["image_jobs"] = [{"prompt": "...", "dest": "ref/nhan-vat.jpg"}, ...]
Steps: app to front → Ảnh AI → "Nhập prompt" (clear old text, common name = title, paste prompts separated by a
blank line) → "Nhập N prompt" (new rows are appended and are the only ticked rows)
→ --auto: Windows OCR reads the button, must say "Tạo ảnh N" → click it → --collect: tool_jobs.py images copies
each finished image to its dest.
Settings (provider / ratio / resolution) are inherited from the rows above (eg. Banana · 9:16 · Full HD);
change them once by hand if a video needs other settings.

Safety: same rules as tool_macro.py (screen state checked before each step, only clicks / Ctrl+A / Ctrl+V,
never the anti-crack keys, no tool files written). The X of a detail panel = the "Tạo ảnh" button, so the macro
only clicks (1533,23) when no panel is open.
"""
from __future__ import annotations

import argparse
import json
import os
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

import tool_macro as T  # noqa: E402  (tao-video helpers, not modified)
from tts_macro import ctrl, set_clipboard  # noqa: E402

P = dict(nav_anh=(35, 99), btn_import=(1329, 56), name_box=(550, 100), paste=(624, 100), clear_text=(722, 100),
         do_import=(1050, 583), cancel=(991, 583), generate=(1533, 22), close_panel=(1553, 23))
BOX_BUTTON = (1490, 14, 1568, 32)


def state() -> str:
    s = T.screen_state()                          # 'dialog' detection is shared with the Video AI page
    if s == "dialog":
        return "dialog"
    im = T.grab()
    title_bright = T.frac(im, (110, 17, 200, 29), lambda r, g, b: r + g + b > 600)
    if title_bright < 0.05:
        return "panel"                            # page dimmed behind a detail panel
    return "page" if T.active_nav(im) == "anh" else "other"


def expect(want: str, step: str, timeout: float = 5.0) -> None:
    t0, s = time.time(), state()
    while time.time() - t0 < timeout:
        s = state()
        if s == want:
            return
        time.sleep(0.3)
    T.shot(f"STOP_img_{step}")
    raise T.Stop(f"bước '{step}': cần '{want}' nhưng đang '{s}' (xem _macro/STOP_img_{step}.jpg)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--auto", action="store_true", help="OCR kiểm nút 'Tạo ảnh N' rồi tự bấm tạo")
    ap.add_argument("--collect", action="store_true", help="chờ ảnh xong và chép về dest")
    ap.add_argument("--only-generate", action="store_true", help="prompt đã nạp: chỉ OCR kiểm nút rồi bấm tạo")
    ap.add_argument("--wait", type=int, default=300)
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    sb = json.loads(sp.read_text(encoding="utf-8"))
    jobs = sb.get("image_jobs") or []
    if not jobs:
        sys.exit("storyboard chưa có image_jobs.")
    n = len(jobs)
    T.SHOTS = str(sp.parent / "_macro")
    os.makedirs(T.SHOTS, exist_ok=True)
    t0 = time.time()
    try:
        T.focus_app(topmost=True)
        try:
            if state() == "panel":
                T.click(*P["close_panel"], wait=0.8)
            if state() == "dialog":
                T.click(*P["cancel"], wait=0.8)
            T.click(*P["nav_anh"], wait=1.2)
            T.scroll(700, 400, 60)
            expect("page", "trang_anh")
            if not a.only_generate:
                T.click(*P["btn_import"], wait=1.0)
                expect("dialog", "mo_hop_nhap")
                T.click(*P["clear_text"], wait=0.5)    # the dialog keeps the previous text
                expect("dialog", "don_hop")
                T.click(*P["name_box"], wait=0.2)
                ctrl(0x41)
                T.type_text(sb.get("title", "anh"))
                set_clipboard(chr(10).join(" ".join(j["prompt"].split()) + chr(10) for j in jobs).strip())
                T.click(*P["paste"], wait=1.0)
                T.shot("img_1_dialog")
                T.click(*P["do_import"], wait=1.5)
                expect("page", "nhap_xong", timeout=10)
                T.shot("img_2_imported")
                if not a.auto:
                    print(f"ĐÃ NHẬP {n} prompt ảnh. Chạy lại với --only-generate (OCR kiểm nút rồi tự bấm).")
                    return
            from screen_ocr import button_shows
            time.sleep(0.5)
            ok, seen = button_shows(BOX_BUTTON, n, save=str(Path(T.SHOTS) / "ocr_img_button.png"))
            print(f"OCR nút: {seen!r} → cần {n}: {'KHỚP' if ok else 'KHÔNG KHỚP'}")
            if not ok:
                raise T.Stop(f"nút không ghi 'Tạo ảnh {n}' (có dòng lạ đang tích?) — không bấm; xem _macro/ocr_img_button.png")
            expect("page", "truoc_khi_tao")           # never click (1533,22) while a panel is open
            T.click(*P["generate"], wait=1.5)
            T.shot("img_3_generate")
        finally:
            T.release_topmost()
    except T.Stop as e:
        print(f"STOP: {e}")
        sys.exit(2)
    print(f"Đã gửi tạo {n} ảnh sau {time.time() - t0:.0f}s.")
    if a.collect:
        rc = subprocess.run([sys.executable, str(TAO / "tool_jobs.py"), "images", str(sp), "--wait", str(a.wait)]).returncode
        # ảnh Gemini/Banana chưa bật xoá watermark → tự đẩy logo ngôi sao ra khỏi khung; cảnh báo ảnh sai tỉ lệ
        subprocess.run([sys.executable, str(HERE / "gemini_wm.py"), str(sp)])
        sys.exit(rc)
    print(f"Lấy ảnh: python {TAO / 'tool_jobs.py'} images {sp} --wait {a.wait}")


if __name__ == "__main__":
    main()
