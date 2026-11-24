"""Tự kiểm bố cục trên khung hình THẬT trước khi render: chữ đè nhau, chữ tràn khung, chữ quá nhỏ.

  python qa_layout.py projects/<slug>            # 3 mốc mỗi cảnh (giữa, 80%, gần cuối) — tránh lúc đang chuyển cảnh
  python qa_layout.py projects/<slug> --at 12.5 30   # thêm mốc tuỳ chọn

In lỗi kèm giây + nội dung chữ; lưu ảnh khung lỗi render/qa_<giây>.jpg (khoanh đỏ chỗ đè) để xem (Read). Thoát mã 1 nếu có lỗi.
Không tính: các từ trong cùng 1 dòng sub, chữ nằm trong cùng một khối (cha–con), chữ gần như trong suốt (đang hiện/ẩn).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ENGINE = (SKILL / "templates" / "engine.html").as_uri()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

JS = r"""
(U) => {
  const st = document.getElementById('stage'), S = st.getBoundingClientRect();
  const vis = e => { let o = 1; for (let n = e; n && n !== st; n = n.parentElement) { const c = getComputedStyle(n); if (c.display === 'none' || c.visibility === 'hidden') return 0; o *= +c.opacity; } return o; };
  const out = [];
  for (const e of st.querySelectorAll('*')) {
    if (['SCRIPT','STYLE','svg','path','CANVAS','IMG','VIDEO'].includes(e.tagName)) continue;
    const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    const qb = e.classList.contains('qabox');  // thẻ logo/ảnh: tính cả khung, không chỉ chữ
    if (!own && !qb) continue;
    const o = vis(e); if (o < .6) continue;
    const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
    if (!qb && !/[\p{L}\p{N}]/u.test(own)) continue;  // biểu tượng / emoji trang trí
    const grp = e.closest('#subs') ? 'subs' : (e.closest('.source') || /^(Ảnh|Nguồn)\s*:/.test(own)) ? 'source' : e.closest('#brandtag') ? 'brand' : 'main';
    out.push({t: qb ? '[thẻ ' + e.dataset.qname + ']' : own.slice(0, 40), x: r.left - S.left, y: r.top - S.top, w: r.width, h: r.height, fs: parseFloat(getComputedStyle(e).fontSize), grp, id: out.length, el: null});
    e.dataset.qa = out.length - 1;
  }
  // vùng BẰNG CHỨNG (cửa sổ quay màn hình, khung video, thẻ ảnh): chữ chốt (#kw) không được đè lên
  const ev = [];
  for (const e of st.querySelectorAll('.qa-ev')) { if (vis(e) < .6) continue; const r = e.getBoundingClientRect(); if (r.width < 4 || r.height < 4) continue;
    ev.push({x: r.left - S.left, y: r.top - S.top, w: r.width, h: r.height}); }
  for (const a of out) a.kw = 0;
  for (const e of st.querySelectorAll('#kw [data-qa]')) out[+e.dataset.qa].kw = 1;
  // cha–con (cùng khối) không tính là đè
  const anc = {}; for (const e of st.querySelectorAll('[data-qa]')) { const a = []; for (let n = e.parentElement; n && n !== st; n = n.parentElement) if (n.dataset.qa) a.push(+n.dataset.qa); anc[e.dataset.qa] = a; }
  for (const e of st.querySelectorAll('[data-qa]')) delete e.dataset.qa;
  return {items: out, anc, ev, W: S.width, H: S.height};
}
"""


MIN_MAIN, WARN_MAIN, MIN_SUB = 2.0, 2.8, 4.0  # đơn vị U (=1% cạnh ngắn). Luật Q11: chữ phải đọc được trên điện thoại
WARN: set = set()


def check(d: dict, U: float, v2: bool = False) -> list[str]:
    it, anc, W, H = d["items"], d["anc"], d["W"], d["H"]
    errs = []
    for a in it:
        if a["x"] < -2 or a["y"] < -2 or a["x"] + a["w"] > W + 2 or a["y"] + a["h"] > H + 2:
            errs.append(f"tràn khung: '{a['t']}'")
        if a["grp"] == "main" and not a["t"].startswith("[thẻ"):
            mn = MIN_MAIN if v2 else 1.7  # v1 (video cũ) giữ ngưỡng cũ để dựng lại y nguyên
            if a["fs"] < mn * U:
                errs.append(f"chữ nhỏ ({a['fs']:.0f}px < {mn * U:.0f}px): '{a['t']}'")
            elif v2 and a["fs"] < WARN_MAIN * U:
                WARN.add(f"{a['t'][:30]} ({a['fs']:.0f}px)")
        if v2 and a["grp"] == "subs" and a["fs"] < MIN_SUB * U:
            errs.append(f"sub nhỏ ({a['fs']:.0f}px < {MIN_SUB * U:.0f}px), khó đọc trên điện thoại")
    for a in it:  # luật Q9: chữ chốt / sub không che bằng chứng
        if a["grp"] == "subs":
            for e in d.get("ev", []):
                ix = max(0, min(a["x"] + a["w"], e["x"] + e["w"]) - max(a["x"], e["x"]))
                iy = max(0, min(a["y"] + a["h"], e["y"] + e["h"]) - max(a["y"], e["y"]))
                if a["w"] * a["h"] and ix * iy / (a["w"] * a["h"]) > .25:
                    errs.append(f"sub đè lên khung bằng chứng: '{a['t']}' (thu nhỏ/đẩy khung lên, hoặc tăng profile.sub_bottom)")
                    break
            continue
        if not a.get("kw"):
            continue
        for e in d.get("ev", []):
            ix = max(0, min(a["x"] + a["w"], e["x"] + e["w"]) - max(a["x"], e["x"]))
            iy = max(0, min(a["y"] + a["h"], e["y"] + e["h"]) - max(a["y"], e["y"]))
            if a["w"] * a["h"] and ix * iy / (a["w"] * a["h"]) > .08:
                errs.append(f"chữ chốt che bằng chứng: '{a['t']}' (dời sang cột trống / pos khác)")
                break
    for i, a in enumerate(it):
        for b in it[i + 1:]:
            if a["grp"] == b["grp"] == "subs":
                continue
            if b["id"] in anc.get(str(a["id"]), []) or a["id"] in anc.get(str(b["id"]), []):
                continue
            ix = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
            iy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
            sm = min(a["w"] * a["h"], b["w"] * b["h"])
            if sm and ix * iy / sm > .12:
                errs.append(f"đè nhau: '{a['t']}' × '{b['t']}'")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--at", nargs="*", type=float, default=[])
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    tl = json.loads((proj / "render" / "timeline.json").read_text(encoding="utf-8"))
    U = min(tl["W"], tl["H"]) / 100
    times = sorted({round(t, 2) for sc in tl["scenes"] for t in (sc["start"] + (sc["end"] - sc["start"]) * f for f in (.5, .8)) } |
                   {round(sc["end"] - .15, 2) for sc in tl["scenes"]} | set(a.at) |
                   {round(max(it.get("at", sc["start"]) for it in (g.get("items") or [g])) + .7, 2) for sc in tl["scenes"] for g in sc.get("callouts") or []} |
                   {round(k["at"] + .6, 2) for sc in tl["scenes"] for k in sc.get("keywords") or [] if k.get("at") is not None})
    from playwright.sync_api import sync_playwright
    bad = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
        pg = br.new_page(viewport={"width": tl["W"], "height": tl["H"]})
        pg.goto(ENGINE)
        pg.evaluate("tl => window.init(tl)", tl)
        for t in times:
            pg.evaluate("t => window.renderAtAsync(t)", t)
            d = pg.evaluate(JS, U)
            errs = sorted(set(check(d, U, tl.get("design") == "v2")))
            if errs:
                bad += 1
                f = proj / "render" / f"qa_{t:06.2f}.jpg"
                pg.screenshot(path=str(f), type="jpeg", quality=80)
                print(f"✗ {t:6.2f}s  ({f.name})")
                for e in errs:
                    print("    - " + e)
        br.close()
    if WARN:
        print(f"\n⚠ {len(WARN)} chữ hơi nhỏ khi xem điện thoại (< {WARN_MAIN}% cạnh ngắn, không chặn): " + "; ".join(sorted(WARN)[:12]))
    print(f"\n{'OK: không thấy chữ đè / tràn / quá nhỏ ở ' + str(len(times)) + ' mốc.' if not bad else str(bad) + ' mốc có lỗi bố cục — sửa storyboard (pos, dx/dy, size) rồi chạy lại.'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
