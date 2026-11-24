"""Macro chạy liền một mạch trên AI VIDEO LIBRARY (trang Video AI) — không chờ Claude nhìn từng bước.

python tool_macro.py projects/<slug>/storyboard.json [--model omni|lite|lite-lp|fast|quality] [--dur 10] [--generate]

Các bước: app nổi trên cùng + phóng to → Video AI → Nhập prompt (Tên chung, Dán Clipboard, nạp ảnh
tool_refs/ vào thư viện) → Nhập N prompt → ngăn chi tiết dòng mới cuối bảng → tỉ lệ, model, thời lượng,
Upscale, Xoá watermark → Áp dụng cho mục chọn → gắn ảnh từng cảnh bằng hộp chọn ảnh (lùi bằng nút ‹)
→ đóng ngăn → (--generate) Tạo video + kiểm tra hàng đợi.

AN TOÀN
- Trước mỗi bước nhận diện trạng thái màn hình (trang / hộp nhập / ngăn chi tiết / hộp chọn ảnh) bằng màu
  điểm ảnh; sai trạng thái là DỪNG ngay (in "STOP: …"), không gõ / bấm tiếp.
- Nút X đóng ngăn (1553,23) trùng chỗ nút Tạo video → chỉ bấm khi ngăn đang mở.
- Không tự bấm Tạo video lần 2 (bấm vào một dòng là app tự TÍCH dòng đó → dễ tạo nhầm prompt của anh).
- Chỉ dùng click, cuộn, gõ chữ Unicode, Enter, Esc, Ctrl+A. KHÔNG BAO GIỜ gửi F12 / Ctrl+Shift+I/J/C /
  Ctrl+U (bẫy chống crack của app).
Toạ độ đo trên màn 3440x1440, scale 100%, app phóng to (khung chụp của Claude 1568x656).
Ảnh từng mốc lưu ở projects/<slug>/_macro/.
"""
import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get("APPDATA", ""), "AI_VIDEO_LIBRARY_DATA")
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
SW, SH = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
FX, FY = SW / 1568, SH / 656


class Stop(Exception):
    pass


# ---------- nhập liệu cấp thấp (SendInput) ----------
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send(*ins):
    arr = (INPUT * len(ins))(*ins)
    u32.SendInput(len(ins), arr, ctypes.sizeof(INPUT))


def _mouse(flags, data=0):
    i = INPUT(type=0)
    i.u.mi = MOUSEINPUT(0, 0, data, flags, 0, 0)
    return i


def _kb(vk=0, scan=0, flags=0):
    return INPUT(type=1, u=_U(ki=KEYBDINPUT(vk, scan, flags, 0, 0)))


def click(x, y, wait=0.5):
    u32.SetCursorPos(int(x * FX), int(y * FY))
    time.sleep(0.05)
    _send(_mouse(0x0002), _mouse(0x0004))
    time.sleep(wait)


def scroll(x, y, ticks):  # > 0 lên, < 0 xuống
    u32.SetCursorPos(int(x * FX), int(y * FY))
    for _ in range(abs(ticks)):
        _send(_mouse(0x0800, ctypes.c_uint32(120 if ticks > 0 else -120).value))
        time.sleep(0.01)
    time.sleep(0.4)


SAFE_VK = {0x0D, 0x1B, 0x41}  # Enter, Esc, A (chỉ dùng kèm Ctrl = chọn hết)


def key(vk, ctrl=False, wait=0.3):
    if vk not in SAFE_VK:
        raise Stop("phím không nằm trong danh sách an toàn")
    seq = ([_kb(0x11)] if ctrl else []) + [_kb(vk), _kb(vk, flags=2)] + ([_kb(0x11, flags=2)] if ctrl else [])
    _send(*seq)
    time.sleep(wait)


def type_text(t, wait=0.3):
    for ch in t:
        _send(_kb(scan=ord(ch), flags=4), _kb(scan=ord(ch), flags=6))
    time.sleep(wait)


# ---------- nhìn màn hình ----------
def grab():
    from PIL import ImageGrab
    return ImageGrab.grab()


