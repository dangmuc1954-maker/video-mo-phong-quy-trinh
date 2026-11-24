"""Vietnamese script -> voice.mp3 + words.json (word timing from ElevenLabs alignment).

Usage:
  python tts_elevenlabs.py --list-voices
  python tts_elevenlabs.py --voice VOICE_ID --sample "Xin chào, đây là giọng thử." -o .
  python tts_elevenlabs.py script.txt --voice VOICE_ID -o projects/demo
"""
from __future__ import annotations

import argparse
import base64
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import (ELEVEN_BASE, align_to_script, get_api_key, need, probe_duration,  # noqa: E402
                        read_script_paragraphs, run, save_words, script_tokens)

import requests  # noqa: E402


def list_voices(key: str) -> None:
    r = requests.get(f"{ELEVEN_BASE}/v1/voices", headers={"xi-api-key": key}, timeout=60)
    r.raise_for_status()
    for v in r.json().get("voices", []):
        labels = ", ".join(f"{k}={val}" for k, val in (v.get("labels") or {}).items())
        print(f"{v['voice_id']}  {v['name']:<28} {labels}")


def tts_chunk(key, voice, text, args, prev_text=None, next_text=None) -> tuple[bytes, dict]:
    settings = {"stability": args.stability, "similarity_boost": args.similarity,
                "style": args.style, "use_speaker_boost": True}
    if abs(args.speed - 1.0) > 1e-6:
        settings["speed"] = args.speed
    body = {"text": text, "model_id": args.model, "voice_settings": settings}
    if args.language_code:
        body["language_code"] = args.language_code
    if args.model != "eleven_v3":
        if prev_text:
            body["previous_text"] = prev_text
        if next_text:
            body["next_text"] = next_text
    r = requests.post(f"{ELEVEN_BASE}/v1/text-to-speech/{voice}/with-timestamps",
                      params={"output_format": "mp3_44100_128"},
                      headers={"xi-api-key": key, "Content-Type": "application/json"},
                      json=body, timeout=300)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs lỗi {r.status_code}: {r.text[:500]}")
    data = r.json()
    return base64.b64decode(data["audio_base64"]), (data.get("alignment") or data.get("normalized_alignment"))


def words_from_alignment(al: dict, offset: float) -> list[dict]:
    chars = al["characters"]
    st = al["character_start_times_seconds"]
    en = al["character_end_times_seconds"]
    words, cur, t0, t1 = [], "", None, None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                words.append({"text": cur, "start": t0 + offset, "end": t1 + offset, "confidence": 1.0})
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = s
        cur += c
        t1 = e
    if cur:
        words.append({"text": cur, "start": t0 + offset, "end": t1 + offset, "confidence": 1.0})
    return words


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("--voice")
    ap.add_argument("-o", "--out", default=".")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--language-code", default=None, help="vd: vi (chỉ một số model hỗ trợ)")
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--similarity", type=float, default=0.75)
    ap.add_argument("--style", type=float, default=0.3)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--max-chars", type=int, default=2500)
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--sample", help="Đọc thử một câu ngắn để duyệt giọng")
    ap.add_argument("--timeline", help="Sau khi lồng tiếng, tự khớp lại timeline.json này theo giọng mới")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    key = get_api_key(out)

    if args.list_voices:
        list_voices(key)
        return
    if not args.voice:
        sys.exit("Cần --voice VOICE_ID (xem --list-voices).")
    if args.sample:
        audio, _ = tts_chunk(key, args.voice, args.sample, args)
        p = out / f"sample_{args.voice[:8]}.mp3"
        p.write_bytes(audio)
        print(f"Đã tạo {p}")
        return
    if not args.script:
        sys.exit("Cần file kịch bản.")

    paras = read_script_paragraphs(Path(args.script))
    if not paras:
        sys.exit("Kịch bản trống.")

    # group paragraphs into API-sized chunks
    chunks, cur = [], []
    for p in paras:
        if cur and len("\n\n".join(cur + [p])) > args.max_chars:
            chunks.append(cur)
            cur = []
        cur.append(p)
    chunks.append(cur)

    need("ffmpeg")
    raw_words, offset = [], 0.0
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, ch in enumerate(chunks):
            text = "\n\n".join(ch)
            prev_t = chunks[i - 1][-1] if i > 0 else None
            next_t = chunks[i + 1][0] if i + 1 < len(chunks) else None
            print(f"Lồng tiếng phần {i + 1}/{len(chunks)} ({len(text)} ký tự)…")
            audio, al = tts_chunk(key, args.voice, text, args, prev_t, next_t)
            part = Path(td) / f"part{i:03d}.mp3"
            part.write_bytes(audio)
            parts.append(part)
            raw_words += words_from_alignment(al, offset)
            offset += probe_duration(part)
        voice = out / "voice.mp3"
        if len(parts) == 1:
            voice.write_bytes(parts[0].read_bytes())
        else:
            lst = Path(td) / "list.txt"
            lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:a", "libmp3lame", "-b:a", "192k", voice])

    words = align_to_script(raw_words, script_tokens(paras))
    duration = probe_duration(out / "voice.mp3")
    save_words(words, out / "words.json", {"source": "elevenlabs_tts", "timing": "verified",
                                            "model": args.model, "voice": args.voice,
                                            "duration_seconds": round(duration, 3), "beats": len(paras)})
    print(f"Xong: {out / 'voice.mp3'} ({duration:.2f}s), {len(words)} từ, {len(paras)} beat → {out / 'words.json'}")
    if args.timeline:
        from retime_timeline import retime
        retime(Path(args.timeline), out / "words.json", out / "voice.mp3")


if __name__ == "__main__":
    main()
