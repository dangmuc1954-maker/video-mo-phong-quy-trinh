"""Render ANY tao-video storyboard with the skill's text style when the speech is INSIDE the clips
(Muse/Veo dialogue or narration generated with the scene) or when there is no speech at all.

  python clip_render.py projects/<slug>/storyboard.json [--preview] [--preset story_pop] [--capcut-layers]

- Scenes keep their natural length (edit_plan.json trims and scene "keep" are applied), clip sound is kept.
- Speech: faster-whisper reads each clip → word timings (text corrected with scene "dialogue"/"narration"/"lines"
  when given) → subtitles `story_pop` (each word appears when spoken, the word being said in the accent colour).
- Scene without speech but with "subtitle" → that caption is shown as word-by-word kinetic text (lower third).
- "caption_top", scene "graphic" (cue word in the speech), "transition_in" (soft FFmpeg transitions) work as in
  story_render.py. Output: projects/<slug>/2-xuat/<title> (story_pop).mp4
Use story_render.py instead when the video has an ElevenLabs narration (narration/sync.json).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from story_render import xfade_of  # noqa: E402
from vse_common import align_to_script, normalize_token, probe_duration, run, save_words, script_tokens  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def scene_text(sc: dict) -> str:
    if sc.get("lines"):
        return " ".join(ln["text"] for ln in sc["lines"] if ln.get("text"))
    return (sc.get("dialogue") or sc.get("narration") or "").strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--preset", default=None)
    ap.add_argument("--capcut-layers", action="store_true")
    ap.add_argument("--whisper-model", default="small")
    a = ap.parse_args()

    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = json.loads(sp.read_text(encoding="utf-8"))
    plan = json.loads((proj / "edit_plan.json").read_text(encoding="utf-8")) if (proj / "edit_plan.json").exists() else {}
    ndir = proj / "narration"
    ndir.mkdir(exist_ok=True)
    W, H = story.get("canvas", [1080, 1920])
    kept = [sc for sc in story["scenes"] if not plan.get(str(sc["id"]), {}).get("drop")]

    from faster_whisper import WhisperModel
    model = WhisperModel(a.whisper_model, device="cpu", compute_type="int8")

    assets, layers, beats, words, audio_parts = [], [], [], [], []
    t = 0.0
    tmp = Path(tempfile.mkdtemp())
    for i, sc in enumerate(kept):
        clip = proj / "1-canh" / sc["clip"]
        if not clip.exists():
            sys.exit(f"Thiếu clip cảnh {sc['id']}: {clip}")
        p = plan.get(str(sc["id"]), {})
        s0 = float(p.get("trim_start", 0))
        e0 = probe_duration(clip) - float(p.get("trim_end", 0))
        if sc.get("keep"):
            s0, e0 = max(s0, sc["keep"][0]), min(e0, sc["keep"][1])
        d = round(e0 - s0, 3)
        # clip sound for this scene (kept, concatenated later)
        wav = tmp / f"a{i:02d}.wav"
        run(["ffmpeg", "-y", "-ss", f"{s0:.3f}", "-t", f"{d:.3f}", "-i", clip, "-vn", "-ac", "2", "-ar", "44100",
             "-af", "apad", "-t", f"{d:.3f}", wav])
        audio_parts.append(wav)
        # speech → words
        segs, _ = model.transcribe(str(wav), language="vi", word_timestamps=True, vad_filter=True)
        asr = [{"text": w.word.strip(), "start": w.start, "end": w.end, "confidence": round(w.probability, 3), "beat": i}
               for s in segs for w in (s.words or []) if w.word.strip()]
        txt = scene_text(sc)
        if asr and txt:
            sw = align_to_script(asr, [(tok, i) for tok, _ in script_tokens([txt])])
        else:
            sw = asr
        for w in sw:
            w["start"] = round(t + float(w["start"]), 3)
            w["end"] = round(min(t + d, t + float(w["end"])), 3)
            w["beat"] = i
        words += sw
        aid, bid = f"c{sc['id']}", f"b{sc['id']}"
        assets.append({"id": aid, "kind": "video", "file": f"../1-canh/{sc['clip']}", "prompt": sc.get("prompt"),
                       "license": "AI-generated (tool/Muse)", "status": "ready"})
        layers.append({"id": f"L{sc['id']}", "type": "scene", "start": round(t, 3), "end": round(t + d, 3), "asset_id": aid,
                       "motion": "static", "beat_id": bid, "source_start": round(s0, 3), "speed": 1.0, **xfade_of(sc, i)})
        beats.append({"id": bid, "start": round(t, 3), "end": round(t + d, 3), "spoken_text": txt,
                      "meaning": sc.get("action", ""), "visual_type": "scene", "rationale": "cảnh tạo theo storyboard",
                      "asset_ids": [aid], "visual_cue_word_ids": [], "keywords": sc.get("keywords", [])})
        # no speech → the scene caption becomes word-by-word text at the lower third
        cap = (sc.get("subtitle") or "").strip()
        if not sw and cap and not story.get("caption_top"):
            layers.append({"id": f"S{sc['id']}", "type": "mograph", "start": round(t + 0.2, 3), "end": round(t + d, 3),
                           "beat_id": bid, "template": "kinetic_text", "anchor": "lower_third",
                           "data": {"lines": [cap], "emphasis_index": -1, "style": "word_pop", "glow": False}})
        # graphic on a cue word of this scene's speech
        g = sc.get("graphic")
        if g:
            k = [normalize_token(x) for x in g.get("cue", "").split() if normalize_token(x)]
            norm = [normalize_token(w["text"]) for w in sw]
            hit = next((j for j in range(len(norm) - len(k) + 1) if k and norm[j:j + len(k)] == k), None)
            gs = (sw[hit]["start"] - 0.1) if hit is not None else t + 0.3
            ge = min(t + d + 2.0, gs + float(g.get("hold", 2.8)))
            layers.append({"id": f"G{sc['id']}", "type": "mograph", "start": round(max(t, gs), 3), "end": round(ge, 3),
                           "beat_id": bid, "template": g["template"],
                           "anchor": "center" if story.get("caption_top") else g.get("anchor", "center"),
                           "data": g.get("data", {})})
        print(f"Cảnh {sc['id']}: {t:6.2f}→{t + d:6.2f}s, {len(sw)} từ nói" + (" (khớp chữ theo kịch bản)" if asr and txt else ""))
        t += d
    dur = round(t, 3)
    for L in layers:
        L["end"] = round(min(L["end"], dur), 3)

    caps = [(sc.get("subtitle") or "").strip() for sc in kept]
    if story.get("caption_top") and any(caps) and len(set(caps)) == 1:
        layers.append({"id": "T0", "type": "mograph", "start": 0.0, "end": dur, "beat_id": beats[0]["id"],
                       "template": "kinetic_text", "anchor": "top",
                       "data": {"lines": [caps[0]], "emphasis_index": 0, "style": "word_pop", "glow": False}})

    # concatenated clip sound = the audio track of the render
    lst = tmp / "a.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in audio_parts), encoding="utf-8")
    audio = ndir / "clip_audio.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", audio])
    save_words(words, ndir / "words.json", {"source": "faster-whisper on clips", "timing": "verified", "duration_seconds": dur})

    tl = {"version": "2.0", "mode": "STORYTELLING",
          "project": {"title": story.get("title", proj.name), "language": "vi", "fps": 30, "width": W, "height": H,
                      "duration_seconds": dur, "voice_audio": audio.name, "source_video": None, "bgm": None,
                      "bgm_volume": 0.15, "transcript_timing": "verified"},
          "style_bible": {"palette": story.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"], "font": story.get("font", "Roboto"),
                          "subtitle_preset": a.preset or story.get("subtitle_preset", "story_pop"), "subtitle_uppercase": False},
          "words": [dict(w, id=f"w{n + 1}") for n, w in enumerate(words)], "beats": beats, "assets": assets, "layers": layers,
          "qa": {"subtitle_alignment_status": "verified", "visual_alignment_status": "planned"}}
    tpath = ndir / "timeline.json"
    tpath.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.preview:
        out = ndir / "build" / "preview.mp4"
    else:
        (proj / "2-xuat").mkdir(exist_ok=True)
        out = proj / "2-xuat" / f"{story.get('title', proj.name)} (story_pop).mp4"
    cmd = [sys.executable, str(HERE / "render.py"), str(tpath), "-o", str(out)] + (["--preview"] if a.preview else []) \
        + (["--capcut-layers"] if a.capcut_layers else [])
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
