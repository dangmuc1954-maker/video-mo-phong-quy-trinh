"""Word timing for a voice file made elsewhere (eg. the TTS page of the AI VIDEO LIBRARY tool), offline.

faster-whisper gives word timestamps; the text is then replaced by the script (correct spelling) with
align_to_script, so words.json has exact script words + real timing + beat (paragraph) index.

Usage:
  python align_voice.py voice.mp3 script.txt -o words.json [--model small]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import (align_to_script, probe_duration, read_script_paragraphs,  # noqa: E402
                        save_words, script_tokens)


def align(voice: Path, script: Path, out: Path, model_name: str = "small") -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Cần faster-whisper: pip install faster-whisper")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    paras = read_script_paragraphs(script)
    # no initial_prompt: feeding the script as a prompt made whisper skip/hallucinate most of the audio
    segs, _ = model.transcribe(str(voice), language="vi", word_timestamps=True, vad_filter=False)
    asr = []
    for s in segs:
        for w in s.words or []:
            t = w.word.strip()
            if t:
                asr.append({"text": t, "start": w.start, "end": w.end, "confidence": round(w.probability, 3), "beat": None})
    if not asr:
        sys.exit("Không nhận dạng được từ nào trong file giọng.")
    words = align_to_script(asr, script_tokens(paras))
    n_interp = sum(1 for w in words if w.get("aligned") == "interpolated")
    save_words(words, out, {"source": f"faster-whisper:{model_name}+script", "timing": "verified",
                            "duration_seconds": round(probe_duration(voice), 3), "beats": len(paras),
                            "interpolated_words": n_interp})
    print(f"Timing từ giọng thật: {len(words)} từ ({n_interp} từ nội suy) → {out}")
    if n_interp > 0.15 * len(words):
        print(f"CẢNH BÁO: {n_interp}/{len(words)} từ phải nội suy — giọng có thể đọc khác kịch bản hoặc nhận dạng lỗi, kiểm tra lại trước khi dựng.")
    return words


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    ap.add_argument("script")
    ap.add_argument("-o", "--out", default="words.json")
    ap.add_argument("--model", default="small")
    a = ap.parse_args()
    align(Path(a.voice), Path(a.script), Path(a.out), a.model)


if __name__ == "__main__":
    main()
