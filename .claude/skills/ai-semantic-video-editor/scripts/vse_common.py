"""Shared helpers for the AI Semantic Video Editor scripts."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ELEVEN_BASE = "https://api.elevenlabs.io"


# ---------- API key ----------

def get_api_key(project_dir: Path | None = None) -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    for d in [project_dir, Path.cwd(), Path.home()]:
        if d and (Path(d) / ".env").exists():
            for line in (Path(d) / ".env").read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*ELEVENLABS_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
                if m:
                    return m.group(1)
    sys.exit("Thiếu ELEVENLABS_API_KEY (đặt biến môi trường, hoặc ghi vào file .env trong thư mục dự án hay thư mục người dùng). "
             "Không có key thì dùng provisional_timing.py để dựng thử.")


# ---------- script parsing ----------

def read_script_paragraphs(path: Path) -> list[str]:
    """Paragraphs separated by blank lines; lines starting with '#' are notes."""
    text = Path(path).read_text(encoding="utf-8-sig")
    paras, cur = [], []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if not s:
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(" ".join(cur))
    return paras


def normalize_token(t: str) -> str:
    t = unicodedata.normalize("NFC", t).lower()
    return re.sub(r"[^\w]", "", t)


# ---------- words ----------

def save_words(words: list[dict], path: Path, meta: dict | None = None) -> None:
    for i, w in enumerate(words, 1):
        w["id"] = f"w{i}"
        w["start"] = round(float(w["start"]), 3)
        w["end"] = round(float(w["end"]), 3)
    data = {"meta": meta or {}, "words": words}
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def load_words(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["words"] if isinstance(data, dict) else data


def align_to_script(asr: list[dict], script_tokens: list[tuple[str, int]]) -> list[dict]:
    """Replace ASR word text with script tokens, keeping ASR timing.

    script_tokens: list of (token_text, beat_index).
    Unmatched script spans get timings interpolated over the ASR span they replace.
    """
    import difflib

    a = [normalize_token(w["text"]) for w in asr]
    b = [normalize_token(t) for t, _ in script_tokens]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out: list[dict] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                w = dict(asr[i1 + k])
                w["text"], w["beat"] = script_tokens[j1 + k]
                out.append(w)
        elif op in ("replace", "insert"):
            if i2 > i1:
                t0, t1 = asr[i1]["start"], asr[i2 - 1]["end"]
            else:  # pure insert: squeeze between neighbours
                t0 = out[-1]["end"] if out else 0.0
                t1 = asr[i1]["start"] if i1 < len(asr) else t0 + 0.25 * (j2 - j1)
                if t1 <= t0:
                    t1 = t0 + 0.12 * (j2 - j1)
            n = j2 - j1
            step = (t1 - t0) / n
            for k in range(n):
                text, beat = script_tokens[j1 + k]
                out.append({"text": text, "beat": beat, "start": t0 + k * step,
                            "end": t0 + (k + 1) * step, "confidence": None,
                            "aligned": "interpolated"})
        # 'delete': ASR words not in script are dropped (fillers, misrecognitions)
    # enforce monotonic, non-overlapping times
    for i in range(1, len(out)):
        if out[i]["start"] < out[i - 1]["end"]:
            out[i]["start"] = out[i - 1]["end"]
        if out[i]["end"] <= out[i]["start"]:
            out[i]["end"] = out[i]["start"] + 0.05
    return out


def script_tokens(paragraphs: list[str]) -> list[tuple[str, int]]:
    toks = []
    for bi, p in enumerate(paragraphs):
        for t in p.split():
            if normalize_token(t):
                toks.append((t, bi))
            elif toks:  # stray punctuation like "…" or "-" → attach to previous word
                toks[-1] = (toks[-1][0] + t, toks[-1][1])
    return toks


# ---------- media ----------

def need(tool: str) -> str:
    p = shutil.which(tool)
    if not p:
        sys.exit(f"Không tìm thấy {tool} trong PATH.")
    return p


def run(cmd: list, cwd: Path | None = None, quiet: bool = True) -> None:
    cmd = [str(c) for c in cmd]
    if not quiet:
        print(" ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        sys.exit(f"Lệnh thất bại: {cmd[0]} (mã {r.returncode})")


def probe_duration(path: Path) -> float:
    need("ffprobe")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"Không đọc được thời lượng: {path}")


# ---------- fonts ----------

FONT_FILES = {
    "roboto": ["Roboto-Bold.ttf", "Roboto-Bold_2.ttf", "Roboto-Black.ttf", "Roboto-Medium.ttf", "Roboto-Regular.ttf"],
    "inter": ["Inter-Bold.ttf", "Inter-Bold-slnt=0.ttf", "Inter-Regular-slnt=0.ttf", "Inter-Regular.ttf"],
    "be vietnam pro": ["BeVietnamPro-Bold.ttf", "BeVietnamPro-SemiBold.ttf", "BeVietnamPro-Regular.ttf"],
    "montserrat": ["Montserrat-Bold.ttf", "Montserrat-ExtraBold.ttf", "Montserrat-Regular.ttf"],
    "arial": ["arialbd.ttf", "arial.ttf"],
    "segoe ui": ["segoeuib.ttf", "segoeui.ttf"],
    "tahoma": ["tahomabd.ttf", "tahoma.ttf"],
}


def font_dirs(extra: list[Path] | None = None) -> list[Path]:
    dirs = list(extra or [])
    dirs.append(Path(__file__).resolve().parent.parent / "assets" / "fonts")
    windir = os.environ.get("WINDIR", "C:/Windows")
    dirs.append(Path(windir) / "Fonts")
    if os.environ.get("LOCALAPPDATA"):
        dirs.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts")
    dirs += [Path("/usr/share/fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts",
             Path.home() / ".fonts", Path.home() / ".local/share/fonts"]
    return [d for d in dirs if d.exists()]


def find_font(name: str = "Roboto", extra_dirs: list[Path] | None = None) -> Path:
    """Return a TTF path for `name` (a family name or a file path), falling back to Arial/DejaVu."""
    if name and Path(name).is_file():
        return Path(name)
    wanted = FONT_FILES.get((name or "").lower(), []) + FONT_FILES["arial"] + ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    dirs = font_dirs(extra_dirs)
    for fname in wanted:
        for d in dirs:
            p = d / fname
            if p.exists():
                return p
            hits = list(d.rglob(fname)) if d.name in ("fonts", "share") else []
            if hits:
                return hits[0]
    # last resort: any file whose name starts with the family name
    key = (name or "").replace(" ", "").lower()
    for d in dirs:
        for p in d.glob("*.ttf"):
            if p.name.replace(" ", "").lower().startswith(key):
                return p
    sys.exit(f"Không tìm thấy font '{name}'. Bỏ file .ttf vào {Path(__file__).resolve().parent.parent / 'assets' / 'fonts'}")


def font_family_name(path: Path) -> str:
    try:
        from PIL import ImageFont
        return ImageFont.truetype(str(path), 20).getname()[0]
    except Exception:
        return path.stem.split("-")[0]


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ass_color(h: str, alpha: int = 0) -> str:
    r, g, b = hex_to_rgb(h)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"