def frac(im, box, test):
    r = im.crop(tuple(int(v * (FX if i % 2 == 0 else FY)) for i, v in enumerate(box))).convert("RGB")
    px = r.get_flattened_data() if hasattr(r, "get_flattened_data") else r.getdata()
    px = list(px)
    return sum(1 for p in px if test(*p)) / max(1, len(px))


NAV_BOX = {"anh": (10, 93, 98, 105), "video": (10, 109, 98, 121), "xuong": (10, 125, 98, 137),
           "kichban": (10, 141, 98, 153)}


def active_nav(im=None):
    """Mục menu trái đang mở (nền xanh: ~0.12 điểm xanh, mục khác 0). None nếu không rõ (đang có hộp che)."""
    im = im or grab()
    cyan = lambda r, g, b: b > r + 25 and g > r + 15 and b > 70
    scores = {k: frac(im, box, cyan) for k, box in NAV_BOX.items()}
    k = max(scores, key=scores.get)
    return k if scores[k] > 0.05 else None


def screen_state():
    im = grab()
    if frac(im, (1050, 52, 1088, 68), lambda r, g, b: r > 150 and r > b + 30) > 0.05:
        return "dialog"           # hộp Nhập prompt: nút "Đóng" đỏ hồng
    if frac(im, (1120, 518, 1186, 536), lambda r, g, b: r + g + b > 600) > 0.02 and \
       frac(im, (380, 105, 1190, 540), lambda r, g, b: r + g + b > 600) < 0.2:
        return "picker"           # hộp chọn ảnh: nút "Dùng ảnh đã chọn"
    badge = (1400, 17, 1436, 29)  # ô "Prompt #N" đầu ngăn chi tiết (đo: mở 0.16 trắng / đóng 0.005)
    if frac(im, badge, lambda r, g, b: min(r, g, b) > 170) > 0.08 and \
       frac(im, badge, lambda r, g, b: r + g + b < 120) > 0.4:
        return "panel"
    return "page" if active_nav(im) == "video" else "other"   # "page" = trang Video AI, không hộp nào mở


def expect(state, step, timeout=4.0):
    t = time.time()
    while time.time() - t < timeout:
        s = screen_state()
        if s == state:
            return
        time.sleep(0.3)
    shot(f"STOP_{step}")
    raise Stop(f"bước '{step}': cần màn hình '{state}' nhưng đang là '{s}'")


def is_on(x, y):
    r, g, b = grab().getpixel((int(x * FX), int(y * FY)))[:3]
    return max(r, g, b) - min(r, g, b) > 60 and max(r, g, b) > 120


SHOTS = None


def shot(name):
    grab().resize((1568, 656)).save(os.path.join(SHOTS, f"{name}.jpg"), quality=70)


# ---------- cửa sổ ----------
HWND = None


def focus_app(topmost=True):
    global HWND
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process | ?{ $_.ProcessName -like 'AI VIDEO*' -and $_.MainWindowHandle -ne 0 } | select -First 1).MainWindowHandle"],
                         capture_output=True, text=True).stdout.strip()
    if not out or out == "0":
        raise Stop("AI VIDEO LIBRARY chưa mở — mở app rồi chạy lại")
    HWND = wintypes.HWND(int(out))
    u32.ShowWindow(HWND, 3)
    _send(_kb(0x12), _kb(0x12, flags=2))      # Alt rỗng để Windows cho đưa cửa sổ lên trước
    u32.SetForegroundWindow(HWND)
    if topmost:                                # nổi trên mọi cửa sổ (kể cả Claude) trong lúc chạy
        u32.SetWindowPos(HWND, wintypes.HWND(-1), 0, 0, 0, 0, 0x0003)
    for _ in range(3):
        time.sleep(0.6)
        fg = u32.GetAncestor(u32.GetForegroundWindow(), 3)   # GA_ROOTOWNER: hộp con của app vẫn tính là app
        if fg == HWND.value:
            return
        _send(_kb(0x12), _kb(0x12, flags=2))
        u32.SetForegroundWindow(HWND)
    raise Stop("không đưa được app lên trước")


