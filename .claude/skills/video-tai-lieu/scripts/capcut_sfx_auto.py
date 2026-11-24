"""Tự chèn SFX + nhạc nền vào draft hậu kỳ CapCut, đúng giây theo render/timeline.json (không cần thao tác tay trong CapCut).

  python capcut_sfx_auto.py projects/<slug> [--title "<tên> (hau ky)"] [--music-start 0] [--music-vol .13]

Chạy SAU `compose.py projects/<slug> --capcut`, CapCut phải TẮT. Mẫu tiếng lấy từ các project CapCut khác trên máy
(thư viện SFX đã tải sẵn). Ghi narration/sfx_cues.json + .md để `capcut_sfx_check.py` đối chiếu.

SFX tự sinh:
  - chuyển cảnh (whip→gió, zoom→swish, flash→màn trập, slam→impact)
  - chữ chốt stamp_slam / warning / count, logo + ảnh callouts bật ra, khoanh viền (rings), gõ prompt, đồng hồ
  - cảnh "climax": true → hit + reveal lúc vào cảnh; khung đóng băng (freeze) → màn trập
  - thêm tay: scene["sfx_extra"] = [{"at_clip": 0.0, "key": "bass", "why": "vào phần chính"}] (key: xem LIB)
Nhạc nền: bắt đầu từ storyboard["edit_profile"]["music_start"] (mặc định 0; hook có tiếng riêng thì đặt = cuối hook),
lặp tới hết video, âm lượng 0.13, fade vào 1.5s / ra 2s.
"""
import argparse, copy, glob, json, os, sys, uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SK / "tao-video" / "scripts"))
import build_capcut_draft as B  # noqa: E402

US = 1_000_000
ROOT = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
LIB = {"hit": "Cinematic hit impact! 13", "stamp": "Press the seal and stamp 02(1170761)", "keys": "PC typing keyboard Kacha",
       "type": "Realistic sound effects for typing on keyboards", "swish": "swish_whoosh (large)(794558)", "reveal": "Whoosh movie 6(1503715)",
       "wind": "Wind noise suitable for scene change", "shutter": "Camera shutter sound (analog)(808890)", "bass": "Bass impact(1171693)",
       "rise": "Rise Vibraphone Hightone Announcement Achieved(819061)", "impact": "Impact", "ding": 'Bell ring "ding!"',
       "crack": "Crack glass and glass 03", "click": 'Switch sound. "Click"(92853)', "pop": "Pop (lower) telop sound etc",
       "music": "Technology - IT - News - Electro(1696152)"}
DUR = {"hit": 1.8, "stamp": .33, "swish": .8, "reveal": 1.6, "wind": 1.0, "shutter": .85, "bass": 1.4, "rise": 1.5, "impact": 1.2,
       "ding": 1.2, "crack": 1.1, "click": .4, "pop": .4}
VOL = {"hit": .5, "stamp": .45, "swish": .28, "reveal": .38, "wind": .28, "shutter": .35, "bass": .42, "rise": .32, "impact": .4,
       "ding": .35, "crack": .38, "click": .3, "pop": .25, "keys": .32, "type": .3}
