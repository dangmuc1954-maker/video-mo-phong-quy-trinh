"""storyboard.json + narration/sync.json + narration/words.json + assets/assets.json → render/timeline.json

  python plan_timeline.py projects/<slug>/storyboard.json

- Cảnh nằm đúng khoảng thời gian câu kể của nó (sync.json).
- Mọi "cue": "<cụm từ trong lời kể>" (trong p, items, stops, routes, labels, keywords, sfx) → "at": giây tuyệt đối
  khi cụm từ đó được đọc. Không tìm thấy → báo và đặt ở đầu cảnh.
- Từ khoá chưa ghi "effect" → lấy theo edit_profile.emphasis (bộ não đạo diễn).
- Ảnh "photo_query" → ảnh đã tải + dòng nguồn. Map → điểm dừng + ảnh vệ tinh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

# kiểu nhấn mạnh theo hồ sơ → hiệu ứng từ khoá mặc định
EMPH_DEFAULT = {"stamp_slam": "stamp_slam", "cartoon_bounce": "bounce", "soft_fade": "fade", "price_giftbox": "giftbox",
                "data_count": "zoom_big", "typewriter": "typewriter"}
# hiệu ứng → SFX gợi ý cho hậu kỳ (theo sfx_style)
SFX_BY_EFFECT = {
    "stamp_slam": {"real_heavy": "stamp", "real_light": "paper hit", "cartoon": "bonk", "ui": "impact"},
    "giftbox": {"_": "gift box open"}, "bounce": {"_": "boing"}, "typewriter": {"_": "typewriter"},
    "rise": {"_": "whoosh up"}, "crack": {"_": "glass crack"}, "warning": {"_": "alarm beep"},
    "redact": {"_": "marker"}, "speed": {"_": "whoosh"}, "zoom_big": {"_": "impact"}, "count": {"_": "counter"},
}
SFX_BY_TRANSITION = {"whip": "whoosh", "zoom": "whoosh", "flash": "camera flash", "flash_red": "hit", "slam": "impact", "pop": "pop"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"[^\w\s]", " ", s).split().__str__()


def toks(s: str) -> list[str]:
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"[^\w\s]", " ", s).split()


class Cues:
    def __init__(self, words: list[dict]):
        self.w = words
        self.t = [(toks(x["text"]) or [""])[0] for x in words]
        self.miss: list[str] = []

    def find(self, cue: str, lo: float, hi: float, where: str) -> float:
        c = toks(cue)
        if not c:
            return lo
        best = None
        for i in range(len(self.t) - len(c) + 1):
            if self.t[i:i + len(c)] == c:
                st = self.w[i]["start"]
                if lo - 0.6 <= st <= hi + 0.6:
                    return st
                best = best if best is not None else st
        if best is not None:
            return best
        # khớp từ đầu tiên trong cảnh
        for i, tk in enumerate(self.t):
            if tk == c[0] and lo - 0.6 <= self.w[i]["start"] <= hi + 0.6:
                self.miss.append(f"{where}: '{cue}' chỉ khớp từ đầu")
                return self.w[i]["start"]
        self.miss.append(f"{where}: KHÔNG thấy '{cue}' trong lời kể → đặt đầu cảnh")
        return lo + 0.3


def resolve(o, cues: Cues, lo: float, hi: float, where: str):
    if isinstance(o, dict):
        if "cue" in o and "at" not in o:
            o["at"] = round(cues.find(o["cue"], lo, hi, where), 3)
        for k in list(o.keys()):
            if k.endswith("_cue") and isinstance(o[k], str):
                o[k[:-4] + "_at"] = round(cues.find(o[k], lo, hi, where), 3)
            resolve(o[k], cues, lo, hi, where)
    elif isinstance(o, list):
        for v in o:
            resolve(v, cues, lo, hi, where)


LOGO_LIB = Path(__file__).resolve().parent.parent / "brand" / "logos"
# tên hay gặp → khoá logo trong brand/logos (quy tắc 4b: gọi tên phần mềm/tổ chức thì phải có logo/ảnh thật)
KNOWN_NAMES = {"chatgpt": "chatgpt", "openai": "openai", "claude": "claude", "google": "google", "gemini": "gemini", "veo": "veo",
               "grok": "grok", "elevenlabs": "elevenlabs", "capcut": "capcut", "mckinsey": "mckinsey", "codex": "codex", "cursor": "cursor",
               "copilot": "copilot", "midjourney": "midjourney", "canva": "canva", "tiktok": "tiktok", "youtube": "youtube", "facebook": "facebook",
               "antigravity": "antigravity", "notion": "notion", "excel": "excel", "zalo": "zalo", "shopee": "shopee"}


def resolve_callouts(cos, proj: Path, photos: dict) -> list:
    out = []
    for g in json.loads(json.dumps(cos or [])):
        for it in g.get("items") or [g]:
            for key in ("logo", "photo"):
                v = it.get(key)
                if not isinstance(v, str) or v.startswith("file:"):
                    continue
                if key == "photo" and v in photos and photos[v]:
                    it.setdefault("source", photos[v]["credit"]); it[key] = photos[v]["file"]; continue
                f = (LOGO_LIB / f"{v}.png") if key == "logo" and "/" not in v and "." not in v else (proj / v)
                if not f.exists():
                    print(f"  ! callout thiếu file {key}: {v}")
                it[key] = f.resolve().as_uri()
        out.append(g)
    return out


def absolutize(o, proj: Path):
    """Ảnh/video ghi đường dẫn tương đối trong dự án (kể cả trong nhịp then, slider, timeline…) → file:/// để engine nạp được."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("photo", "video", "bg_photo", "bg_video") and isinstance(v, str) and not v.startswith(("file:", "http")):
                f = (proj / v)
                if f.exists():
                    o[k] = f.resolve().as_uri()
            else:
                absolutize(v, proj)
    elif isinstance(o, list):
        for v in o:
            absolutize(v, proj)


