"""Macro Studio Kịch Bản (video đồng nhất, nối frame cuối) — chạy liền một mạch, không chờ Claude nhìn từng bước.

python tool_story_macro.py projects/<slug>/storyboard.json [--provider veo3|muse] [--model omni|lite|lite-lp|fast|quality] [--dur 10]
python tool_story_macro.py projects/<slug>/storyboard.json --only-generate

Bước 1 (mặc định): app lên trước → Studio Kịch Bản → + Thêm Dự Án Mới (dự án mới, KHÔNG đụng dự án của anh)
→ chỉnh Cảnh 1 mẫu (nền tảng / model / tỉ lệ / thời lượng, ô chọn gốc Windows → dùng phím) → Nhập Danh Sách Prompt
→ Dán Clipboard → Nạp Vào Dự Án (mọi cảnh kế thừa cài đặt Cảnh 1) → gắn ảnh nhân vật vào "Ảnh đầu vào" Cảnh 1 (nếu có).
Sau đó Claude zoom kiểm tra nút "TẠO VIDEO KỊCH BẢN (N cảnh)" + cài đặt các thẻ, rồi chạy bước 2.
Bước 2 (--only-generate): chỉ bấm TẠO VIDEO KỊCH BẢN khi đang ở trang Kịch Bản (không hộp nào mở).
Lấy clip: tool_jobs.py collect … --wait 1800.

An toàn giống tool_macro.py: nhận diện màn hình trước mỗi bước, sai là dừng; không phím nguy hiểm.
Chỉ tự gắn ảnh cho Cảnh 1 (vị trí nút "+" các cảnh sau đổi theo độ dài prompt) — cảnh sau cần ảnh riêng thì Claude gắn tay.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tool_macro as M  # noqa: E402  (dùng chung SendInput, nhận diện, focus_app, shot)

VK_DOWN, VK_HOME, VK_END = 0x28, 0x24, 0x23
M.SAFE_VK |= {VK_DOWN, VK_HOME, VK_END}

S = dict(
    nav_story=(48, 147), add_project=(1527, 23), run=(1493, 82),
    import_btn=(158, 82), dlg_paste=(820, 272), dlg_load=(895, 396), dlg_cancel=(846, 396),
    sc1_provider=(137, 230), sc1_model=(185, 230), sc1_ratio=(226, 230), sc1_dur=(256, 230),
    sc1_add_img=(126, 175),
)
MODEL_KEYS = {"omni": [VK_HOME], "lite": [VK_HOME, VK_DOWN], "lite-lp": [VK_HOME, VK_DOWN, VK_DOWN],
              "fast": [VK_END, 0x26], "quality": [VK_END]}  # 0x26 = ↑
M.SAFE_VK.add(0x26)
RATIO_KEYS = {"16:9": [VK_HOME], "9:16": [VK_HOME, VK_DOWN], "1:1": [VK_END]}
DUR_KEYS = {5: [VK_HOME], 6: [VK_HOME, VK_DOWN], 8: [VK_END, 0x26], 10: [VK_END]}


def story_state():
    im = M.grab()
    teal = lambda r, g, b: g > 150 and b > 150 and r < 140
    white = lambda r, g, b: min(r, g, b) > 170
    # Trang Kịch Bản = mục "Studio Kịch Bản" đang sáng ở menu trái VÀ nút "+ Thêm Dự Án Mới" xanh ngọc.
    # (Chỉ nhìn nút góc phải là SAI: nút "Tạo video" của trang Video AI cũng xanh ngọc → đã bấm nhầm 07/11/2026.)
    if M.active_nav(im) == "kichban" and M.frac(im, (1500, 17, 1556, 29), teal) > 0.15:
        return "story"
    if M.frac(im, (640, 242, 830, 252), white) > 0.08:
        return "story_dialog"     # hộp "Nhập Danh Sách Prompt Kịch Bản Cho: …"
    return "other"


def expect(state, step, timeout=4.0):
    t = time.time()
    s = None
    while time.time() - t < timeout:
        s = story_state()
        if s == state:
            return
        time.sleep(0.3)
    M.shot(f"STOP_{step}")
    raise M.Stop(f"bước '{step}': cần '{state}' nhưng đang là '{s}'")


def pick(xy, keys):
    """Ô chọn gốc Windows: bấm → phím → Enter."""
    M.click(*xy, wait=0.5)
    for k in keys:
        M.key(k, wait=0.12)
    M.key(0x0D, wait=0.7)


def build(a):
    sb = json.load(open(a.storyboard, encoding="utf-8"))
    proj = os.path.dirname(os.path.abspath(a.storyboard))
    n = len(sb["scenes"])
    ratio = sb.get("aspect", "16:9")
    t0 = time.time()
    subprocess.run([sys.executable, os.path.join(M.HERE, "tool_jobs.py"), "export", a.storyboard, "--lines", "--clip"],
                   check=True, capture_output=True)

    M.focus_app()
    M.click(*S["nav_story"], wait=1.2)
    expect("story", "mo_trang_kich_ban")

    # dự án mới (có sẵn 2 cảnh mẫu Muse AI · 16:9 · 10s)
    M.click(*S["add_project"], wait=1.5)
    expect("story", "tao_du_an")

    # Cảnh 1 mẫu: nền tảng → model → tỉ lệ → thời lượng (đổi nền tảng tự đặt lại model + thời lượng)
    if a.provider == "veo3":
        pick(S["sc1_provider"], [VK_HOME, VK_DOWN])
        pick(S["sc1_model"], MODEL_KEYS[a.model])
        pick(S["sc1_ratio"], RATIO_KEYS.get(ratio, [VK_HOME]))
        pick(S["sc1_dur"], DUR_KEYS[a.dur])
    else:                                         # Muse AI: không có ô model → tỉ lệ dời sang trái
        pick(S["sc1_provider"], [VK_HOME])
        pick((173, 230), RATIO_KEYS.get(ratio, [VK_HOME]))
    expect("story", "cai_dat_canh_1")
    M.shot("1_canh1")

    # nạp danh sách prompt (thay toàn bộ cảnh, kế thừa cài đặt Cảnh 1)
    M.click(*S["import_btn"], wait=1.0)
    expect("story_dialog", "mo_hop_nhap")
    M.click(*S["dlg_paste"], wait=1.0)
    M.shot("2_dan")
    M.click(*S["dlg_load"], wait=1.5)
    expect("story", "nap_xong")

    # ảnh nhân vật cho Cảnh 1
    sc1 = sb["scenes"][0]
    imgs = sc1.get("reference_images") or sc1.get("first_last") or []
    imgs = [imgs] if isinstance(imgs, str) else imgs
    if imgs:
        paths = [p if os.path.isabs(p) else os.path.join(proj, p) for p in imgs]
        folder = os.path.dirname(paths[0])
        M.click(*S["sc1_add_img"], wait=1.5)     # hộp chọn file Windows
        M.type_text(folder)
        M.key(0x0D, wait=1.0)
        M.type_text(" ".join(f'"{os.path.basename(p)}"' for p in paths))
        M.key(0x0D, wait=2.0 + 0.8 * len(paths))
        M.focus_app()
        expect("story", "gan_anh_canh_1")
    others = [sc["id"] for sc in sb["scenes"][1:] if sc.get("reference_images")]
    M.shot("3_xong")
    print(f"Đã tạo dự án mới, nạp {n} cảnh ({a.provider}/{a.model}, {ratio}, {a.dur}s), "
          f"ảnh Cảnh 1: {len(imgs)} — {time.time() - t0:.0f}s. Ảnh: {M.SHOTS}")
    if others:
        print(f"LƯU Ý: cảnh {others} có ảnh riêng — Claude gắn tay bằng nút (+) của thẻ cảnh đó.")
    print(f"Tiếp: Claude zoom (1440,72)-(1556,92) phải ghi 'TẠO VIDEO KỊCH BẢN {n} cảnh', rồi chạy --only-generate.")


def generate(a):
    sb = json.load(open(a.storyboard, encoding="utf-8"))
    prompts = [sc["prompt"] for sc in sb["scenes"]]
    M.focus_app()
    expect("story", "truoc_khi_tao")
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 5))
    M.click(*S["run"], wait=8.0)
    c = M.queued_count(prompts[:1], since)        # chuỗi chạy lần lượt → lúc đầu chỉ có Cảnh 1
    if c:
        print("ĐÃ CHẠY: Cảnh 1 đã vào hàng đợi, các cảnh sau tự nối tiếp. Lấy clip: tool_jobs.py collect … --wait 1800")
    else:
        M.shot("4_tao")
        print("STOP: chưa thấy Cảnh 1 trong hàng đợi — Claude xem _macro/4_tao.jpg.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--provider", default="veo3", choices=["veo3", "muse"])
    ap.add_argument("--model", default="omni", choices=list(MODEL_KEYS))
    ap.add_argument("--dur", type=int, default=10, choices=list(DUR_KEYS))
    ap.add_argument("--only-generate", action="store_true")
    a = ap.parse_args()
    M.SHOTS = os.path.join(os.path.dirname(os.path.abspath(a.storyboard)), "_macro")
    os.makedirs(M.SHOTS, exist_ok=True)
    try:
        generate(a) if a.only_generate else build(a)
    except M.Stop as e:
        print(f"STOP: {e}. Ảnh lúc dừng trong {M.SHOTS}")
        sys.exit(2)
    finally:
        M.release_topmost()


if __name__ == "__main__":
    main()
