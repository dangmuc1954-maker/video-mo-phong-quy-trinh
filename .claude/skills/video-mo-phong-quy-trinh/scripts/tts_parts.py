"""Giọng kể dài > 1000 ký tự: chia theo ranh giới cảnh, tạo từng phần qua macro TTS của tool, KIỂM từng phần, ghép, đồng bộ.

  python tts_parts.py projects/<slug>/storyboard.json [--only-part 2] [--max 990]

- Chia thành ít phần nhất (mỗi phần ≤ --max ký tự), cân độ dài giữa các phần.
- Mỗi phần: xoá narration/voice.mp3 cũ → tts_macro.py --auto --no-sync --text-file part<k>.txt → kiểm file mới tồn tại
  và độ dài hợp lý (≈ số âm tiết / 3.5 giây, cho phép ±45%) → lưu voice_part<k>.mp3. Sai → STOP (không ghép).
- Ghép (nghỉ 0.25s giữa các phần) → voice_all.mp3 → story_voice.py --voice-file → narration/sync.json, words.json.
- Kiểm sync: tổng thời lượng khớp, không cảnh nào > 16s. In OK / STOP.
Macro chỉ click / Ctrl+A / Ctrl+V / Esc (an toàn tool). Anh đừng đụng chuột/bàn phím lúc chạy.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
A = Path(__file__).resolve().parents[2] / "ai-semantic-video-editor" / "scripts"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def dur(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def syll(t: str) -> int:
    return len(re.findall(r"\w+", t))


def split(scenes, mx):
    L = [len(s["narration"]) + 1 for s in scenes]
    n = len(L)
    for k in range(1, 6):  # ít phần nhất, cân nhất
        best = None

        def rec(start, parts, cuts):
            nonlocal best
            if parts == 1:
                seg = sum(L[start:])
                if seg <= mx:
                    m = max([seg] + [sum(L[a:b]) for a, b in zip([0] + cuts, cuts)])
                    if best is None or m < best[0]:
                        best = (m, cuts[:])
                return
            for c in range(start + 1, n):
                if sum(L[start:c]) > mx:
                    break
                rec(c, parts - 1, cuts + [c])
        rec(0, k, [])
        if best:
            cuts = best[1]
            bounds = [0] + cuts + [n]
            return [list(range(a, b)) for a, b in zip(bounds, bounds[1:])]
    sys.exit("STOP: có cảnh có lời kể > giới hạn một phần TTS — rút gọn cảnh đó.")


def clamp_holds(sbp: Path) -> None:
    """Chữ lớn (graphic) không được lố sang cảnh kế: hold ≤ (hết cảnh − giây bật chữ − 0.15)."""
    nd = sbp.parent / "narration"
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    sync = json.loads((nd / "sync.json").read_text(encoding="utf-8"))
    words = json.loads((nd / "words.json").read_text(encoding="utf-8"))
    words = words["words"] if isinstance(words, dict) else words
    slots = {str(x["id"]): x["slot"] for x in sync["scenes"]}
    norm = lambda t: re.sub(r"[^\w]+", " ", t.lower()).strip()
    changed = False
    for sc in sb["scenes"]:
        g = sc.get("graphic")
        if not g:
            continue
        st, en = slots[str(sc["id"])]
        cue = norm(g["cue"]).split()
        ws = [w for w in words if st - .2 <= w["start"] <= en]
        at = next((ws[j]["start"] for j in range(len(ws)) if [norm(w["text"]) for w in ws[j:j + len(cue)]] == cue), None)
        if at is None:
            print(f"  ⚠ cảnh {sc['id']}: không thấy cụm '{g['cue']}' trong giọng đọc")
            continue
        mx = round(en - at - 0.15, 2)
        if g.get("hold", 2.6) > mx:
            new = max(1.0, mx)
            print(f"  chữ lớn cảnh {sc['id']}: bật {at:.1f}s, hết cảnh {en:.1f}s → hold {g.get('hold')} → {new}")
            g["hold"] = new
            changed = True
    if changed:
        sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
        subprocess.run([sys.executable, str(A / "story_voice.py"), str(sbp), "--sync-only"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
        print("  đã tính lại narration/timeline.json (story_voice --sync-only)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--only-part", type=int)
    ap.add_argument("--max", type=int, default=990)
    ap.add_argument("--clamp-only", action="store_true", help="chỉ chỉnh thời gian giữ chữ lớn theo sync.json hiện có")
    a = ap.parse_args()
    sbp = Path(a.storyboard).resolve()
    if a.clamp_only:
        clamp_holds(sbp)
        print("OK: đã chỉnh thời gian giữ chữ lớn")
        return
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    nd = sbp.parent / "narration"
    nd.mkdir(exist_ok=True)
    groups = split(sb["scenes"], a.max)
    texts = [" ".join(sb["scenes"][i]["narration"] for i in g) for g in groups]
    for k, (g, t) in enumerate(zip(groups, texts), 1):
        (nd / f"part{k}.txt").write_text(t, encoding="utf-8")
        print(f"phần {k}: cảnh {g[0] + 1}–{g[-1] + 1}, {len(t)} ký tự")
    todo = [a.only_part] if a.only_part else range(1, len(groups) + 1)
    for k in todo:
        out = nd / f"voice_part{k}.mp3"
        for attempt in (1, 2):
            v = nd / "voice.mp3"
            if v.exists():
                v.unlink()
            r = subprocess.run([sys.executable, str(A / "tts_macro.py"), str(sbp), "--auto", "--no-sync", "--text-file", str(nd / f"part{k}.txt")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
            print("\n".join((r.stdout + r.stderr).strip().splitlines()[-3:]))
            exp = syll(texts[k - 1]) / 3.5
            d = dur(v) if v.exists() else 0
            if v.exists() and 0.55 * exp <= d <= 1.45 * exp:
                v.replace(out)
                print(f"  ✓ phần {k}: {d:.1f}s (dự kiến ~{exp:.0f}s)")
                break
            print(f"  ✗ phần {k} lần {attempt}: file {'không có' if not v.exists() else f'{d:.1f}s, dự kiến ~{exp:.0f}s'}")
        else:
            sys.exit(f"STOP: phần {k} không tạo được giọng — xem ảnh projects/<slug>/_macro/STOP_tts_*.jpg / ocr_tts_button.png, "
                     f"xử lý (đóng menu/hộp thoại bằng Esc) rồi chạy lại: tts_parts.py {a.storyboard} --only-part {k}")
    parts = [nd / f"voice_part{k}.mp3" for k in range(1, len(groups) + 1)]
    miss = [p.name for p in parts if not p.exists()]
    if miss:
        sys.exit(f"STOP: còn thiếu {miss} — chạy --only-part cho phần đó.")
    ins = sum([["-i", str(p)] for p in parts], [])
    fc = "".join(f"[{i}]aresample=44100{',apad=pad_dur=0.25' if i < len(parts) - 1 else ''}[a{i}];" for i in range(len(parts)))
    fc += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1"
    allf = nd / "voice_all.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-b:a", "192k", str(allf)], check=True)
    r = subprocess.run([sys.executable, str(A / "story_voice.py"), str(sbp), "--voice-file", str(allf)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    print("\n".join((r.stdout + r.stderr).strip().splitlines()[-4:]))
    sync = json.loads((nd / "sync.json").read_text(encoding="utf-8"))
    total = dur(allf)
    long_ = [(s["id"], round(s["slot"][1] - s["slot"][0], 1)) for s in sync["scenes"] if s["slot"][1] - s["slot"][0] > 16]
    if long_ or abs(sync["scenes"][-1]["slot"][1] - total) > 3:
        sys.exit(f"STOP: đồng bộ bất thường (cảnh quá dài {long_}, tổng {total:.1f}s) — kiểm voice_part*.mp3.")
    clamp_holds(sbp)
    print(f"OK: giọng kể {total:.1f}s, {len(sync['scenes'])} cảnh đồng bộ → {nd / 'sync.json'}")


if __name__ == "__main__":
    main()
