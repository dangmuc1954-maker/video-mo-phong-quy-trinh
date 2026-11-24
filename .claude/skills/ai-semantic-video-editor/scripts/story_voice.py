"""Voice a tao-video storyboard with ElevenLabs and compute per-scene timing (narration/sync.json).

Each scene's narration text = scene["narration"] (or scene["dialogue"] with --from-dialogue).
The whole story is read in ONE voice in one pass, then every scene gets a time slot that starts
when its first word is spoken, so scenes, subtitles and graphics follow the real voice.

Usage:
  python story_voice.py projects/<slug>/storyboard.json --voice VOICE_ID [--speed 0.95] [--model eleven_multilingual_v2]
  python story_voice.py projects/<slug>/storyboard.json --provisional        # no API key: estimated timing
  python story_voice.py projects/<slug>/storyboard.json --sync-only          # recompute sync.json from existing words.json
  python story_voice.py projects/<slug>/storyboard.json --voice-file giong.mp3   # voice made elsewhere (tool TTS page)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_subs import chunk_words, split_lines  # noqa: E402
from vse_common import load_words, normalize_token, probe_duration  # noqa: E402

TAIL = 0.6  # seconds kept after the last word


def narration_of(sc: dict, from_dialogue: bool) -> str:
    t = sc.get("narration")
    if not t and from_dialogue:
        t = sc.get("dialogue")
    return (t or "").strip()


def find_cue(words: list[dict], cue: str) -> float | None:
    k = [normalize_token(x) for x in cue.split() if normalize_token(x)]
    norm = [normalize_token(w["text"]) for w in words]
    for i in range(len(norm) - len(k) + 1):
        if k and norm[i:i + len(k)] == k:
            return words[i]["start"]
    return None


def build_sync(story: dict, scenes: list[dict], words: list[dict], voice: Path, timing: str, portrait: bool) -> dict:
    vdur = probe_duration(voice)
    by_beat: dict[int, list[dict]] = {}
    for w in words:
        by_beat.setdefault(w["beat"], []).append(w)
    if len(by_beat) != len(scenes):
        sys.exit(f"Số đoạn giọng ({len(by_beat)}) khác số cảnh có lời kể ({len(scenes)}).")
    starts = [by_beat[i][0]["start"] for i in range(len(scenes))]
    total = round(max(vdur, words[-1]["end"] + TAIL), 3)
    line_chars = 28 if portrait else 42
    out = []
    for i, sc in enumerate(scenes):
        a = 0.0 if i == 0 else starts[i]
        b = starts[i + 1] if i + 1 < len(scenes) else total
        ws = by_beat[i]
        lines = []
        chunks = chunk_words(ws, max_chars=line_chars * 2)
        for ci, ch in enumerate(chunks):
            end = ch[-1]["end"] + 0.3
            if ci + 1 < len(chunks):
                end = min(end, chunks[ci + 1][0]["start"])
            end = min(max(end, ch[-1]["end"]), b)
            brk = split_lines([w["text"] for w in ch], line_chars)
            text = "".join(w["text"] + ("\n" if j == brk else " ") for j, w in enumerate(ch)).strip()
            lines.append({"start": round(ch[0]["start"], 3), "end": round(end, 3), "text": text})
        g = sc.get("graphic")
        graphic = None
        if g:
            s = find_cue(ws, g["cue"]) if g.get("cue") else None
            if g.get("cue") and s is None:
                print(f"CẢNH BÁO: cảnh {sc['id']}: không thấy từ khóa '{g['cue']}' trong lời kể, graphic đặt ở đầu cảnh.")
            s = max(a, (s if s is not None else a + 0.3) - 0.1)
            e = min(total, s + float(g.get("hold", max(2.5, b - s))))   # may run into the next scene to stay readable
            graphic = {**{k: v for k, v in g.items() if k not in ("cue", "hold")}, "start": round(s, 3), "end": round(e, 3)}
            if story.get("caption_top") and graphic.get("anchor", "top") in ("top", "upper_left", "upper_right"):
                graphic["anchor"] = "center"      # the top band is taken by the caption
        out.append({"id": sc["id"], "slot": [round(a, 3), round(b, 3)], "lines": lines,
                    "first_word": ws[0]["start"], "last_word": ws[-1]["end"], "graphic": graphic})
    gs = [x["graphic"] for x in out if x.get("graphic")]
    for g1, g2 in zip(gs, gs[1:]):            # never overlap the next graphic
        if g1["end"] > g2["start"] - 0.1:
            g1["end"] = round(max(g1["start"] + 0.5, g2["start"] - 0.1), 3)
    return {"voice": voice.name, "timing": timing, "duration": total, "scenes": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--voice")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--speed", type=float, default=0.95)
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--style", type=float, default=0.3)
    ap.add_argument("--from-dialogue", action="store_true", help="dùng scene.dialogue khi không có scene.narration")
    ap.add_argument("--provisional", action="store_true")
    ap.add_argument("--sync-only", action="store_true")
    ap.add_argument("--voice-file", help="file giọng đã tạo sẵn (vd từ mục Giọng đọc TTS của tool); lấy timing bằng faster-whisper")
    ap.add_argument("--whisper-model", default="small")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    story = json.loads(sp.read_text(encoding="utf-8"))
    ndir = sp.parent / "narration"
    ndir.mkdir(exist_ok=True)
    scenes = [sc for sc in story["scenes"] if narration_of(sc, a.from_dialogue)]
    missing = [sc["id"] for sc in story["scenes"] if not narration_of(sc, a.from_dialogue)]
    if missing:
        sys.exit(f"Cảnh {missing} chưa có 'narration' (lời kể). Thêm lời kể cho mọi cảnh rồi chạy lại.")

    script = ndir / "script.txt"
    script.write_text("\n\n".join(f"# cảnh {sc['id']}\n{narration_of(sc, a.from_dialogue)}" for sc in scenes) + "\n",
                      encoding="utf-8")

    py = sys.executable
    voice_file = None
    if a.voice_file:
        import shutil
        from align_voice import align
        src = Path(a.voice_file).resolve()
        voice_file = ndir / f"voice{src.suffix.lower()}"
        if src != voice_file:
            shutil.copy2(src, voice_file)
        align(voice_file, script, ndir / "words.json", a.whisper_model)
    elif not a.sync_only:
        if a.provisional:
            cmd = [py, str(HERE / "provisional_timing.py"), str(script), "-o", str(ndir), "--silence", "--rate", "3.0"]
        else:
            voice = a.voice or story.get("narration_voice", {}).get("voice_id")
            if not voice:
                sys.exit("Cần --voice VOICE_ID (xem: tts_elevenlabs.py --list-voices).")
            cmd = [py, str(HERE / "tts_elevenlabs.py"), str(script), "--voice", voice, "-o", str(ndir),
                   "--model", a.model, "--speed", str(a.speed), "--stability", str(a.stability), "--style", str(a.style)]
        if subprocess.run(cmd).returncode != 0:
            sys.exit("Lồng tiếng thất bại.")

    if voice_file is None:
        voice_file = ndir / "voice.mp3" if (ndir / "voice.mp3").exists() and not a.provisional else ndir / "voice.wav"
        if not voice_file.exists():
            voice_file = ndir / "voice.mp3"
    wmeta = json.loads((ndir / "words.json").read_text(encoding="utf-8")).get("meta", {})
    w, h = story.get("canvas", [1080, 1920])
    sync = build_sync(story, scenes, load_words(ndir / "words.json"), voice_file, wmeta.get("timing", "verified"), h > w)
    (ndir / "sync.json").write_text(json.dumps(sync, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nĐồng bộ xong: {sync['duration']:.2f}s, {len(scenes)} cảnh → {ndir / 'sync.json'}")
    for s in sync["scenes"]:
        print(f"  Cảnh {s['id']}: {s['slot'][0]:6.2f} → {s['slot'][1]:6.2f}s ({s['slot'][1] - s['slot'][0]:.2f}s), "
              f"{len(s['lines'])} dòng sub" + (f", graphic {s['graphic']['template']}" if s["graphic"] else ""))


if __name__ == "__main__":
    main()