TR = {"whip": "wind", "zoom": "swish", "flash": "shutter", "flash_red": "bass", "slam": "impact", "pop": "pop"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--title")
    ap.add_argument("--music-start", type=float)
    ap.add_argument("--music-vol", type=float, default=.13)
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    tl = json.loads((proj / "render" / "timeline.json").read_text(encoding="utf-8"))
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    extra = {str(s["id"]): s.get("sfx_extra") or [] for s in sb["scenes"]}
    title = a.title or f"{tl.get('title') or proj.name} (hau ky)"
    mstart = a.music_start if a.music_start is not None else float((sb.get("edit_profile") or {}).get("music_start", 0))

    plan = []
    def add(t, k, why, sc, d=None, v=None):
        if k == "pop" and any(x[1] == "pop" and abs(x[0] - t) < .2 for x in plan):  # 2 thứ bật cùng lúc → 1 tiếng
            return
        plan.append((round(t, 2), k, d or DUR.get(k, 1.0), v or VOL[k], sc, why))

    for i, s in enumerate(tl["scenes"]):
        sid, st, p = s["id"], s["start"], s.get("p") or {}
        k = TR.get(s.get("transition_in"))
        if i and k:
            add(st, k, f"chuyển cảnh {s['transition_in']}", sid)
        if s.get("climax"):
            add(st + .05, "hit", "cao trào", sid); add(st + .05, "reveal", "lật mở cao trào", sid)
        for kw in s.get("keywords") or []:
            e, at = kw.get("effect"), kw.get("at", st)
            if e == "stamp_slam": add(at + .08, "stamp", f"dấu '{kw['text']}'", sid)
            elif e == "warning": add(at, "crack", f"cảnh báo '{kw['text']}'", sid)
            elif e == "count": add(at, "rise", f"số '{kw['text']}' chạy", sid, d=1.4)
        for g in s.get("callouts") or []:
            for it in g.get("items") or [g]:
                add(it.get("at", st), "pop", f"'{it.get('name', '')}' bật ra", sid, v=.3)
        for r in p.get("rings") or []:
            add(r.get("at", st + .6), "pop", f"khoanh '{r.get('label', '')}'", sid)
        for f in p.get("freeze") or []:
            add(f.get("at", st + 1), "shutter", "đóng băng khung + khoanh", sid)
        if p.get("prompt"):
            pr = p["prompt"]; t0 = pr.get("at", st + .3); n = len(pr["text"]) * pr.get("speed", .035)
            add(t0, "type", "gõ câu lệnh", sid, d=round(min(max(.5, n), 3.4), 2))
        if p.get("timer"):
            tm = p["timer"]; t0 = tm.get("at", st + .5)
            add(t0, "keys", "đồng hồ chạy", sid, d=round(tm.get("dur", 2), 2), v=.25); add(t0 + tm.get("dur", 2), "ding", "chốt giờ", sid)
        for x in extra.get(str(sid), []):
            add(st + float(x.get("at_clip", 0)), x["key"], x.get("why", "thêm tay"), sid, d=x.get("dur"), v=x.get("volume"))

    found = {}
    for f in glob.glob(str(ROOT / "*" / "draft_content.json")):
        if title in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mats = {m["id"]: m for m in d.get("materials", {}).get("audios", [])}
        for t in d.get("tracks", []):
            if t["type"] != "audio":
                continue
            for s in t["segments"]:
                m = mats.get(s["material_id"])
                if m and m.get("name") in LIB.values() and m["name"] not in found and os.path.exists(m.get("path", "")):
                    found[m["name"]] = (d, s, t)
    need = {k for _, k, *_ in plan} | ({"music"} if not a.no_music else set())
    miss = [k for k in need if LIB[k] not in found]
    if miss:
        sys.exit(f"STOP: thiếu mẫu tiếng {miss} trong thư viện CapCut trên máy (tải mẫu đó vào 1 project CapCut bất kỳ rồi chạy lại).")

    draft = ROOT / title / "draft_content.json"
    if not draft.exists():
        sys.exit(f"STOP: chưa có draft '{title}'. Chạy trước: compose.py {a.project} --capcut")
    doc = json.load(open(draft, encoding="utf-8"))
    amats = {m["id"]: m for m in doc["materials"].get("audios", [])}
    # bỏ SFX/nhạc cũ, giữ giọng kể (extract_music)
    doc["tracks"] = [t for t in doc["tracks"] if t["type"] != "audio" or any(amats.get(x["material_id"], {}).get("type") == "extract_music" for x in t["segments"])]
    lanes, cues = [], []
    for at, key, dur, vol, scn, why in sorted(plan):
        sd, ss, st_ = found[LIB[key]]
        seg, mat, _ = B.Cloner(sd, doc["materials"]).segment(ss)
        d = min(int(dur * US), mat.get("duration", int(dur * US)))
        seg.update({"source_timerange": {"start": 0, "duration": d}, "target_timerange": {"start": int(at * US), "duration": d}, "speed": 1.0, "volume": vol})
        for lane in lanes:
            if lane["end"] <= at - .01:
                break
        else:
            lane = {"end": 0, "track": copy.deepcopy(st_)}; lane["track"]["id"] = B.new_id(); lane["track"]["segments"] = []; lanes.append(lane)
        lane["track"]["segments"].append(seg); lane["end"] = at + d / US
        cues.append({"kind": "sfx", "scene": scn, "time": round(at, 2), "end": round(at + d / US, 2), "timecode": f"{int(at // 60):02d}:{at % 60:05.2f}",
                     "sound": f"{why} ({LIB[key]})", "search": LIB[key], "volume": vol, "why": why})
    n_music = 0
    if not a.no_music:
        sd, ss, st_ = found[LIB["music"]]
        mtrack = copy.deepcopy(st_); mtrack["id"] = B.new_id(); mtrack["segments"] = []
        fades = doc["materials"].setdefault("audio_fades", [])
        t0, end = mstart, tl["duration"] - .2
        while end - t0 > 1:
            seg, mat, _ = B.Cloner(sd, doc["materials"]).segment(ss)
            dd = min(end - t0, mat.get("duration", 0) / US - .5)
            seg.update({"source_timerange": {"start": 0, "duration": int(dd * US)}, "target_timerange": {"start": int(t0 * US), "duration": int(dd * US)},
                        "speed": 1.0, "volume": a.music_vol})
            fid = str(uuid.uuid4()).upper()
            fades.append({"id": fid, "type": "audio_fade", "fade_in_duration": 1_500_000, "fade_out_duration": 2_000_000, "fade_type": 0})
            seg.setdefault("extra_material_refs", []).append(fid)
            mtrack["segments"].append(seg); t0 += dd; n_music += 1
        doc["tracks"].append(mtrack)
    doc["tracks"] += [l["track"] for l in lanes]
    B.dump(doc, draft)
    tlp = ROOT / title / "Timelines" / doc["id"] / "draft_content.json"
    if tlp.parent.exists():
        B.dump(doc, tlp)
    (proj / "narration").mkdir(exist_ok=True)
    (proj / "narration" / "sfx_cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# SFX đã chèn vào CapCut (đúng giây timeline, có mốc kết thúc)\n", "| Bắt đầu | Kết thúc | Cảnh | SFX | Âm lượng | Vì sao |", "|---|---|---|---|---|---|"]
    md += [f"| {c['time']:.2f} | {c['end']:.2f} | {c['scene']} | {c['search']} | {c['volume']} | {c['why']} |" for c in cues]
    (proj / "narration" / "sfx_cues.md").write_text("\n".join(md), encoding="utf-8")
    print(f"OK: chèn {len(cues)} SFX ({len(lanes)} track) + nhạc nền {n_music} đoạn từ {mstart:.1f}s vào '{title}'.")


if __name__ == "__main__":
    main()
