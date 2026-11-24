"""Căn mốc thời gian phụ đề theo TỪ đã nói (faster-whisper word timestamps).

python align_lines.py projects/<slug>/storyboard.json [--model small] [--lang vi]

Dùng khi lời đọc/lời thoại đã biết trước (kịch bản) và `scenes[i].lines` đã có chữ chuẩn:
script nghe lại clip, lấy mốc từng từ, rồi đặt start/end của mỗi dòng phụ đề vào đúng lúc
câu đó được nói (chia theo số chữ cái, nên chịu được lỗi nghe nhầm vài chữ).
"""
import argparse
import json
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("storyboard")
ap.add_argument("--model", default="small")
ap.add_argument("--lang", default="vi")
a = ap.parse_args()

from faster_whisper import WhisperModel  # noqa: E402

model = WhisperModel(a.model, device="cpu", compute_type="int8")  # CUDA của máy thiếu cublas → dùng CPU


def letters(t):
    t = unicodedata.normalize("NFD", t.lower())
    return len(re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn")))


sb = json.load(open(a.storyboard, encoding="utf-8"))
proj = os.path.dirname(os.path.abspath(a.storyboard))
for sc in sb["scenes"]:
    lines = sc.get("lines") or []
    if not lines:
        continue
    clip = os.path.join(proj, "1-canh", sc["clip"])
    segs, _ = model.transcribe(clip, language=a.lang, word_timestamps=True, vad_filter=True)
    words = [w for s in segs for w in (s.words or []) if letters(w.word)]
    if not words:
        print(f"Cảnh {sc['id']}: không nghe được từ nào — giữ mốc cũ")
        continue
    # trục "chữ cái đã nói" → thời gian
    cum, marks = 0, []
    for w in words:
        n = letters(w.word)
        marks.append((cum, w.start))
        cum += n
        marks.append((cum, w.end))
    total_spoken = cum
    want = [letters(l["text"]) for l in lines]
    scale = total_spoken / max(1, sum(want))

    def time_at(pos):
        for (p0, t0), (p1, t1) in zip(marks, marks[1:]):
            if p0 <= pos <= p1:
                return t0 if p1 == p0 else t0 + (t1 - t0) * (pos - p0) / (p1 - p0)
        return marks[-1][1]

    pos = 0
    for l, n in zip(lines, want):
        l["start"] = round(time_at(pos), 2)
        pos += n * scale
        l["end"] = round(time_at(pos), 2)
    print(f"Cảnh {sc['id']}: " + " | ".join(f"{l['start']}-{l['end']} {l['text']}" for l in lines))

json.dump(sb, open(a.storyboard, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