def attach_photos(o, photos: dict):
    if isinstance(o, dict):
        q = o.get("photo_query")
        if q and photos.get(q):
            o["photo"] = photos[q]["file"]
            o.setdefault("source", photos[q]["credit"])
        for key, credk in (("photo", "source"), ("bg_photo", "bg_source"), ("bg_video", "bg_source"), ("video", "_vsrc")):
            v = o.get(key)
            if isinstance(v, str) and v in photos and photos[v]:
                o[credk] = o.get(credk) or photos[v]["credit"]
                o[key] = photos[v]["file"]
        for v in o.values():
            attach_photos(v, photos)
    elif isinstance(o, list):
        for v in o:
            attach_photos(v, photos)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    a = ap.parse_args()
    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    sb = json.loads(sp.read_text(encoding="utf-8"))
    sync = json.loads((proj / "narration" / "sync.json").read_text(encoding="utf-8"))
    words = json.loads((proj / "narration" / "words.json").read_text(encoding="utf-8"))["words"]
    am = proj / "assets" / "assets.json"
    assets = json.loads(am.read_text(encoding="utf-8")) if am.exists() else {"maps": {}, "photos": {}}
    brand = json.loads((SKILL / "brand" / "brand.json").read_text(encoding="utf-8"))
    brand.update(sb.get("brand") or {})
    prof = sb.get("edit_profile") or {}
    W, H = sb.get("canvas", [1080, 1920])
    cues = Cues(words)
    slots = {s["id"]: s for s in sync["scenes"]}
    out_sc, subs, sfx = [], [], []
    dur = sync["duration"] + float(sb.get("tail", 0.6))
    ids = [sc["id"] for sc in sb["scenes"]]
    for n, sc in enumerate(sb["scenes"]):
        sl = slots[sc["id"]]["slot"]
        st = sl[0]
        en = slots[ids[n + 1]]["slot"][0] if n + 1 < len(ids) else dur
        p = json.loads(json.dumps(sc.get("p") or {}))
        attach_photos(p, assets.get("photos", {}))
        absolutize(p, proj)
        for it in p.get("items", []) if isinstance(p.get("items"), list) else []:
            if isinstance(it, dict) and isinstance(it.get("flag"), str) and it["flag"] in assets.get("flags", {}):
                it["flag"] = assets["flags"][it["flag"]]
        if sc.get("module") == "map":
            m = assets["maps"].get(str(sc["id"]), {})
            stops = []
            places = p.get("places") or []
            for i, s in enumerate(m.get("stops") or places):
                s = dict(s)
                if i < len(places):  # sửa trong storyboard (nhãn, ẩn ghim, cue…) luôn được áp, không cần tải lại tư liệu
                    s.update({k: v for k, v in places[i].items() if k not in ("lat", "lon")})
                s.setdefault("zoom", 12)
                stops.append(s)
            p["stops"] = stops
            p["levels"] = m.get("levels", [])
        resolve(p, cues, st, en, f"cảnh {sc['id']}")
        kws = json.loads(json.dumps(sc.get("keywords") or []))
        for k in kws:
            k.setdefault("effect", EMPH_DEFAULT.get(prof.get("emphasis", ""), "fade"))
        resolve(kws, cues, st, en, f"cảnh {sc['id']} từ khoá")
        if sc.get("module", "title") == "title" and en - st > 2.6 and not p.get("then"):
            print(f"  ! cảnh {sc['id']}: tiêu đề lớn treo {en - st:.1f}s — thêm p.then (nhịp graphic) để tiêu đề chỉ hiện ~1.2s")
        cos = resolve_callouts(sc.get("callouts"), proj, assets.get("photos", {}))
        resolve(cos, cues, st, en, f"cảnh {sc['id']} callout")
        said = " ".join(toks(sc.get("text") or ""))
        have = " ".join(toks(json.dumps(sc.get("callouts") or [], ensure_ascii=False)))
        for nm in KNOWN_NAMES:
            if re.search(rf"{nm}", said) and nm not in have:
                print(f"  ! cảnh {sc['id']}: lời kể gọi tên '{nm}' mà chưa có callout logo (quy tắc 4b)")
        theme = sc.get("theme") or sb.get("theme") or ("map" if sc.get("module") == "map" else "dark_glow")
        out_sc.append({"id": sc["id"], "start": round(st, 3), "end": round(en, 3), "module": sc.get("module", "title"),
                       "theme": theme, "mood": sc.get("mood") or prof.get("mood_key") or "neutral",
                       "camera": sc.get("camera", "push"), "transition_in": sc.get("transition_in", "cut" if n == 0 else "whip"),
                       "p": p, "keywords": kws, "callouts": cos})
        # SFX gợi ý: khai báo tay (sfx: [{cue,sound,search,volume}]) + theo hiệu ứng từ khoá + chuyển cảnh
        style = prof.get("sfx_style", "real_light")
        for x in sc.get("sfx") or []:
            x = dict(x)
            resolve(x, cues, st, en, f"cảnh {sc['id']} sfx")
            sfx.append({"scene": sc["id"], "time": x.get("at", st), **x})
        for k in kws:
            m = SFX_BY_EFFECT.get(k["effect"], {})
            snd = m.get(style) or m.get("_")
            if snd:
                sfx.append({"scene": sc["id"], "time": k.get("at", st), "sound": f"từ khoá '{k['text']}'", "search": snd,
                            "volume": 0.4, "why": f"hiệu ứng {k['effect']}"})
        for g in cos:
            for it in g.get("items") or [g]:
                sfx.append({"scene": sc["id"], "time": it.get("at", st), "sound": f"logo '{it.get('name', '')}' bật ra", "search": "pop",
                            "volume": 0.3, "why": "callout logo/ảnh"})
        tr = out_sc[-1]["transition_in"]
        if n and tr in SFX_BY_TRANSITION:
            sfx.append({"scene": sc["id"], "time": st, "sound": "chuyển cảnh", "search": SFX_BY_TRANSITION[tr], "volume": 0.3,
                        "why": f"chuyển cảnh {tr}"})
        if sc.get("module") == "map" and p.get("from_space"):
            sfx.append({"scene": sc["id"], "time": st, "sound": "bay từ vũ trụ xuống", "search": "whoosh wind", "volume": 0.35,
                        "why": "máy quay xuyên mây"})
    # phụ đề: dòng của sync + mốc từng từ
    used_w: set = set()
    for s in sync["scenes"]:
        for ln in s.get("lines", []):
            ws = []
            for wi, w in enumerate(words):  # mỗi chữ chỉ thuộc MỘT dòng sub (chữ nằm đúng ranh giới không bị lặp ở 2 dòng)
                if wi not in used_w and ln["start"] - 0.06 <= w["start"] <= ln["end"] + 0.06:
                    used_w.add(wi)
                    ws.append({"text": w["text"], "start": w["start"], "end": w["end"]})
            subs.append({"start": ln["start"], "end": ln["end"], "text": ln["text"], "words": ws})
    geo = {iso: json.loads(Path(fp).read_text()) for iso, fp in (assets.get("geo") or {}).items() if Path(fp).exists()}
    if sb.get("brand_tag"):
        brand["tag"] = sb["brand_tag"]
    tl = {"W": W, "H": H, "fps": sb.get("fps", 30), "duration": round(dur, 3), "brand": brand, "design": sb.get("design", "v1"), "geo": geo,
          "profile": {"subtitle": prof.get("subtitle", "story_pop_compact"), "mood": prof.get("mood_key", "neutral"),
                      "sub_bottom": sb.get("sub_bottom"), "sub_size": sb.get("sub_size")},
          "header": sb.get("header"),
          "icon_base": assets.get("icon_base", ""), "globe": assets.get("globe"), "scenes": out_sc, "subs": subs,
          "credits": assets.get("credits", []), "title": sb.get("title", proj.name)}
    rd = proj / "render"
    rd.mkdir(exist_ok=True)
    (rd / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    # S5: cảnh cao trào ("climax": true) → câu âm thanh riser (dồn) → impact (đập) → sparkle (loé)
    for sc, s in zip(sb["scenes"], out_sc):
        if sc.get("climax"):
            t = s["start"]
            sfx += [{"scene": s["id"], "time": round(max(0, t - 1.2), 3), "end": round(t, 3), "sound": "dồn trước cao trào", "search": "riser", "volume": 0.35, "why": "luật S5 riser"},
                    {"scene": s["id"], "time": t, "sound": "đập cao trào", "search": "cinematic impact", "volume": 0.5, "why": "luật S5 impact"},
                    {"scene": s["id"], "time": round(t + .25, 3), "sound": "loé sáng sau cú đập", "search": "sparkle shimmer", "volume": 0.3, "why": "luật S5 sparkle"}]
    sfx.sort(key=lambda x: x["time"])
    # S2: chống "súng máy" — cùng một tiếng ≥3 lần cách nhau <0.7s → xen 2 mẫu (A/B) + âm lượng bậc thang 0.40 → 0.25
    by: dict = {}
    for x in sfx:
        by.setdefault(x.get("search"), []).append(x)
    for xs in by.values():
        run = [xs[0]]
        for x in xs[1:] + [None]:
            if x is not None and x["time"] - run[-1]["time"] < .7:
                run.append(x)
                continue
            if len(run) >= 3:
                for i, r in enumerate(run):
                    r["volume"] = round(.40 - (.15 * i / (len(run) - 1)), 3)
                    r["variant"] = "B" if i % 2 else "A"
                    r["ladder"] = True
                    r["why"] = f"{r.get('why', '')} · chuỗi {len(run)} tiếng: mẫu {r['variant']}, âm lượng giảm dần"
            run = [x] if x is not None else []
    (rd / "sfx_plan.json").write_text(json.dumps(sfx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Timeline: {len(out_sc)} cảnh, {dur:.2f}s, {len(subs)} dòng sub, {len(sfx)} gợi ý SFX → {rd / 'timeline.json'}")
    for s in out_sc:
        print(f"  {s['id']:>2} {s['start']:6.2f}→{s['end']:6.2f}  {s['module']:<9} {s['theme']:<9} {s['mood']:<8} "
              f"{s['transition_in']:<6} từ khoá: {', '.join(k['text'] + '@' + str(k.get('at')) for k in s['keywords']) or '-'}")
    if cues.miss:
        print("Cần xem lại cue:")
        for m in cues.miss:
            print("  ! " + m)


if __name__ == "__main__":
    main()
