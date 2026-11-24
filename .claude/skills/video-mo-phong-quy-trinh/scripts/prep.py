"""Kiểm kịch bản theo LUẬT VÀNG rồi sinh prompt + storyboard_tool.json (chỉ các cảnh tạo trong tool).

  python prep.py projects/<slug>/storyboard.json

In "OK: …" khi đạt; "STOP: …" kèm danh sách lỗi phải sửa trong build_sb.py rồi chạy lại.
Cảnh có "real_photo" (ảnh thật) KHÔNG đưa vào tool — photo_clip.py làm clip cho cảnh đó.

TRẠNG THÁI XÂY DỰNG (luật 12 — chặn lỗi "chưa xây mà đã thấy công trình xong"):
  sb["ten_cong_trinh"] = ["great wall", "pyramid"]   ← tên (tiếng Anh, chữ thường) tool dễ vẽ sẵn bản hoàn chỉnh
  mỗi cảnh: "da_co": [...] (đã xây tới cảnh này), "chua_co": [...] (chưa xây, CẤM xuất hiện),
            tuỳ chọn "hoan_thanh": true (cảnh cho phép thấy công trình xong), "tua_lai": true (cảnh tua ngược, được lùi trạng thái)
  prep.py ghi vào prompt từng cảnh: "ALREADY BUILT … / NOT BUILT YET, must NOT appear …" và chặn khi beats nhắc phần chưa xây.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
S = Path(__file__).resolve().parents[2] / "tao-video" / "scripts"

LEADS = ["không chịu bỏ cuộc", "nghỉ ngơi", "ngàn cân treo sợi tóc", "thua keo này", "mất ngủ", "chợt hiểu", "bế tắc",
         "thất bại", "bật dậy", "nảy ra", "sáng lên ý tưởng", "lóe lên", "búng tay"]
BAD_STYLE = ["photorealistic", "photo-realistic", "cinematic", "drone", "live-action", "realistic footage"]
DEPTH = ["cutaway", "section", "x-ray", "semi-transparent", "exploded", "peel", "flies through", "inside", "macro",
         "wireframe", "arrow", "time-lapse", "cross-section", "zoom"]


GHOST = ["ghost", "wireframe", "blueprint", "plan ", "outline marker", "survey"]


def as_list(v):
    return [x.strip().lower() for x in (v if isinstance(v, list) else [v] if v else []) if str(x).strip()]


def state_checks(sb: dict, sc: list, err: list, warn: list) -> None:
    names = as_list(sb.get("ten_cong_trinh"))
    if not names:
        err.append("thiếu sb['ten_cong_trinh'] (tên công trình tiếng Anh, vd ['great wall']) — để soát việc tool vẽ sẵn bản hoàn chỉnh")
        return
    base = (sb.get("settings", {}).get("site") or "").lower()
    head = (sb.get("style", "") + " " + base + " " + sb.get("lock", "")).lower()
    for n in names:
        if n in head:
            err.append(f"style/settings/lock có tên công trình '{n}' → tool vẽ sẵn công trình xong ở mọi cảnh; tả bối cảnh trung tính (địa hình, trời), tên chỉ xuất hiện ở cảnh hoan_thanh")
    prev = None
    for s in sc:
        if s.get("real_photo"):
            continue
        sid = s["id"]
        if "da_co" not in s or "chua_co" not in s:
            err.append(f"cảnh {sid}: thiếu 'da_co' / 'chua_co' (đã xây tới đâu / chưa xây gì, CẤM xuất hiện)")
            continue
        da, chua = as_list(s["da_co"]), as_list(s["chua_co"])
        txt = " ".join(b[1] for b in s.get("beats", [])).lower() + " " + s.get("action", "").lower() + " " + s.get("camera", "").lower()
        if not s.get("hoan_thanh"):
            if not chua and sid not in (sc[-3]["id"], sc[-2]["id"], sc[-1]["id"]):
                err.append(f"cảnh {sid}: 'chua_co' rỗng nhưng không phải cảnh hoan_thanh/cuối — công trình chưa xong thì còn phần chưa xây")
            for n in names:
                if n in txt and not any(g in txt for g in GHOST):
                    err.append(f"cảnh {sid}: beats nhắc tên công trình '{n}' trước khi cảnh được đánh dấu hoan_thanh → tool sẽ vẽ bản xong")
        if not s.get("tua_lai"):
            for it in chua:
                if it in txt:
                    # cho phép nếu beat đó nói là khung dây / bản vẽ
                    bad = [b[1] for b in s.get("beats", []) if it in b[1].lower() and not any(g in b[1].lower() for g in GHOST)]
                    if bad or (it in s.get("action", "").lower()):
                        err.append(f"cảnh {sid}: beats nhắc '{it}' nhưng 'chua_co' ghi chưa xây (nếu là khung dây/bản vẽ thì ghi 'ghosted wireframe …')")
        both = set(da) & set(chua)
        if both:
            err.append(f"cảnh {sid}: {sorted(both)} nằm cả trong da_co và chua_co")
        if prev and not s.get("tua_lai"):
            back = set(as_list(prev["da_co"])) & set(chua)
            if back:
                err.append(f"cảnh {sid}: {sorted(back)} đã có ở cảnh {prev['id']} mà lại 'chua_co' (lùi trạng thái) — thêm \"tua_lai\": true nếu là cảnh tua ngược")
        prev = s
    first = next((x for x in sc if not x.get("real_photo")), None)
    if first and not first.get("hoan_thanh") and as_list(first.get("chua_co")) and not (first.get("first_last") or first.get("reference_images")):
        err.append("cảnh 1 mở bằng mặt đất trống: cần ảnh khung đầu (first_last: [\"ref/khung_dau.jpg\"]) tạo bằng Ảnh AI — không có thì tool tự mở bằng hình công trình xong")


def apply_state(sb: dict) -> None:
    """Ghi 'đã có / chưa có' vào mô tả bối cảnh từng cảnh (make_prompts đọc 'setting' dạng chữ)."""
    base = sb.get("settings", {}).get("site", "")
    for s in sb["scenes"]:
        if s.get("real_photo") or "da_co" not in s:
            continue
        da, chua = as_list(s["da_co"]), as_list(s["chua_co"])
        s["setting"] = (f"{base}. ALREADY BUILT at this exact moment: {', '.join(da) if da else 'nothing, completely bare ground'}. "
                        + (f"NOT BUILT YET, must NOT appear anywhere in the shot: {', '.join(chua)}." if chua else "The structure is complete."))
    neg = sb.get("negative", "")
    extra = "a finished completed structure appearing before it is built, parts that are not built yet"
    if extra not in neg:
        sb["negative"] = neg + (", " if neg else "") + extra


def syll(t: str) -> int:
    return len(re.findall(r"\w+", t))


def main() -> None:
    sbp = Path(sys.argv[1]).resolve()
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    sc = sb["scenes"]
    err, warn = [], []
    style = (sb.get("style", "") + " " + sb.get("lock", "")).lower()
    for w in BAD_STYLE:
        if w in style:
            err.append(f"style/lock có chữ '{w}' → hình sẽ ra kiểu quay thật (bỏ đi; chỉ để trong 'negative')")
    if "photorealistic" not in sb.get("negative", "").lower():
        err.append("negative thiếu 'photorealistic, cinematic film look, live-action footage, drone footage' (chép từ hinh-mo-phong.md mục 4)")
    full = " ".join(s.get("narration", "") for s in sc)
    low = full.lower()
    if "giai đoạn" in low:
        err.append("lời kể có chữ 'giai đoạn' → chuyển ý tự nhiên ('Việc đầu tiên là…', 'Tiếp theo là…')")
    nk = low.count("người khôn như bạn") + low.count("người thông minh như bạn")
    if nk > 2:
        err.append(f"'người khôn/thông minh như bạn' xuất hiện {nk} lần (tối đa 2) → thay bằng câu dẫn ngắn (kich-ban.md mục 3)")
    for lead in LEADS:
        if low.count(lead) > 1:
            err.append(f"câu dẫn '{lead}' lặp {low.count(lead)} lần → mỗi câu dẫn 1 lần/video")
    if re.search(r"\d", full):
        warn.append("lời kể có chữ số → đọc bằng chữ cho TTS (vd 'một trăm năm mươi')")
    if "chúc mừng bạn" not in sc[-1].get("narration", "").lower():
        err.append("cảnh cuối phải có 'Xin chúc mừng bạn, bạn đã xây thành công …'")
    if not sc[-1].get("real_photo"):
        err.append("cảnh cuối phải là ảnh thật: thêm \"real_photo\": \"File:…\" (find_photo.py)")
    ng = sum(1 for s in sc if s.get("graphic"))
    if not 2 <= ng <= 4:
        warn.append(f"chữ lớn đặt tên {ng} lần (nên 2–3)")
    if not 10 <= len(sc) <= 18:
        warn.append(f"{len(sc)} cảnh (nên 12–16)")
    for s in sc:
        n = syll(s.get("narration", ""))
        if s.get("real_photo"):
            continue
        if not s.get("beats"):
            err.append(f"cảnh {s['id']}: thiếu 'beats' theo giây (hình khớp lời từng cụm)")
            continue
        if n > 44:
            err.append(f"cảnh {s['id']}: lời kể {n} âm tiết (>44 ≈ >12s, clip 10s sẽ bị làm chậm quá) → rút gọn hoặc tách cảnh")
        elif n > 40:
            warn.append(f"cảnh {s['id']}: lời kể {n} âm tiết, sát ngưỡng (giọng đọc có thể dài hơn clip 10s)")
        elif n < 18:
            warn.append(f"cảnh {s['id']}: lời kể ngắn ({n} âm tiết)")
        bt = " ".join(b[1] for b in s["beats"]).lower()
        nd = sum(1 for b in s["beats"] if any(d in b[1].lower() for d in DEPTH))
        if nd > 2:
            warn.append(f"cảnh {s['id']}: {nd} nhịp có hiệu ứng chiều sâu (một clip 10s nên tối đa 2 — tool khó làm hết)")
        if not any(d in bt for d in DEPTH):
            err.append(f"cảnh {s['id']}: beats không có hiệu ứng chiều sâu (cutaway / X-ray / exploded / section plane…)")
        for w in BAD_STYLE:
            if w in bt:
                err.append(f"cảnh {s['id']}: beats có chữ '{w}'")
        g = s.get("graphic")
        if g and g.get("cue", "").lower() not in s["narration"].lower():
            err.append(f"cảnh {s['id']}: cue chữ lớn '{g.get('cue')}' không có trong lời kể")
    state_checks(sb, sc, err, warn)
    for w in warn:
        print("  ⚠ " + w)
    if err:
        for e in err:
            print("  ✗ " + e)
        print(f"\nSTOP: {len(err)} lỗi theo luật vàng — sửa build_sb.py rồi chạy lại prep.py.")
        sys.exit(1)
    apply_state(sb)
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(S / "make_prompts.py"), str(sbp)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        sys.exit("STOP: make_prompts.py lỗi")
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    tool = dict(sb)
    tool["scenes"] = [s for s in sb["scenes"] if not s.get("real_photo")]
    (sbp.parent / "storyboard_tool.json").write_text(json.dumps(tool, ensure_ascii=False, indent=1), encoding="utf-8")
    sec = sum(syll(s.get("narration", "")) for s in sc) / 3.5
    print(f"OK: {len(sc)} cảnh (~{sec:.0f}s lời kể), {len(tool['scenes'])} cảnh tạo trong tool → {sbp.parent / 'storyboard_tool.json'}")


if __name__ == "__main__":
    main()
