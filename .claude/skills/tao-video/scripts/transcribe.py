"""Nhận dạng lời thoại trong từng cảnh (faster-whisper) để làm vietsub.

python transcribe.py projects/<slug>/storyboard.json [--model small]

Ghi projects/<slug>/transcript.json:
  {"1": [{"start": 2.1, "end": 5.1, "text": "Ha ha ha! You're so slow!"}], "3": [] ...}
Cảnh rỗng = không có thoại → dùng chú thích cốt truyện.
Sau đó Claude dịch sang tiếng Việt và ghi vào storyboard: scenes[i]["lines"] = [{"start","end","text"}].
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("storyboard")
ap.add_argument("--model", default="small")
a = ap.parse_args()

from faster_whisper import WhisperModel  # noqa: E402


def load_model():
    # GPU nhanh hơn nhưng cần cublas của CUDA 12; thiếu thì tự chuyển CPU (clip 10s vẫn chỉ vài giây)
    try:
        return WhisperModel(a.model, device="cuda", compute_type="float16"), "cuda"
    except Exception:
        return WhisperModel(a.model, device="cpu", compute_type="int8"), "cpu"


base = os.path.dirname(os.path.abspath(a.storyboard))
story = json.load(open(a.storyboard, encoding="utf-8"))
model, dev = load_model()
out = {}
for sc in story["scenes"]:
    p = os.path.join(base, "1-canh", sc["clip"])
    try:
        segs, info = model.transcribe(p, vad_filter=True)
        segs = list(segs)
    except RuntimeError:  # thiếu thư viện CUDA lúc chạy → CPU
        model, dev = WhisperModel(a.model, device="cpu", compute_type="int8"), "cpu"
        segs, info = model.transcribe(p, vad_filter=True)
        segs = list(segs)
    lines = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
             for s in segs if s.no_speech_prob < 0.6 and s.text.strip()]
    out[str(sc["id"])] = lines
    print(f"Cảnh {sc['id']}: " + (" | ".join(f"{l['start']}-{l['end']} {l['text']}" for l in lines) or "(không thoại)"))

json.dump(out, open(os.path.join(base, "transcript.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[{dev}] → {os.path.join(base, 'transcript.json')}")
