"""Estimate word timing from a script when no TTS/ASR is available (marked provisional).

Usage:
  python provisional_timing.py script.txt -o projects/demo [--rate 3.2] [--silence]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import need, read_script_paragraphs, run, save_words, script_tokens  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("-o", "--out", default=".")
    ap.add_argument("--rate", type=float, default=3.2, help="âm tiết/giây")
    ap.add_argument("--silence", action="store_true", help="tạo voice.wav im lặng đúng độ dài")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paras = read_script_paragraphs(Path(args.script))
    toks = script_tokens(paras)
    syl = 1.0 / args.rate
    t, words, prev_beat = 0.25, [], 0
    for text, beat in toks:
        if beat != prev_beat:
            t += 0.45  # paragraph pause
            prev_beat = beat
        words.append({"text": text, "start": t, "end": t + syl * 0.92, "confidence": None, "beat": beat})
        t += syl
        if text[-1] in ".!?…":
            t += 0.35
        elif text[-1] in ",;:":
            t += 0.18
    duration = round(t + 0.5, 2)
    save_words(words, out / "words.json", {"source": "provisional_estimate", "timing": "provisional",
                                            "duration_seconds": duration, "beats": len(paras)})
    if args.silence:
        need("ffmpeg")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", duration, out / "voice.wav"])
    print(f"Timing tạm tính: {len(words)} từ, {duration}s → {out / 'words.json'}")


if __name__ == "__main__":
    main()
