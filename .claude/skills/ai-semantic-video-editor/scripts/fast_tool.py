"""Studio Kịch Bản MỘT MẠCH, không khựng: nạp prompt → gắn ảnh tham chiếu → kiểm nút → bấm tạo, trong 1 tiến trình.

  python fast_tool.py projects/<slug>/storyboard.json [--speed 0.55] [--model omni] [--dur 10] [--provider veo3] [--collect]

So với auto_tool.py story (3 tiến trình, chờ cố định):
  - chờ sau mỗi cú bấm × --speed (0.55 = nhanh gần gấp đôi; 1.0 = như cũ); các bước vẫn có kiểm trạng thái màn hình (expect / hộp chọn file),
    sai là dừng an toàn (STOP), không gõ bừa.
  - kiểm số trên nút bằng OCR nhiều biến thể (hết dừng vì đọc sai chữ).
  - không khởi động lại tiến trình / không focus lại giữa các bước.
In ra thời gian từng chặng. Lấy clip (nền): thêm --collect, hoặc chạy tool_jobs.py collect.
Chỉ click / Ctrl+A / Ctrl+V / Esc (an toàn tool). Model mặc định Omni 1.1 Flash (KHÔNG 1.2) — Read _macro/1_canh1.jpg kiểm nếu lần đầu.
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

import tool_macro as M  # noqa: E402
import tool_story_macro as S  # noqa: E402
from screen_ocr import button_shows  # noqa: E402

BOX = (1440, 72, 1556, 92)


def speed_up(f: float) -> None:
    """Co thời gian chờ cố định sau mỗi click / phím (sàn 0.15s), giữ nguyên các bước kiểm trạng thái."""
    oc, ok = M.click, M.key

    def click(x, y, wait=0.5):
        return oc(x, y, wait=max(0.15, wait * f))

    def key(vk, ctrl=False, wait=0.3):
        return ok(vk, ctrl=ctrl, wait=max(0.08, wait * f))

    M.click, M.key = click, key


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--speed", type=float, default=0.4)
    ap.add_argument("--model", default="omni")
    ap.add_argument("--dur", type=int, default=10)
    ap.add_argument("--provider", default="veo3")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="kiểm số trên nút bằng OCR (~10s, mặc định TẮT: từ 23/11/2026 app tạo dự án trống + macro Dọn Cảnh trước khi nạp → không còn cảnh lạ)")
    ap.add_argument("--wait", type=int, default=3600)
    a = ap.parse_args()
    sp = Path(a.storyboard).resolve()
    sb = json.loads(sp.read_text(encoding="utf-8"))
    n = len(sb["scenes"])
    M.SHOTS = str(sp.parent / "_macro")
    Path(M.SHOTS).mkdir(exist_ok=True)
    speed_up(a.speed)
    ns = argparse.Namespace(storyboard=str(sp), provider=a.provider, model=a.model, dur=a.dur, only_generate=False)
    t0 = time.time()
    try:
        S.build(ns)                                   # nạp prompt + gắn ảnh (có kiểm hộp chọn file)
        t1 = time.time()
        t2 = t1
        if a.verify:                                  # tuỳ chọn: kiểm số trên nút bằng OCR (chậm ~20s, chỉ cần khi nạp vào dự án CÓ SẴN)
            ok, text = button_shows(BOX, n, save=str(Path(M.SHOTS) / "ocr_button.png"))
            t2 = time.time()
            print(f"OCR nút → cần {n}: {'KHỚP' if ok else 'KHÔNG KHỚP'} ({t2 - t1:.1f}s)")
            if not ok:
                M.shot("STOP_nut_tao")
                sys.exit(f"STOP: số trên nút không khớp {n} cảnh. Xem _macro/STOP_nut_tao.jpg. {text[:160]}")
        S.generate(ns)                                # bấm tạo + xác nhận cảnh 1 vào hàng đợi
    except M.Stop as e:
        sys.exit(f"STOP: {e}")
    finally:
        try:
            M.release_topmost()
        except Exception:  # noqa: BLE001
            pass
    try:
        st = subprocess.run([sys.executable, str(TAO / "tool_jobs.py"), "status", str(sp)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        busy = sum(1 for l in st.splitlines() if "Running" in l or "Pending" in l or "Completed" in l)
        model = "1.2" if "omni-flash-1.2" in st else "1.1" if "omni-flash-1.1" in st else "?"
        print(f"Hàng đợi: {busy}/{n} cảnh đã vào · model omni-flash-{model}" + ("  ⚠ ĐANG DÙNG 1.2 (đắt gấp 3)" if model == "1.2" else ""))
    except Exception:  # noqa: BLE001
        pass
    print(f"XONG: nạp + gắn ảnh {t1 - t0:.0f}s · kiểm nút {t2 - t1:.0f}s · bấm tạo {time.time() - t2:.0f}s · tổng {time.time() - t0:.0f}s (speed {a.speed})")
    if a.collect:
        r = subprocess.run([sys.executable, str(TAO / "tool_jobs.py"), "collect", str(sp), "--wait", str(a.wait)])
        sys.exit(r.returncode)
    print(f"Lấy clip: python {TAO / 'tool_jobs.py'} collect {sp} --wait {a.wait}")


if __name__ == "__main__":
    main()