def release_topmost():
    if HWND:
        u32.SetWindowPos(HWND, wintypes.HWND(-2), 0, 0, 0, 0, 0x0003)


# ---------- toạ độ (khung 1568x656) ----------
P = dict(
    nav_video=(38, 115), page_top=(700, 400), table=(700, 150),
    btn_import=(1327, 57), name_box=(550, 100), paste=(624, 100), clear_text=(722, 100), clear_imgs=(746, 283),
    src_computer=(553, 208), dropzone=(624, 250), do_import=(1050, 583),
    last_row=(400, 200), close_panel=(1553, 23), prev_prompt=(1470, 23),
    ratio=(1425, 307), model=(1478, 288), dur=(1530, 307), upscale=(1540, 347), wm=(1540, 379),
    apply_sel=(1439, 411), add_ref=(1537, 447), mode_frames=(1517, 239), mode_components=(1438, 239),
    pick_search=(1110, 150), pick_first=(437, 225), pick_ok=(1153, 527),
    generate=(1535, 23),
)
RATIO_Y = {"16:9": 325, "9:16": 341}
# Từ 13/11/2026 tool thêm "Omni 1.2 Flash" lên ĐẦU danh sách (đốt credit gấp ~3 lần, anh dặn KHÔNG dùng). "omni" = Omni 1.1 Flash (mục 2); "omni12" chỉ khi anh yêu cầu rõ.
# Toạ độ ước theo khoảng cách ~14px/mục — LUÔN Read _macro/2_settings.jpg kiểm ô model ghi "Omni 1.1 Flash" trước khi tạo.
MODEL_Y = {"omni12": 307, "omni": 321, "lite": 335, "lite-lp": 350, "fast": 364, "quality": 378}
DUR_Y = {4: 325, 6: 338, 8: 353, 10: 368}


def asset_names_by_sha(shas):
    out = {}
    for _ in range(10):
        a = json.load(open(os.path.join(DATA, "asset-state.json"), encoding="utf-8"))
        for x in a.get("assets", []):
            if x.get("sha256") in shas and x.get("type") == "image":
                out[x["sha256"]] = x.get("name", "")
        if len(out) == len(shas):
            break
        time.sleep(1)
    return out


def attach_ref(names, h, tag):
    """Ngăn chi tiết đang mở → Thêm ảnh → hộp chọn ảnh: tìm theo tên → ảnh đầu → Dùng ảnh đã chọn."""
    if h not in names:
        raise Stop(f"không thấy ảnh ({tag}) trong thư viện tool")
    click(*P["add_ref"], wait=1.0)
    expect("picker", f"hop_chon_anh_{tag}")
    click(*P["pick_search"], wait=0.2)
    key(0x41, ctrl=True, wait=0.1)               # xoá chữ tìm kiếm cũ
    type_text(names[h], wait=1.0)
    click(*P["pick_first"], wait=0.4)
    click(*P["pick_ok"], wait=0.8)
    expect("panel", f"gan_anh_{tag}")


def queued_count(prompts, since):
    q = json.load(open(os.path.join(DATA, "queue-state.json"), encoding="utf-8"))
    keys = {" ".join(p.split()).lower() for p in prompts}
    return sum(1 for j in q.get("jobs", []) if j.get("createdAt", "") >= since
               and " ".join((j.get("payload", {}).get("prompt") or "").split()).lower() in keys)


def prepare_refs(sb, proj):
    """tool_refs/ref-<vân tay chữ>.<đuôi> — tên không có chữ số để hộp Nhập không tự ghép nhầm cảnh."""
    rd = os.path.join(proj, "tool_refs")
    shutil.rmtree(rd, ignore_errors=True)
    os.makedirs(rd)
    shas = []
    for sc in sb["scenes"]:
        imgs = sc.get("reference_images") or sc.get("first_last") or []
        imgs = [imgs] if isinstance(imgs, str) else imgs
        if not imgs:
            shas.append(None)
            continue
        src = imgs[0] if os.path.isabs(imgs[0]) else os.path.join(proj, imgs[0])
        h = hashlib.sha256(open(src, "rb").read()).hexdigest()
        shas.append(h)
        name = "ref-" + h[:10].translate(str.maketrans("0123456789abcdef", "ghijklmnoqrstuvw"))
        shutil.copy2(src, os.path.join(rd, name + os.path.splitext(src)[1].lower()))
    return shas, sorted(os.listdir(rd))


