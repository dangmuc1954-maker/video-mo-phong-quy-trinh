"""Read text on screen with Windows built-in OCR (no Claude screenshot needed).

  from screen_ocr import read_box, number_in_box
  number_in_box((1490, 14, 1568, 32))   # box in the 1568x656 frame used by tool_macro.py

CLI: python screen_ocr.py 1490 14 1568 32
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _frame_scale():
    import ctypes
    u32 = ctypes.windll.user32
    u32.SetProcessDPIAware()
    return u32.GetSystemMetrics(0) / 1568, u32.GetSystemMetrics(1) / 656


def read_box(box, upscale: int = 4, save: str | None = None) -> str:
    from PIL import ImageGrab, ImageOps
    fx, fy = _frame_scale()
    x0, y0, x1, y1 = box
    im = ImageGrab.grab(bbox=(int(x0 * fx), int(y0 * fy), int(x1 * fx), int(y1 * fy))).convert("L")
    im = im.resize((im.width * upscale, im.height * upscale))
    if sum(im.getdata()) / (im.width * im.height) < 128:     # light text on dark/coloured button → invert
        im = ImageOps.invert(im)
    im = ImageOps.autocontrast(im)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    im.save(tmp)
    if save:
        im.save(save)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "win_ocr.ps1"), tmp],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return (r.stdout or "").strip()
    finally:
        os.unlink(tmp)


FIX = str.maketrans({"l": "1", "I": "1", "|": "1", "!": "1", "i": "1", "O": "0", "o": "0", "D": "0", "Q": "0",
                     "S": "5", "s": "5", "Z": "2", "z": "2", "B": "8", "g": "9", "q": "9"})


def number_in_box(box, **kw) -> tuple[int | None, str]:
    """Number written on a button such as 'Tạo video 6', 'Tạo âm thanh 1', 'TẠO VIDEO KỊCH BẢN 6 cảnh'.
    OCR often glues the digit to the word ('videol'), so the token right after the keyword is normalised."""
    text = read_box(box, **kw)
    m = re.search(r"(?:vide0|video|thanh|b.n|ban|.nh)\s*([0-9lIi|!OoDQSsZzBgq]{1,3})(?![a-zA-Z])", text, re.I)
    if m:
        d = m.group(1).translate(FIX)
        if d.isdigit():
            return int(d), text
    nums = re.findall(r"\d+", text)
    return (int(nums[-1]) if nums else None), text


def _ocr_image(im) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    im.save(tmp)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "win_ocr.ps1"), tmp],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return (r.stdout or "").strip()
    finally:
        os.unlink(tmp)


def _variants(im):
    """Các biến thể ảnh để OCR: cả nút + riêng nửa phải (chỗ ghi 'N cảnh' / số), nhiều độ phóng, đảo màu hoặc không."""
    from PIL import ImageOps
    g = im.convert("L")
    w, h = g.size
    for crop, name in ((g, "full"), (g.crop((int(w * 0.55), 0, w, h)), "right45"), (g.crop((int(w * 0.68), 0, w, h)), "right32")):
        for up in (3, 5):
            big = crop.resize((crop.width * up, crop.height * up))
            for inv in (False, True):
                v = ImageOps.autocontrast(ImageOps.invert(big) if inv else big)
                yield f"{name}x{up}{'i' if inv else ''}", v
            # chữ trắng trên nền màu / chuyển màu (nút đang bật): tách chữ sáng → chữ đen nền trắng; và ngược lại cho chữ tối
            for thr in (150, 185, 215):
                yield f"{name}x{up}w{thr}", big.point(lambda px, t=thr: 0 if px > t else 255)
            for thr in (70, 110):
                yield f"{name}x{up}d{thr}", big.point(lambda px, t=thr: 0 if px < t else 255)


def count_in_image(im, expected: int) -> tuple[bool, str]:
    """True khi MỘT biến thể ảnh đọc ra đúng số `expected` (số riêng hoặc 'N cảnh'/'N video'), và không biến thể nào đọc ra số khác một cách rõ ràng."""
    seen, texts = {}, []
    for name, v in _variants(im):
        t = _ocr_image(v)
        texts.append(f"{name}:{t!r}")
        for m in re.finditer(r"(?<![0-9])([0-9lIi|!OoDQSsZzBgq]{1,3})\s*(?:c[a-zåäàáảãạâ]*nh|video|v[i1]deo|prompt|[âa]m)", t, re.I):
            d = m.group(1).translate(FIX)
            if d.isdigit():
                seen[int(d)] = seen.get(int(d), 0) + 1
        if name.startswith("right"):
            for d in re.findall(r"(?<![0-9])\d{1,3}(?![0-9])", t):
                seen[int(d)] = seen.get(int(d), 0) + 1
        if seen.get(expected, 0) >= 1 and name.startswith("right") and all(c < seen[expected] for k, c in seen.items() if k != expected):
            return True, " | ".join(texts)
    ok = bool(seen) and max(seen, key=seen.get) == expected and seen[expected] >= 1
    return ok, " | ".join(texts)


def button_shows(box, expected: int, tries: int = 2, save: str | None = None, **kw) -> tuple[bool, str]:
    """Kiểm số trên nút. NHANH TRƯỚC: cách đơn giản (1 lần OCR, ~1s) — khớp là trả về ngay. Chỉ khi không khớp mới thử nhiều biến thể ảnh (chậm, cho nút chữ trắng trên nền màu)."""
    from PIL import ImageGrab
    fx, fy = _frame_scale()
    x0, y0, x1, y1 = box
    n, last = number_in_box(box, save=save) if save else number_in_box(box)
    if n == expected:
        return True, last
    for _ in range(max(1, tries - 1)):
        im = ImageGrab.grab(bbox=(int(x0 * fx), int(y0 * fy), int(x1 * fx), int(y1 * fy)))
        if save:
            im.save(save)
        ok, t = count_in_image(im, expected)
        last += f" | variants:{t[:200]}"
        if ok:
            return True, last
    return False, last


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    b = tuple(float(v) for v in sys.argv[1:5])
    n, t = number_in_box(b)
    print(f"text={t!r} number={n}")
