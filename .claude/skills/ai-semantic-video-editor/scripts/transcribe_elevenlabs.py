"""Video/audio -> words.json using ElevenLabs Speech-to-Text (Scribe), optional script correction.

Usage:
  python transcribe_elevenlabs.py review.mp4 -o words.json [--script script.txt] [--model scribe_v1]
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import (ELEVEN_BASE, align_to_script, get_api_key, need, probe_duration,  # noqa: E402
                        read_script_paragraphs, run, save_words, script_tokens)

import requests  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("-o", "--out", default="words.json")
    ap.add_argument("--script", help="Kịch bản gốc để sửa chính tả theo kịch bản")
    ap.add_argument("--model", default="scribe_v1")
    ap.add_argument("--language", default="vi")
    args = ap.parse_args()

    media = Path(args.media)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    key = get_api_key(out.parent)
    need("ffmpeg")

    with tempfile.TemporaryDirectory() as td:
        audio = Path(td) / "audio.mp3"
        run(["ffmpeg", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", audio])
        print("Đang nhận dạng giọng nói…")
        with open(audio, "rb") as f:
            r = requests.post(f"{ELEVEN_BASE}/v1/speech-to-text", headers={"xi-api-key": key},
                              data={"model_id": args.model, "language_code": args.language,
                                    "timestamps_granularity": "word", "tag_audio_events": "false"},
                              files={"file": ("audio.mp3", f, "audio/mpeg")}, timeout=900)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs lỗi {r.status_code}: {r.text[:500]}")
    data = r.json()

    words = []
    for w in data.get("words", []):
        if w.get("type", "word") != "word" or not w.get("text", "").strip():
            continue
        lp = w.get("logprob")
        words.append({"text": w["text"].strip(), "start": w["start"], "end": w["end"],
                      "confidence": round(math.exp(lp), 3) if lp is not None else None, "beat": None})

    meta = {"source": f"elevenlabs_stt:{args.model}", "timing": "verified",
            "duration_seconds": round(probe_duration(media), 3), "media": str(media)}
    if args.script:
        paras = read_script_paragraphs(Path(args.script))
        words = align_to_script(words, script_tokens(paras))
        meta["script_corrected"] = True
        n_interp = sum(1 for w in words if w.get("aligned") == "interpolated")
        meta["interpolated_words"] = n_interp
        if n_interp:
            print(f"Lưu ý: {n_interp} từ phải nội suy timing (lời nói khác kịch bản), hãy kiểm tra lại.")
    low = [w["text"] for w in words if w.get("confidence") is not None and w["confidence"] < 0.6]
    if low:
        print(f"Từ có độ tin cậy thấp ({len(low)}): {', '.join(low[:20])}")
    save_words(words, out, meta)
    print(f"Xong: {len(words)} từ → {out}")


if __name__ == "__main__":
    main()