def run(a):
    sb = json.load(open(a.storyboard, encoding="utf-8"))
    proj = os.path.dirname(os.path.abspath(a.storyboard))
    prompts = [sc["prompt"] for sc in sb["scenes"]]
    n = len(prompts)
    ratio = sb.get("aspect", "16:9")
    t0 = time.time()

    subprocess.run([sys.executable, os.path.join(HERE, "tool_jobs.py"), "export", a.storyboard, "--clip"],
                   check=True, capture_output=True)
    shas, refs = prepare_refs(sb, proj)

    # 1. app → Video AI, đầu trang, không mở gì
    focus_app()
    click(*P["nav_video"], wait=1.2)
    scroll(*P["page_top"], 60)
    if screen_state() == "panel":
        click(*P["close_panel"], wait=0.8)
    expect("page", "mo_trang")

    # 2. hộp Nhập prompt
    click(*P["btn_import"], wait=1.0)
    expect("dialog", "mo_hop_nhap")
    # Hộp Nhập GIỮ nội dung lần trước (Hủy không xoá) → dọn sạch trước khi dán, nếu không sẽ nhân đôi prompt.
    click(*P["clear_text"], wait=0.5)            # nút đỏ xoá nội dung (chỉ hiện khi có chữ; trống thì bấm vào khoảng trống)
    click(*P["clear_imgs"], wait=0.5)            # "Xóa tất cả ảnh" (chỉ hiện khi còn ảnh cũ)
    expect("dialog", "don_hop_nhap")
    click(*P["name_box"], wait=0.2)
    key(0x41, ctrl=True, wait=0.1)               # gõ đè Tên chung cũ
    type_text(sb.get("title", "video"))
    click(*P["paste"], wait=1.0)
    if refs:
        click(*P["src_computer"], wait=0.4)
        click(*P["dropzone"], wait=1.5)          # hộp chọn file Windows
        type_text(os.path.join(proj, "tool_refs"))
        key(0x0D, wait=1.0)
        type_text(" ".join(f'"{r}"' for r in refs))
        key(0x0D, wait=1.2)
        expect("dialog", "nap_anh")
    shot("1_import_dialog")
    click(*P["do_import"], wait=1.5 + 0.8 * len(refs))
    expect("page", "nhap_xong", timeout=10)

    # 3. ngăn chi tiết dòng mới cuối bảng
    scroll(*P["table"], -20)
    scroll(*P["page_top"], 60)                   # bảng đã ở cuối thì lệnh cuộn trôi sang trang
    for y in (P["last_row"][1], 175, 150, 125, 100):   # bảng ngắn (1–3 dòng) thì dòng cuối nằm cao hơn
        click(P["last_row"][0], y, wait=1.0)
        if screen_state() == "panel":
            break
    expect("panel", "mo_ngan_chi_tiet")

    # 4. cài đặt rồi áp cho các dòng đang tích (chính là các dòng vừa nhập)
    if a.frames:                                 # Khung hình: ảnh của cảnh = KHUNG ĐẦU (I2V), khoá mặt nhân vật
        click(*P["mode_frames"], wait=0.8)
        expect("panel", "che_do_khung_hinh")
    if ratio in RATIO_Y:
        click(*P["ratio"], wait=0.6)
        click(1428, RATIO_Y[ratio], wait=0.6)
    click(*P["model"], wait=0.6)
    click(1440, MODEL_Y[a.model], wait=0.8)
    if a.model == "omni":                        # Veo 3.1 chỉ có 8s
        click(*P["dur"], wait=0.6)
        click(1525, DUR_Y[a.dur], wait=0.8)
    expect("panel", "cai_dat")
    for k in ("upscale", "wm"):
        if not is_on(*P[k]):
            click(*P[k], wait=0.5)
    st = {k: is_on(*P[k]) for k in ("upscale", "wm")}
    shot("2_settings")

    # "Áp dụng cho mục chọn" chép CẢ ảnh tham chiếu của dòng đang mở sang mọi dòng đang tích.
    #  - Mọi cảnh dùng CHUNG 1 ảnh → gắn 1 lần ở dòng này rồi Áp dụng (nhanh nhất).
    #  - Mỗi cảnh ảnh RIÊNG → Áp dụng TRƯỚC (dòng này chưa có ảnh), rồi gắn ảnh riêng từng cảnh,
    #    nếu không ảnh của dòng này sẽ đè lên mọi cảnh.
    names = asset_names_by_sha({h for h in shas if h}) if any(shas) else {}
    shared = len(set(shas)) == 1 and shas[0]
    attached = 0
    if shared:
        attach_ref(names, shas[0], "chung")
        attached = n
    click(*P["apply_sel"], wait=1.0)
    expect("panel", "ap_dung")

    # 5. ảnh riêng từng cảnh: đang ở cảnh cuối, lùi bằng ‹
    if any(shas) and not shared:
        for i in range(n - 1, -1, -1):
            if shas[i]:
                attach_ref(names, shas[i], f"c{i + 1}")
                attached += 1
            if i:
                click(*P["prev_prompt"], wait=0.7)
        shot("3_refs")

    # 6. đóng ngăn (CHỈ khi ngăn đang mở — X trùng chỗ nút Tạo video)
    expect("panel", "truoc_khi_dong")
    click(*P["close_panel"], wait=0.8)
    expect("page", "dong_ngan")
    shot("4_table")
    print(f"Đã nhập {n} prompt, gắn {attached} ảnh, tỉ lệ {ratio}, model={a.model}, {a.dur}s, "
          f"upscale={st['upscale']}, xoá WM={st['wm']} — {time.time() - t0:.0f}s. Ảnh: {SHOTS}")

    if a.generate:
        generate(prompts, n)


