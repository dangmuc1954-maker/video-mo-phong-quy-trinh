"""Hậu kỳ CapCut một lệnh: cảnh đã cắt + lớp chữ (sub story_pop, chữ lớn) + giọng + SFX + nhạc nền, rồi kiểm SFX.

  python post_capcut.py projects/<slug>

CapCut phải TẮT (đang mở → in STOP: hỏi anh tắt, KHÔNG tự tắt). Các bước:
  1) story_render.py --capcut-layers   (cắt cảnh khớp giọng + lớp chữ trong suốt)
  2) capcut_post.py                    (draft "<title> (hau ky)")
  0) gắn chuyển cảnh CapCut cho từng ranh giới cảnh đổi bối cảnh / cao trào (ghi transition_in vào storyboard.json)
  3) render/timeline.json tối giản     (mốc cảnh từ sync.json, mốc chữ lớn từ words.json)
  4) rich_audio.py                     (SFX cho MỌI hành động + ambient từng cảnh + whoosh/swish chuyển cảnh + chime mở/chốt + nhạc nền dịu; --legacy-sfx dùng bản cũ)
  5) capcut_sfx_check.py               (phải in OK)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SK = Path(__file__).resolve().parents[2]
A = SK / "ai-semantic-video-editor" / "scripts"
V = SK / "video-tai-lieu" / "scripts"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run(args, tail=6):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    out = (r.stdout or "") + (r.stderr or "")
    print("\n".join(out.strip().splitlines()[-tail:]))
    return r.returncode, out


# Dùng MỌI chuyển cảnh CapCut có sẵn, kể cả loại Pro (anh yêu cầu 13/11/2026: "cứ mở chuyển cảnh Pro, không chặn"). Anh tự lo gói Pro.
TRANS_CYCLE = ["Phóng to rồi mờ dần", "Quét tro", "Xoáy thuận chiều kim ĐH", "Tầm nhìn nghiêng", "Chuyển ảnh chớp nháy", "Sao nhấp nháy", "Tách giữa", "Hộp xoay"]


def enrich_transitions(sb: dict, sbp: Path) -> int:
    """Gắn chuyển cảnh CapCut cho ranh giới đổi bối cảnh/thời điểm; cảnh liền mạch cùng bối cảnh giữ cắt thẳng. Không ghi đè cảnh đã có transition_in."""
    n, k = 0, 0
    prev_set, prev_txt = None, ""
    for i, sc in enumerate(sb["scenes"]):
        txt = (sc.get("setting", "") + " " + " ".join(b[1] for b in (sc.get("beats") or [])) + " " + sc.get("action", "")).lower()
        night = any(w in txt for w in ("night", "moon", "firefl", "đêm"))
        dawn = any(w in txt for w in ("dawn", "sunrise", "bình minh"))
        storm = any(w in txt for w in ("storm", "heavy rain", "rain and wind", "bão"))
        last = i == len(sb["scenes"]) - 1
        if i > 0 and not sc.get("transition_in"):
            changed = sc.get("setting") != prev_set or (night, dawn, storm) != prev_txt
            if last:
                sc["transition_in"] = "Lóa sáng rạng rỡ"
            elif dawn and prev_txt != (False, True, False):
                sc["transition_in"] = "Lóa sáng rạng rỡ"
            elif storm and prev_txt != (False, False, True):
                sc["transition_in"] = "Quét tro"
            elif night and prev_txt != (True, False, False):
                sc["transition_in"] = "Phóng to rồi mờ dần"
            elif changed:
                sc["transition_in"] = TRANS_CYCLE[k % len(TRANS_CYCLE)]
                k += 1
            if sc.get("transition_in"):
                n += 1
        prev_set, prev_txt = sc.get("setting"), (night, dawn, storm)
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def norm(t: str) -> str:
    return re.sub(r"[^\w]+", " ", t.lower()).strip()


def main() -> None:
    proj = Path(sys.argv[1]).resolve()
    sbp = proj / "storyboard.json"
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    force = "--force" in sys.argv      # chỉ khi CapCut đang ở màn hình chính, KHÔNG mở dự án này
    if not force and os.name == "nt" and "CapCut.exe" in subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True, errors="replace").stdout:
        sys.exit("STOP: CapCut đang mở — HỎI ANH cho tắt (không tự tắt), rồi chạy lại.")
    nt = enrich_transitions(sb, sbp)
    print(f"== 0/5 chuyển cảnh CapCut: {nt} ranh giới")
    print("== 1/5 cắt cảnh + lớp chữ")
    rc, _ = run([A / "story_render.py", sbp, "--capcut-layers"])
    if rc:
        sys.exit("STOP: story_render --capcut-layers lỗi")
    print("== 2/5 draft CapCut")
    title = (sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else f"{sb.get('title', proj.name)} (hau ky)")
    rc, _ = run([A / "capcut_post.py", sbp, "--title", title] + (["--force"] if force else []))
    if rc:
        sys.exit("STOP: capcut_post lỗi")
    print("== 3/5 mốc SFX")
    sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
    words = json.loads((proj / "narration" / "words.json").read_text(encoding="utf-8"))
    words = words["words"] if isinstance(words, dict) else words
    slots = {str(s["id"]): s["slot"] for s in sync["scenes"]}
    scenes = []
    n = len(sb["scenes"])
    for i, s in enumerate(sb["scenes"]):
        sid = str(s["id"])
        st, en = slots[sid]
        d = {"id": sid, "start": st, "end": en, "module": "screen", "p": {}, "keywords": [], "callouts": []}
        if i == 0 or i == n - 2:
            d["climax"] = True          # mở đầu xé toạc / toàn cảnh hoàn thành
        if s.get("real_photo"):
            d["transition_in"] = "zoom"  # chuyển sang hình thật
        g = s.get("graphic")
        if g:
            cue = norm(g["cue"]).split()
            ws = [w for w in words if st - .2 <= w["start"] <= en]
            at = None
            for j in range(len(ws)):
                if [norm(w["text"]) for w in ws[j:j + len(cue)]] == cue:
                    at = ws[j]["start"]
                    break
            if at is not None:
                d["keywords"].append({"text": g["cue"], "effect": "stamp_slam", "at": round(at, 2)})
            else:
                print(f"  ⚠ cảnh {sid}: không tìm thấy cụm '{g['cue']}' trong giọng đọc — bỏ tiếng dấu ấn")
        scenes.append(d)
    (proj / "render").mkdir(exist_ok=True)
    tl = {"title": sb.get("title", proj.name), "duration": max(v[1] for v in slots.values()), "scenes": scenes,
          "W": sb.get("canvas", [1080, 1920])[0], "H": sb.get("canvas", [1080, 1920])[1]}
    (proj / "render" / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print("== 4/5 SFX + nhạc")
    if "--legacy-sfx" in sys.argv:
        rc, _ = run([V / "capcut_sfx_auto.py", proj, "--title", title])
    else:
        rc, _ = run([Path(__file__).resolve().parent / "rich_audio.py", proj, "--title", title], 6)
    if rc:
        sys.exit("STOP: bước âm thanh dừng — đọc lý do ở trên")
    print("== 5/5 kiểm SFX")
    rc, out = run([A / "capcut_sfx_check.py", sbp, "--title", title], 4)
    last = out.strip().splitlines()[-1] if out.strip() else ""
    if not last.startswith("OK"):
        sys.exit("STOP: capcut_sfx_check chưa OK")
    print(f"\nOK: draft '{title}' sẵn sàng — mở CapCut, mở project này, Xuất → Xuất (1080p).")


if __name__ == "__main__":
    main()
