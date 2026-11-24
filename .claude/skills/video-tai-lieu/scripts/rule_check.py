"""Tự soát bộ luật dựng (references/luat-dung.md) trên timeline thật → render/rule_report.md

  python rule_check.py projects/<slug>

Chạy SAU plan_timeline.py (cần render/timeline.json, render/sfx_plan.json). Chỉ báo, không sửa gì.
In "OK: …" khi không có ✗. Luật cố ý vi phạm: ghi storyboard["rule_notes"] = {"R4": "lý do"} → báo "bỏ qua (có lý do)".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_timeline import KNOWN_NAMES, toks  # noqa: E402

SIGNATURE = {"converge", "transform", "waffle", "duo", "prompt_video", "people", "breakout", "dot_number", "timeline", "slider",
             "orbit3d", "exploded3d", "race", "line_chart", "area_compare", "strike_cards", "open_loop"}
HEAVY_KW = {"stamp_slam", "warning", "crack", "giftbox"}
HIT_TR = {"flash", "flash_red", "slam"}


def ats(o, out: list):
    """Gom mọi mốc 'at' / '*_at' trong một cấu trúc (từ khoá, callout, nhịp, khoanh, mục liệt kê…)."""
    if isinstance(o, dict):
        for k, v in o.items():
            if (k == "at" or k.endswith("_at")) and isinstance(v, (int, float)):
                out.append(float(v))
            else:
                ats(v, out)
    elif isinstance(o, list):
        for v in o:
            ats(v, out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    tl = json.loads((proj / "render" / "timeline.json").read_text(encoding="utf-8"))
    sfx_p = proj / "render" / "sfx_plan.json"
    sfx = json.loads(sfx_p.read_text(encoding="utf-8")) if sfx_p.exists() else []
    notes = sb.get("rule_notes") or {}
    text = {s["id"]: s.get("text") or s.get("narration") or "" for s in sb["scenes"]}
    R: dict[str, list[str]] = {k: [] for k in ["R1", "R4", "R5", "R6", "Q2", "Q6", "Q8", "Q9", "S2", "P2"]}

    hits, heavy, sig = [], [], {}
    plain_run = []
    REAL = ("bg_video", "bg_photo", "photo", "video", "levels", "stops")
    events = []
    for s in tl["scenes"]:
        st, en, p, sid = s["start"], s["end"], s.get("p") or {}, s["id"]
        mods = [s["module"]] + [b.get("module") for b in (p.get("then") or []) if isinstance(b, dict)]
        for m in mods:
            if m in SIGNATURE:
                sig.setdefault(m, []).append(sid)
        tt = ats([p, s.get("keywords") or [], s.get("callouts") or []], [])
        events += [st] + [t for t in tt if st - .1 <= t <= en]
        has_real = any(k in json.dumps(p, ensure_ascii=False) for k in (f'"{r}"' for r in REAL)) or s["module"] in ("map", "screen", "photo", "evidence", "letterbox")
        if has_real:
            if len(plain_run) > 2:
                R["Q8"].append(f"{len(plain_run)} cảnh liền chỉ có nền trơn: cảnh {', '.join(map(str, plain_run))} (thêm bg_video/bg_photo/ảnh thật)")
            plain_run = []
        else:
            plain_run.append(sid)
        if s["module"] in ("screen", "timeline", "prompt_video", "slider", "photo", "evidence") and s.get("keywords"):
            bad = [k.get("text", "") for k in s["keywords"] if k.get("x") is None and not (s["module"] == "screen" and p.get("side"))]
            if bad:
                R["Q9"].append(f"cảnh {sid} ({s['module']}): chữ chốt {bad} có thể che bằng chứng — xếp cột riêng (side + x/w) hoặc dùng khoanh viền")
        bgv = str(p.get("bg_video") or "")
        if bgv and (re.search(r"(^|/)(rec|screen|quay)[/_]|screen_?rec|quay_?man", bgv.replace("\\", "/"), re.I) or "màn hình" in str(p.get("bg_source") or "")):
            R["Q9"].append(f"cảnh {sid} ({s['module']}): quay màn hình '{Path(bgv).name}' bị làm NỀN mờ dưới graphic — thao tác phải hiện rõ (module screen + cột chữ riêng), nền chỉ dùng cảnh trang trí")
        late = [t for t in tt if en - .8 < t <= en]
        for k in s.get("keywords") or []:
            if k.get("effect") in HEAVY_KW and k.get("at") is not None:
                heavy.append((k["at"], sid, k.get("text", "")))
        if late and en - st > 1.5:
            R["R1"].append(f"cảnh {sid}: có thứ bật lên lúc {max(late):.1f}s, chỉ {en - max(late):.1f}s trước khi cắt (cần ≥1s để người xem kịp đọc)")
        if s.get("transition_in") in HIT_TR:
            hits.append((st, sid, s["transition_in"]))
        if s["module"] == "title" and en - st > 2.6 and not p.get("then"):
            R["R5"].append(f"cảnh {sid}: tiêu đề lớn treo {en - st:.1f}s, chưa có p.then")
        said = " ".join(toks(text.get(sid, "")))
        have = " ".join(toks(json.dumps(s.get("callouts") or [], ensure_ascii=False)))
        for g in s.get("callouts") or []:
            for it in g.get("items") or [g]:
                if it.get("name") and not (it.get("logo") or it.get("photo") or it.get("no_logo")):  # no_logo: "lý do" (vd chưa có logo chính thức)
                    R["Q2"].append(f"cảnh {sid}: thẻ '{it['name']}' chỉ có chữ — tải logo/ảnh thật: find_photo.py \"{it['name']} logo\" --pick 1 --save brand/logos/<tên>.png")
        for nm in KNOWN_NAMES:
            if re.search(rf"\b{nm}\b", said) and nm not in have:
                R["Q2"].append(f"cảnh {sid}: gọi tên '{nm}' nhưng chưa có logo")
    if len(plain_run) > 2:
        R["Q8"].append(f"{len(plain_run)} cảnh liền chỉ có nền trơn: cảnh {', '.join(map(str, plain_run))} (thêm bg_video/bg_photo/ảnh thật)")
    if len(hits) > 3:
        R["R4"].append(f"{len(hits)} chuyển cảnh đập cả khung (flash/slam) > 3: " + ", ".join(f"cảnh {i} {k}@{t:.0f}s" for t, i, k in hits))
    heavy.sort()
    for (t0, i0, w0), (t1, i1, w1) in zip(heavy, heavy[1:]):
        if t1 - t0 < 8:
            R["R4"].append(f"chữ chốt nặng sát nhau {t1 - t0:.1f}s: '{w0}' (cảnh {i0}) → '{w1}' (cảnh {i1})")
    ev = sorted(set(round(e, 2) for e in events)) + [tl["duration"]]
    for e0, e1 in zip(ev, ev[1:]):
        if e1 - e0 > 8:
            R["R6"].append(f"{e0:.1f}s → {e1:.1f}s: {e1 - e0:.1f}s không có gì mới bật ra (móc mới mỗi 5–8s)")
    for m, ids in sig.items():
        if len(ids) > 1:
            R["Q6"].append(f"kiểu '{m}' làm vai chính {len(ids)} lần (cảnh {', '.join(map(str, ids))})")
    by = {}
    for x in sfx:
        by.setdefault(x.get("search") or x.get("sound"), []).append(x)
    for k, xs in by.items():
        xs.sort(key=lambda x: x["time"])
        run = [xs[0]]
        for x in xs[1:] + [None]:
            if x is not None and x["time"] - run[-1]["time"] < .7:
                run.append(x)
                continue
            if len(run) >= 3 and not all(r.get("ladder") for r in run):
                R["S2"].append(f"'{k}' lặp {len(run)} lần dồn dập từ {run[0]['time']:.1f}s (chưa xen mẫu / giảm âm lượng)")
            run = [x] if x is not None else []
    rp = proj / "render" / "review_report.md"
    if not rp.exists():
        R["P2"].append("chưa có render/review_report.md (kiểm cuối độc lập trước khi gửi anh)")
    elif "KẾT LUẬN: ĐẠT" not in rp.read_text(encoding="utf-8"):
        R["P2"].append("báo cáo kiểm cuối chưa ĐẠT — sửa lỗi rồi giao agent MỚI kiểm lại")

    names = {"R1": "Chốt xong phải thở ≥1s", "R4": "Cú đập cả khung ≤3, chữ nặng cách ≥8s", "R5": "Tiêu đề lớn không treo đơ",
             "R6": "Móc mới mỗi 5–8s", "Q2": "Gọi tên là có logo/ảnh thật", "Q6": "Mỗi kiểu graphic 'đinh' chỉ 1 lần", "Q8": "Không để nền đen trơn kéo dài", "Q9": "Graphic không che bằng chứng",
             "S2": "SFX chống súng máy", "P2": "Kiểm cuối độc lập"}
    md = ["# Báo cáo tự soát luật dựng", "", "Luật đầy đủ: video-tai-lieu/references/luat-dung.md. Q11 (chữ đọc được) → xem kết quả qa_layout.py.", ""]
    bad = 0
    for k, v in R.items():
        if not v:
            md.append(f"- **{k} ✓** {names[k]}")
        elif k in notes:
            md.append(f"- **{k} ~** {names[k]} — bỏ qua (có lý do: {notes[k]})")
        else:
            bad += 1 if k != "P2" else 0
            md.append(f"- **{k} ✗** {names[k]}")
            md += [f"    - {x}" for x in v]
    out = proj / "render" / "rule_report.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\n{'OK: không vi phạm luật tự soát được.' if not bad else str(bad) + ' luật bị vi phạm — sửa storyboard hoặc ghi lý do vào rule_notes.'}  → {out}")


if __name__ == "__main__":
    main()