def generate(prompts, n):
    """Chỉ bấm Tạo video khi đang ở trang thường (không ngăn / hộp nào mở)."""
    if HWND is None:
        focus_app()
    expect("page", "truoc_khi_tao_video")
    if True:
        since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 5))
        click(*P["generate"], wait=6.0)
        c = queued_count(prompts, since)
        if c >= n:
            print(f"ĐÃ GỬI {c}/{n} cảnh vào hàng đợi.")
        else:
            shot("5_generate")
            print(f"STOP: mới vào hàng đợi {c}/{n} cảnh — Claude xem _macro/5_generate.jpg, bỏ tích dòng lạ rồi bấm lại.")


def main():
    global SHOTS
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--model", default="omni", choices=list(MODEL_Y))
    ap.add_argument("--dur", type=int, default=10, choices=list(DUR_Y))
    ap.add_argument("--frames", action="store_true", help="chế độ Khung hình: ảnh cảnh (first_last) làm khung đầu")
    ap.add_argument("--generate", action="store_true", help="nhập xong bấm Tạo video luôn (không khuyên dùng)")
    ap.add_argument("--only-generate", action="store_true",
                    help="chỉ bấm Tạo video — dùng SAU KHI Claude đã nhìn nút ghi đúng 'Tạo video N'")
    a = ap.parse_args()
    if (SW, SH) != (3440, 1440):
        print(f"CẢNH BÁO: màn {SW}x{SH} khác màn lúc học (3440x1440) — toạ độ có thể lệch.")
    SHOTS = os.path.join(os.path.dirname(os.path.abspath(a.storyboard)), "_macro")
    shutil.rmtree(SHOTS, ignore_errors=True)
    os.makedirs(SHOTS)
    try:
        if a.only_generate:
            sb = json.load(open(a.storyboard, encoding="utf-8"))
            generate([sc["prompt"] for sc in sb["scenes"]], len(sb["scenes"]))
        else:
            run(a)
    except Stop as e:
        print(f"STOP: {e}. Ảnh lúc dừng trong {SHOTS}")
        sys.exit(2)
    finally:
        release_topmost()


if __name__ == "__main__":
    main()
