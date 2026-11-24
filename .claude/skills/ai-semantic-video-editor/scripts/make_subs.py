"""words.json -> styled Vietnamese subtitles (.ass for FFmpeg, .srt for CapCut).

Presets: clean | box | karaoke | pop_word | keyword | cinematic | story_pop

Usage:
  python make_subs.py words.json -o build/subs --preset pop_word [--font Roboto] [--accent "#FACC15"]
         [--keywords "kiên trì,đừng bỏ cuộc"] [--uppercase] [--width 1080 --height 1920]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import ass_color, find_font, font_family_name, load_words, normalize_token  # noqa: E402

PRESETS = ["clean", "box", "karaoke", "pop_word", "keyword", "cinematic", "story_pop"]


def chunk_words(words, max_chars=28 * 2, max_words=12, gap=0.35, punct_min=None):
    punct_min = max_chars * 0.35 if punct_min is None else punct_min
    chunks, cur, n = [], [], 0
    for i, w in enumerate(words):
        if cur:
            pause = w["start"] - cur[-1]["end"]
            if pause > gap or n + 1 + len(w["text"]) > max_chars or len(cur) >= max_words \
                    or w.get("beat") != cur[-1].get("beat"):
                chunks.append(cur)
                cur, n = [], 0
        cur.append(w)
        n += len(w["text"]) + (1 if n else 0)
        if w["text"][-1] in ".!?…;:," and n > punct_min:
            chunks.append(cur)
            cur, n = [], 0
    if cur:
        chunks.append(cur)
    return chunks


def split_lines(texts: list[str], line_chars: int) -> list[int]:
    """Return index after which to break (or -1)."""
    total = len(" ".join(texts))
    if total <= line_chars or len(texts) < 2:
        return -1
    best, best_i, acc = 1e9, -1, 0
    for i, t in enumerate(texts[:-1]):
        acc += len(t) + (1 if i else 0)
        score = abs(acc - (total - acc - 1))
        if score < best:
            best, best_i = score, i
    return best_i


def esc(t: str) -> str:
    return t.replace("\\", "＼").replace("{", "(").replace("}", ")")


def ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_ts(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def keyword_mask(words, keywords: list[str]) -> list[bool]:
    norm = [normalize_token(w["text"]) for w in words]
    mask = [False] * len(words)
    for kw in keywords:
        k = [normalize_token(x) for x in kw.split() if normalize_token(x)]
        if not k:
            continue
        for i in range(len(norm) - len(k) + 1):
            if norm[i:i + len(k)] == k:
                for j in range(i, i + len(k)):
                    mask[j] = True
    return mask


def build_subs(words, out_prefix: Path, preset="clean", width=1080, height=1920, font="Roboto",
               accent="#FACC15", keywords=None, uppercase=False) -> tuple[Path, Path, Path]:
    if preset not in PRESETS:
        sys.exit(f"Preset không hợp lệ: {preset}. Chọn: {', '.join(PRESETS)}")
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    font_path = find_font(font)
    fonts_dir = out_prefix.parent / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    shutil.copy2(font_path, fonts_dir / font_path.name)
    family = font_family_name(font_path)

    k = width / 1080
    portrait = height > width
    line_chars = 28 if portrait else 42
    words = [dict(w) for w in words]
    if uppercase:
        for w in words:
            w["text"] = w["text"].upper()
    kmask = keyword_mask(words, keywords or [])
    for w, m in zip(words, kmask):
        w["_kw"] = m

    acc = ass_color(accent)
    white = ass_color("#FFFFFF")
    black = ass_color("#000000")
    mv = int(height * (0.20 if portrait else 0.08))
    st = {  # fontsize, bold, primary, secondary, outline_col, back, borderstyle, outline, shadow, marginV
        "clean": (64, -1, white, white, black, ass_color("#000000", 0x80), 1, 5, 2, mv),
        "box": (56, -1, white, white, ass_color("#000000", 0x55), ass_color("#000000", 0x55), 3, 14, 0, mv),
        "karaoke": (64, -1, acc, white, black, ass_color("#000000", 0x80), 1, 5, 2, mv),
        "pop_word": (92, -1, white, white, black, ass_color("#000000", 0x60), 1, 7, 3, int(height * 0.26) if portrait else mv),
        "keyword": (64, -1, white, white, black, ass_color("#000000", 0x80), 1, 5, 2, mv),
        "story_pop": (76, -1, white, white, black, ass_color("#000000", 0x70), 1, 5, 3, mv),
        "cinematic": (50, 0, ass_color("#F5E6C8"), white, ass_color("#000000", 0x40), ass_color("#000000", 0x90), 1, 2, 3, int(height * (0.12 if portrait else 0.07))),
    }[preset]
    fs, bold, prim, sec, outc, back, bstyle, outl, shad, marv = st
    style = (f"Style: Main,{family},{int(fs * k)},{prim},{sec},{outc},{back},{bold},0,0,0,100,100,"
             f"{1 if preset == 'cinematic' else 0},0,{bstyle},{outl * k:.1f},{shad * k:.1f},2,"
             f"{int(60 * k)},{int(60 * k)},{marv},1")
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
             "WrapStyle: 2", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
             "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
             "Alignment, MarginL, MarginR, MarginV, Encoding", style, "",
             "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    if preset == "pop_word":
        chunks = chunk_words(words, max_chars=18, max_words=3, punct_min=0)
    else:
        chunks = chunk_words(words, max_chars=line_chars * 2)

    def chunk_end(ci):
        ch = chunks[ci]
        end = ch[-1]["end"] + 0.3
        if ci + 1 < len(chunks):
            end = min(end, chunks[ci + 1][0]["start"])
        return max(end, ch[0]["start"] + 0.6) if ci + 1 == len(chunks) else max(end, ch[-1]["end"])

    events = []
    for ci, ch in enumerate(chunks):
        t0, t1 = ch[0]["start"], chunk_end(ci)
        texts = [esc(w["text"]) for w in ch]
        brk = -1 if preset == "pop_word" else split_lines([w["text"] for w in ch], line_chars)
        sep = lambda i: (r"\N" if i == brk else " ")  # noqa: E731
        if preset in ("clean", "box", "cinematic"):
            fade = r"{\fad(250,250)}" if preset == "cinematic" else r"{\fad(60,60)}"
            body = "".join(t + (sep(i) if i < len(texts) - 1 else "") for i, t in enumerate(texts))
            events.append((t0, t1, fade + body))
        elif preset == "keyword":
            parts = []
            for i, (w, t) in enumerate(zip(ch, texts)):
                parts.append(rf"{{\c{acc}\fscx115\fscy115}}{t}{{\r}}" if w["_kw"] else t)
                if i < len(texts) - 1:
                    parts.append(sep(i))
            events.append((t0, t1, r"{\fad(60,60)}" + "".join(parts)))
        elif preset == "karaoke":
            parts = []
            for i, (w, t) in enumerate(zip(ch, texts)):
                nxt = ch[i + 1]["start"] if i + 1 < len(ch) else w["end"]
                parts.append(rf"{{\k{max(1, round((nxt - w['start']) * 100))}}}{t}")
                if i < len(texts) - 1:
                    parts.append(sep(i))
            events.append((t0, t1, r"{\fad(60,60)}" + "".join(parts)))
        elif preset == "story_pop":
            # every word appears exactly when spoken (fade + pop), the word being read is in the accent colour
            parts = []
            for i, (w, t) in enumerate(zip(ch, texts)):
                r = max(0, int(round((w["start"] - t0) * 1000)))
                rn = int(round(((ch[i + 1]["start"] if i + 1 < len(ch) else w["end"]) - t0) * 1000))
                rn = max(rn, r + 120)
                parts.append(rf"{{\alpha&HFF&\fscx60\fscy60\1c{acc}\t({r},{r + 110},\alpha&H00&\fscx116\fscy116)"
                             rf"\t({r + 110},{r + 240},\fscx100\fscy100)\t({rn},{rn + 90},\1c{white})}}{t}")
                if i < len(texts) - 1:
                    parts.append(sep(i))
            events.append((t0, t1, r"{\be1\fad(0,160)}" + "".join(parts)))
        elif preset == "pop_word":
            for wi, w in enumerate(ch):
                s = w["start"] if wi else t0
                e = ch[wi + 1]["start"] if wi + 1 < len(ch) else t1
                parts = []
                for i, t in enumerate(texts):
                    if i == wi:
                        parts.append(rf"{{\c{acc}\fscx125\fscy125\t(0,90,\fscx100\fscy100)}}{t}{{\r}}")
                    else:
                        parts.append(t)
                    if i < len(texts) - 1:
                        parts.append(" ")
                lead = r"{\fad(40,0)}" if wi == 0 else ""
                events.append((s, e, lead + "".join(parts)))

    for s, e, txt in events:
        if e > s:
            lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},Main,,0,0,0,,{txt}")
    ass_path = out_prefix.with_suffix(".ass")
    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    # SRT: phrase level, independent of preset
    srt_chunks = chunk_words(words, max_chars=line_chars * 2)
    srt = []
    for i, ch in enumerate(srt_chunks, 1):
        t1 = ch[-1]["end"] + 0.3
        if i < len(srt_chunks):
            t1 = min(t1, srt_chunks[i][0]["start"])
        t1 = max(t1, ch[-1]["end"])
        brk = split_lines([w["text"] for w in ch], line_chars)
        text = "".join(w["text"] + ("\n" if j == brk else " ") for j, w in enumerate(ch)).strip()
        srt.append(f"{i}\n{srt_ts(ch[0]['start'])} --> {srt_ts(t1)}\n{text}\n")
    srt_path = out_prefix.with_suffix(".srt")
    srt_path.write_text("\n".join(srt), encoding="utf-8-sig")
    return ass_path, srt_path, fonts_dir



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("-o", "--out", default="subs")
    ap.add_argument("--preset", default="clean", choices=PRESETS)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--font", default="Roboto")
    ap.add_argument("--accent", default="#FACC15")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--uppercase", action="store_true")
    a = ap.parse_args()
    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    ass, srt, fonts = build_subs(load_words(Path(a.words)), Path(a.out), a.preset, a.width, a.height,
                                 a.font, a.accent, kws, a.uppercase)
    print(f"Đã tạo {ass} và {srt} (font trong {fonts})")


if __name__ == "__main__":
    main()
