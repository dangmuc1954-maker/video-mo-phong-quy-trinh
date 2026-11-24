"""ElevenLabs voice catalog: used to pick a voice automatically when the user gives no voice ID.

  python voice_catalog.py update            # with ELEVENLABS_API_KEY: the WHOLE voice library (all languages)
                                            # without key: public sample (premade + top voices per language /
                                            # use case, 3 per request — ElevenLabs limit when logged out)
  python voice_catalog.py search --language vi --gender male --age middle_aged --use-case narrative_story \
         --keywords "deep warm calm" [--top 15] [--free-only]
  python voice_catalog.py show <voice_id>
  python voice_catalog.py add <voice_id> "<name>" [--language vi --gender male --age young --note "..."]
  python voice_catalog.py stats

Catalog file: <skill>/voices/catalog.json (shared by every project, text only, ~1 KB per voice).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vse_common  # noqa: E402,F401  (utf-8 console)
from vse_common import ELEVEN_BASE  # noqa: E402

import requests  # noqa: E402

CAT = HERE.parent / "voices" / "catalog.json"
FIELDS = ["voice_id", "name", "language", "locale", "accent", "gender", "age", "use_case", "category",
          "descriptive", "description", "cloned_by_count", "usage_character_count_1y", "free_users_allowed",
          "preview_url", "verified_languages", "source"]
LANGS = ["vi", "en", "zh", "ja", "ko", "th", "id", "ms", "fil", "hi", "ta", "ar", "tr", "ru", "uk", "pl", "cs",
         "sk", "hu", "ro", "bg", "hr", "el", "de", "fr", "es", "pt", "it", "nl", "sv", "no", "da", "fi"]
USE_CASES = [None, "narrative_story", "conversational", "characters_animation", "social_media",
             "entertainment_tv", "advertisement", "informative_educational"]
SORTS = ["trending", "cloned_by_count", "usage_character_count_1y", "created_date"]
# voices already saved / used in the AI VIDEO LIBRARY tool
KNOWN = [
    {"voice_id": "aN7cv9yXNrfIR87bDmyD", "name": "Ninh Đôn - Deep & Warm", "language": "vi", "gender": "male",
     "age": "middle_aged", "use_case": "narrative_story", "descriptive": "deep warm calm",
     "description": "Đã dùng thật cho video đạo lý (07/11/2026), đọc tiếng Việt chuẩn.", "source": "tool"},
    {"voice_id": "tdNewKwOSUwMPbmc5cs4", "name": "Đức Khang - Friendly", "language": "vi", "gender": "male",
     "age": "young", "accent": "standard", "use_case": "conversational", "descriptive": "chill friendly",
     "source": "tool"},
]


def key_or_none() -> str | None:
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if k:
        return k
    for d in (Path.cwd(), Path.home()):
        f = d / ".env"
        if f.exists():
            m = re.search(r"ELEVENLABS_API_KEY\s*=\s*['\"]?([^'\"\s]+)", f.read_text(encoding="utf-8"))
            if m:
                return m.group(1)
    return None


def load() -> dict:
    if CAT.exists():
        return json.loads(CAT.read_text(encoding="utf-8"))
    return {"updated": None, "complete": False, "voices": {}}


def save(cat: dict) -> None:
    CAT.parent.mkdir(parents=True, exist_ok=True)
    for v in KNOWN:
        cat["voices"][v["voice_id"]] = {**cat["voices"].get(v["voice_id"], {}), **v}
    cat["updated"] = time.strftime("%Y-%m-%d %H:%M")
    CAT.write_text(json.dumps(cat, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def slim(v: dict, source: str) -> dict:
    out = {k: v.get(k) for k in FIELDS if v.get(k) not in (None, "", [])}
    labels = v.get("labels") or {}
    for k in ("accent", "gender", "age", "descriptive", "use_case", "language"):
        if k not in out and labels.get(k):
            out[k] = labels[k]
    if v.get("verified_languages"):
        out["verified_languages"] = sorted({x.get("language") for x in v["verified_languages"] if x.get("language")})
    if isinstance(out.get("description"), str):
        out["description"] = out["description"][:300]
    out["source"] = source
    return out


def get(url, params, key=None, tries=4):
    h = {"xi-api-key": key} if key else {}
    r = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=h, timeout=20)
        except requests.RequestException:
            time.sleep(2)
            continue
        if r.status_code == 429:
            print(f"  ElevenLabs bắt chờ (429), nghỉ {3 * (i + 1)}s", flush=True)
            time.sleep(3 * (i + 1))
            continue
        return r
    return r


def update(full_only: bool) -> None:
    cat = load()
    V = cat["voices"]
    key = key_or_none()
    n0 = len(V)
    r = get(f"{ELEVEN_BASE}/v1/voices", {}, key)
    if r is not None and r.ok:
        for v in r.json().get("voices", []):
            V[v["voice_id"]] = {**V.get(v["voice_id"], {}), **slim(v, "premade" if v.get("category") == "premade" else "account")}
    if key:
        print("Có API key: tải TOÀN BỘ thư viện giọng (mọi ngôn ngữ)…", flush=True)
        page, total = 0, None
        while True:
            r = get(f"{ELEVEN_BASE}/v1/shared-voices", {"page_size": 100, "page": page}, key)
            if r is None or not r.ok:
                sys.exit(f"Lỗi {getattr(r, 'status_code', '?')}: {getattr(r, 'text', '')[:300]}")
            d = r.json()
            for v in d.get("voices", []):
                V[v["voice_id"]] = {**V.get(v["voice_id"], {}), **slim(v, "library")}
            total = d.get("total_count", total)
            page += 1
            if page % 10 == 0:
                print(f"  trang {page}: {len(V)} giọng / ~{total}", flush=True)
                save(cat)
            if not d.get("has_more"):
                break
            time.sleep(0.2)
        cat["complete"] = True
    elif full_only:
        sys.exit("Cần ELEVENLABS_API_KEY để tải toàn bộ thư viện.")
    else:
        print("Chưa có API key: lấy mẫu công khai (3 giọng/lần, giới hạn của ElevenLabs khi chưa đăng nhập)…", flush=True)
        combos = []
        for lang in LANGS:
            ucs = USE_CASES if lang in ("vi", "en") else [None, "narrative_story"]
            sorts = SORTS if lang in ("vi", "en") else SORTS[:2]
            for uc in ucs:
                for so in sorts:
                    combos.append((lang, uc, so))
        for i, (lang, uc, so) in enumerate(combos):
            p = {"page_size": 3, "language": lang, "sort": so}
            if uc:
                p["use_case"] = uc
            r = get(f"{ELEVEN_BASE}/v1/shared-voices", p)
            if r is not None and r.ok:
                for v in r.json().get("voices", []):
                    V[v["voice_id"]] = {**V.get(v["voice_id"], {}), **slim(v, "library")}
            if i % 20 == 0:
                print(f"  {i}/{len(combos)} truy vấn, {len(V)} giọng", flush=True)
                save(cat)
            time.sleep(0.25)
        cat["complete"] = False
    save(cat)
    print(f"Xong: {len(V)} giọng (+{len(V) - n0}) → {CAT}" + ("" if cat["complete"] else "  [mẫu công khai — thêm API key rồi chạy lại để lấy toàn bộ]"))


def norm(t: str) -> str:
    return unicodedata.normalize("NFD", (t or "").lower()).encode("ascii", "ignore").decode()


def score(v: dict, a) -> float:
    s = 0.0
    if a.language:
        langs = {v.get("language")} | set(v.get("verified_languages") or [])
        if a.language not in langs:
            return -1
        s += 6 if v.get("language") == a.language else 1   # native voice strongly preferred
    for f in ("gender", "age", "use_case", "accent"):
        want = getattr(a, f, None)
        if want:
            if v.get(f) == want:
                s += 2
            elif v.get(f):
                if f == "gender":
                    return -1
                s -= 1
    if a.keywords:
        text = norm(" ".join(str(v.get(k, "")) for k in ("name", "descriptive", "description", "use_case", "accent")))
        for kw in norm(a.keywords).split():
            if kw in text:
                s += 1.5
    pop = (v.get("cloned_by_count") or 0) + (v.get("usage_character_count_1y") or 0) / 1e5
    s += min(3.0, (pop ** 0.5) / 30)
    if v.get("source") in ("tool", "premade"):
        s += 1.0          # proven to work in the tool / official voice
    return s


def search(a) -> None:
    cat = load()
    vs = [v for v in cat["voices"].values() if not (a.free_only and v.get("free_users_allowed") is False)]
    ranked = sorted(((score(v, a), v) for v in vs), key=lambda x: -x[0])
    ranked = [x for x in ranked if x[0] >= 0][: a.top]
    if not cat.get("complete"):
        print(f"(Danh mục mẫu {len(cat['voices'])} giọng. Có API key thì `update` lấy toàn bộ thư viện.)")
    for s, v in ranked:
        print(f"{s:5.1f}  {v['voice_id']}  {v.get('name', '')[:42]:<42} {v.get('language', '?'):>3} {v.get('gender', '?'):<7}"
              f"{v.get('age', '?'):<12}{v.get('accent', '') or '':<12}{v.get('use_case', '') or '':<24}{v.get('descriptive', '') or ''}")
    if not ranked:
        print("Không có giọng phù hợp; nới bộ lọc (bỏ --age / --accent / --use-case).")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("update")
    u.add_argument("--full-only", action="store_true")
    s = sub.add_parser("search")
    for f in ("language", "gender", "age", "accent", "use-case", "keywords"):
        s.add_argument(f"--{f}")
    s.add_argument("--top", type=int, default=15)
    s.add_argument("--free-only", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("voice_id")
    ad = sub.add_parser("add")
    ad.add_argument("voice_id")
    ad.add_argument("name")
    for f in ("language", "gender", "age", "accent", "use-case", "note"):
        ad.add_argument(f"--{f}")
    sub.add_parser("stats")
    a = ap.parse_args()

    if a.cmd == "update":
        update(a.full_only)
    elif a.cmd == "search":
        search(a)
    elif a.cmd == "show":
        v = load()["voices"].get(a.voice_id)
        print(json.dumps(v, ensure_ascii=False, indent=1) if v else "Không có trong danh mục.")
    elif a.cmd == "add":
        cat = load()
        v = {"voice_id": a.voice_id, "name": a.name, "source": "manual"}
        for f in ("language", "gender", "age", "accent", "use_case"):
            if getattr(a, f):
                v[f] = getattr(a, f)
        if a.note:
            v["description"] = a.note
        cat["voices"][a.voice_id] = {**cat["voices"].get(a.voice_id, {}), **v}
        save(cat)
        print(f"Đã thêm {a.voice_id} {a.name}")
    elif a.cmd == "stats":
        from collections import Counter
        cat = load()
        V = list(cat["voices"].values())
        print(f"{len(V)} giọng, cập nhật {cat.get('updated')}, đầy đủ: {cat.get('complete')}")
        print("Ngôn ngữ:", Counter(v.get("language", "?") for v in V).most_common(15))
        print("Giới tính:", Counter(v.get("gender", "?") for v in V).most_common())


if __name__ == "__main__":
    main()
