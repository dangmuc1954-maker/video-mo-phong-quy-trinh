/* video-tai-lieu engine: renderAt(t) draws one deterministic frame of the timeline.
   timeline = {W,H,fps,duration,brand,profile,scenes:[...],subs:[...]} (built by plan_timeline.py) */
(function () {
  "use strict";
  // ---------------- helpers ----------------
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const prog = (t, a, d) => clamp((t - a) / Math.max(d, 1e-6));
  const E = {
    out: k => 1 - Math.pow(1 - k, 3),
    inout: k => (k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    back: k => { const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
    expo: k => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
    elastic: k => (k === 0 || k === 1) ? k : Math.pow(2, -9 * k) * Math.sin((k * 10 - .75) * 2.1) + 1,
    slam: k => (k < .55 ? Math.pow(k / .55, 2) : 1 + Math.sin((k - .55) / .45 * Math.PI) * .06 * (1 - k)),
  };
  function rnd(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
  const el = (tag, cls, html, parent) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; if (parent) parent.appendChild(e); return e; };
  const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  // *x* = accent, _x_ = accent2, \n = line break
  const mark = s => esc(s).replace(/\*([^*]+)\*/g, '<span class="acc">$1</span>').replace(/_([^_]+)_/g, '<span class="acc2">$1</span>').replace(/\n/g, "<br>");
  const fmtNum = (v, dec, sep) => { const f = Number(v).toFixed(dec || 0); const [i, d] = f.split("."); const g = i.replace(/\B(?=(\d{3})+(?!\d))/g, sep == null ? "." : sep); return d ? g + "," + d : g; };
  const set = (e, o, tr) => { if (!e) return; e.style.opacity = o; if (tr != null) e.style.transform = tr; };

  const VIDS = []; let HEADER = null; let TL, W, H, U, stage, scenesRoot, subsEl, kwRoot, flashEl, grainEl, vigEl, ICON = "", IMGS = {};
  const S = []; // built scenes {d, root, cam, mod, kw}
  let V2 = false, GEO = {}; const FEATH = {};

  // ---------------- mood (lớp 3) ----------------
  const MOODS = {
    neutral: { filter: "", shake: 0, grain: .06, vig: "rgba(0,0,0,.45)" },
    positive: { filter: "saturate(1.12) brightness(1.04)", shake: 0, grain: .04, vig: "rgba(40,20,0,.3)" },
    fun: { filter: "saturate(1.25) brightness(1.05)", shake: 0, grain: 0, vig: "rgba(0,0,0,.15)" },
    tense: { filter: "saturate(.8) contrast(1.08)", shake: .6, grain: .12, vig: "rgba(0,0,0,.7)" },
    dark: { filter: "saturate(.55) contrast(1.15) brightness(.82)", shake: 1.4, grain: .18, vig: "rgba(40,0,0,.8)" },
    shock: { filter: "contrast(1.12)", shake: 2.2, grain: .1, vig: "rgba(0,0,0,.6)" },
    sad: { filter: "saturate(.6) brightness(.92) hue-rotate(-8deg)", shake: 0, grain: .08, vig: "rgba(0,10,30,.55)" },
    calm: { filter: "saturate(.95)", shake: 0, grain: .04, vig: "rgba(0,0,0,.3)" },
  };

  // ---------------- shared header ----------------
  function header(root, p) {
    if (!p.title && !p.kicker) return null;
    const h = el("div", "hdr", null, root);
    if (p.kicker) el("div", "kicker", mark(p.kicker), h);
    if (p.title) el("div", "headline", mark(p.title), h).style.fontSize = `calc(var(--u)*${p.title_size || 8})`;
    if (p.subtitle) el("div", "subline", mark(p.subtitle), h);
    return h;
  }
  function headerUpdate(h, lt) { if (!h) return; const k = E.out(prog(lt, .05, .5)); h.style.opacity = k; h.style.transform = `translateX(${(1 - k) * -40}px)`; }
  function sourceLine(root, p) { if (!p.source) return null; return el("div", "source", "Nguồn: " + esc(p.source), root); }
  function icon(name) { const i = el("span", "ico"); i.style.webkitMaskImage = `url(${ICON}${name}.svg)`; return i; }
  function img(src, cls) { const i = el("img", cls || ""); i.src = src; return i; }

  // ---------------- MODULES (lớp 2) ----------------
  const M = {};

  // TITLE / chapter card (kicker + headline with accent words)
  M.title = (root, p, sc) => {
    // Tiêu đề lớn chỉ "đập" ~1.2s rồi bay ra; phần còn lại của cảnh do các nhịp graphic p.then diễn đúng lời kể.
    const tw = el("div", null, null, root); tw.style.cssText = "position:absolute;inset:0";
    const c = el("div", "center", null, tw);
    const pill = p.pill ? el("div", "pillk", "• " + esc(p.pill) + " •", c) : null;
    const k = p.kicker ? el("div", "kicker", mark(p.kicker), c) : null;
    const hl = el("div", "headline", mark(p.title || ""), c); hl.style.fontSize = `calc(var(--u)*${p.size || 10})`;
    const sb = p.subtitle ? el("div", "subline", mark(p.subtitle), c) : null;
    const tagE = p.tag ? el("div", "tag yellow", esc(p.tag), c) : null;
    if (tagE) { tagE.style.position = "relative"; tagE.style.marginTop = "1.2em"; tagE.style.fontSize = "calc(var(--u)*2.6)"; }
    if (p.title_exit === "label") { const r = hl.getBoundingClientRect(), S0 = stage.getBoundingClientRect(); tw._r = { x: r.left - S0.left, y: r.top - S0.top }; } // đo khi chưa biến đổi
    const raw = Array.isArray(p.then) ? p.then : p.then ? [p.then] : [];
    const t0 = p.title_at != null ? p.title_at - sc.start : 0;
    const hold = p.title_hold != null ? p.title_hold : raw.length ? 1.2 : 1e9;
    const tEnd = sc.start + t0 + hold;
    const starts = raw.map((b, i) => b.at != null ? b.at : i === 0 ? tEnd + .1 : null);
    for (let i = 1; i < starts.length; i++) if (starts[i] == null) starts[i] = starts[i - 1] + (sc.end - starts[i - 1]) / (raw.length - i + 1);
    const beats = raw.map((b, i) => { const bw = el("div", null, null, root); bw.style.cssText = "position:absolute;inset:0;opacity:0";
      const st = starts[i], en = i + 1 < raw.length ? starts[i + 1] : sc.end; const sub = { ...sc, start: st, end: en, p: b.p || {} };
      return { bw, m: (M[b.module] || M.title)(bw, b.p || {}, sub), st, en, last: i + 1 === raw.length }; });
    return { update(lt, dur, t) {
      const L = lt - t0; tw.style.display = L < -.02 ? "none" : "block";
      set(pill, E.out(prog(L, 0, .4)));
      set(k, E.out(prog(L, .05, .4)), `translateY(${(1 - E.out(prog(L, .05, .4))) * 30}px)`);
      const a = prog(L, .1, .55); set(hl, clamp(a * 2), `scale(${lerp(1.25, 1, E.back(a))})`); hl.style.filter = `blur(${(1 - clamp(a * 1.6)) * 14}px)`;
      set(sb, E.out(prog(L, .45, .5)));
      if (tagE) { const q = prog(lt, p.tag_at != null ? p.tag_at - sc.start : t0 + .9, .35); set(tagE, clamp(q * 2), `scale(${lerp(.6, 1, E.back(q))})`); }
      if (p.title_exit === "label") { // thu thành nhãn mục: tiêu đề co 0.3x bay về góc trái trên và Ở LẠI làm nhãn của đoạn
        const e = E.inout(prog(lt, t0 + hold, .85)); const r = tw._r || { x: W * .3, y: H * .4 }, sc2 = lerp(1, p.label_scale || .3, e);
        tw.style.transformOrigin = `${r.x}px ${r.y}px`; tw.style.transform = e ? `translate(${(6 * U - r.x) * e}px,${(H * .075 - r.y) * e}px) scale(${sc2})` : "";
        for (const x of [pill, k, sb, tagE]) if (x) x.style.opacity = Math.min(+x.style.opacity || 0, 1 - clamp(e * 2.5));
      } else {
        const o = prog(lt, t0 + hold, .35); // bay ra: phóng to + nhoè + mờ
        tw.style.opacity = 1 - o; tw.style.transform = o ? `scale(${1 + E.inout(o) * .35}) translateY(${-o * 4 * U}px)` : ""; tw.style.filter = o ? `blur(${o * 14}px)` : "";
      }
      const T = t != null ? t : sc.start + lt;
      for (const b of beats) { const on = T >= b.st - .02 && T < b.en + .3; b.bw.style.display = on ? "block" : "none"; if (!on) continue;
        const ia = E.out(prog(T, b.st, .35)), oa = b.last ? 0 : prog(T, b.en - .1, .3);
        b.bw.style.opacity = ia * (1 - oa); b.bw.style.transform = `scale(${lerp(.94, 1, ia) + oa * .06})`; b.m.update(T - b.st, b.en - b.st, T); }
    } };
  };

  // BIG NUMBER count-up
  M.number = (root, p, sc) => {
    const h = header(root, p);
    const c = el("div", "center", null, root);
    const lab = p.label ? el("div", "pillk", esc(p.label), c) : null;
    const row = el("div", null, null, c); row.style.cssText = "display:flex;align-items:baseline;gap:.25em;margin-top:.3em";
    const num = el("div", "big", "", row); num.style.fontSize = `calc(var(--u)*${p.size || 22})`;
    const unit = p.unit ? el("div", "headline", mark(p.unit), row) : null; if (unit) unit.style.fontSize = "calc(var(--u)*6)";
    const note = p.note ? el("div", "subline", mark(p.note), c) : null;
    const src = sourceLine(root, p);
    const t0 = (p.at != null ? p.at : sc.start + .2) - sc.start;
    return { update(lt) {
      headerUpdate(h, lt); set(lab, E.out(prog(lt, t0 - .2, .4)));
      const k = prog(lt, t0, p.count || 1.1); const v = lerp(p.from || 0, p.value, E.out(k));
      num.textContent = (p.prefix || "") + fmtNum(v, p.decimals, p.format === "year" ? "" : p.sep) + (p.suffix || "");
      set(row, clamp(k * 4), `scale(${lerp(.7, 1, E.back(clamp(k * 1.5)))})`);
      set(note, E.out(prog(lt, t0 + .6, .5))); set(src, E.out(prog(lt, t0 + .4, .5)));
    } };
  };

  // STAT ROW with icons (accumulate)
  M.stats = (root, p, sc) => {
    const h = header(root, p);
    const wrap = el("div", null, null, root); wrap.style.cssText = `position:absolute;left:calc(var(--u)*4);right:calc(var(--u)*4);${p.top != null ? `top:${p.top}%` : `bottom:calc(var(--u)*${p.bottom || 34})`};display:flex;justify-content:space-around;gap:calc(var(--u)*2)`;
    const items = (p.items || []).map(it => {
      const b = el("div", null, null, wrap); b.style.cssText = "text-align:center;flex:1";
      const ic = el("div", null, null, b); ic.style.cssText = "width:calc(var(--u)*10);height:calc(var(--u)*10);margin:0 auto calc(var(--u)*1.6);border-radius:50%;background:var(--accent);display:flex;align-items:center;justify-content:center";
      if (it.icon) { const i = icon(it.icon); i.style.background = "#fff"; i.style.fontSize = "calc(var(--u)*4.6)"; ic.appendChild(i); }
      const v = el("div", "big", "", b); v.style.cssText += ";font-size:calc(var(--u)*9);color:#fff;white-space:nowrap";
      el("div", "pillk", esc(it.label || ""), b).style.cssText += ";background:none;padding:0;margin-top:calc(var(--u)*1.4);font-size:calc(var(--u)*2.6);color:var(--accent2)";
      return { b, v, it };
    });
    const src = sourceLine(root, p);
    return { update(lt) {
      headerUpdate(h, lt);
      items.forEach(({ b, v, it }, i) => { const a = (it.at != null ? it.at - sc.start : .4 + i * .7); const k = prog(lt, a, .5);
        set(b, clamp(k * 3), `translateY(${(1 - E.back(k)) * 40}px)`); const kv = prog(lt, a, .9);
        v.textContent = (it.prefix || "") + fmtNum(lerp(0, it.value, E.out(kv)), it.decimals, it.format === "year" ? "" : it.sep) + (it.unit ? " " + it.unit : ""); });
      set(src, E.out(prog(lt, .8, .5)));
    } };
  };

  // LIST build-up (chips accumulate) — also pipeline when p.flow
  M.list = (root, p, sc) => {
    const h = header(root, p);
    const box = el("div", null, null, root);
    box.style.cssText = p.flow ? "position:absolute;left:4%;right:4%;top:42%;display:flex;align-items:center;justify-content:center;gap:calc(var(--u)*1.5);flex-wrap:wrap"
      : `position:absolute;left:calc(var(--u)*6);right:calc(var(--u)*6);top:${p.top || 36}%;display:flex;flex-direction:column;gap:calc(var(--u)*1.8)`;
    const items = (p.items || []).map((it, i) => {
      const r = el("div", null, null, box); r.style.display = "flex"; r.style.alignItems = "center"; r.style.gap = "calc(var(--u)*1.5)";
      if (p.flow && i) { const ar = el("div", null, "→", r); ar.style.cssText = "font-size:calc(var(--u)*5);color:var(--accent);font-weight:800"; }
      const ch = el("div", "chip card", "", r);
      if (it.icon) ch.appendChild(icon(it.icon));
      el("span", null, mark(it.text), ch);
      if (it.check) { const ck = el("span", null, "✓", ch); ck.style.color = "var(--accent2)"; }
      return { r, it };
    });
    const src = sourceLine(root, p);
    return { update(lt) {
      headerUpdate(h, lt);
      items.forEach(({ r, it }, i) => { const a = it.at != null ? it.at - sc.start : .5 + i * .8; const k = prog(lt, a, .45);
        set(r, clamp(k * 3), p.flow ? `scale(${lerp(.5, 1, E.back(k))})` : `translateX(${(1 - E.out(k)) * -80}px)`); });
      set(src, E.out(prog(lt, .8, .5)));
    } };
  };

  // STEPS 1·2·3 (numbered chips, active lights up) + headline + points
  M.steps = (root, p, sc) => {
    const c = el("div", "center", null, root); c.style.justifyContent = "flex-start"; c.style.paddingTop = "34%";
    const nums = el("div", null, null, c); nums.style.cssText = "display:flex;gap:calc(var(--u)*1.6);margin-bottom:calc(var(--u)*3)";
    const n = p.total || 3, act = p.active || 1;
    const chips = []; for (let i = 1; i <= n; i++) { const b = el("div", "chip", String(i), nums); b.style.cssText += `;border:2px solid ${i === act ? "var(--accent)" : "#555"};background:${i === act ? "var(--accent)" : "rgba(255,255,255,.05)"};color:${i === act ? "#111" : "#ddd"}`; chips.push(b); }
    const hl = el("div", "headline", mark(p.title || ""), c); hl.style.fontSize = `calc(var(--u)*${p.size || 8.5})`;
    const pts = (p.points || []).map(pt => { const d = el("div", "chip card", mark(pt.text), c); d.style.cssText += ";margin-top:calc(var(--u)*1.6);font-size:calc(var(--u)*2.8);font-style:normal"; return { d, pt }; });
    return { update(lt) {
      chips.forEach((b, i) => { const k = prog(lt, i * .08, .3); set(b, k, `scale(${lerp(.4, 1, E.back(k))})`); });
      const k = prog(lt, .25, .5); set(hl, clamp(k * 2), `translateY(${(1 - E.out(k)) * 40}px)`); hl.style.filter = `blur(${(1 - clamp(k * 1.5)) * 10}px)`;
      pts.forEach(({ d, pt }, i) => { const a = pt.at != null ? pt.at - sc.start : 1 + i * .8; const q = prog(lt, a, .4); set(d, clamp(q * 3), `translateX(${(1 - E.out(q)) * 60}px)`); });
    } };
  };

  // QUESTION / twist / quote
  M.question = (root, p, sc) => {
    const c = el("div", "center", null, root);
    const q = p.quote ? el("div", "headline", "“", c) : null; if (q) { q.style.fontSize = "calc(var(--u)*14)"; q.style.color = "var(--accent)"; q.style.lineHeight = ".5"; }
    const hl = el("div", "headline", mark(p.text || ""), c); hl.style.fontSize = `calc(var(--u)*${p.size || 9.5})`;
    const by = p.by ? el("div", "subline", "— " + esc(p.by), c) : null;
    const tg = p.tag ? el("div", "tag yellow", esc(p.tag), c) : null; if (tg) { tg.style.position = "relative"; tg.style.marginTop = "1.4em"; tg.style.fontSize = "calc(var(--u)*2.6)"; }
    return { update(lt) {
      set(q, E.out(prog(lt, 0, .3)));
      const k = prog(lt, .05, .45); set(hl, clamp(k * 2.5), `scale(${lerp(1.6, 1, E.out(k))})`); hl.style.filter = `blur(${(1 - clamp(k * 1.4)) * 16}px)`;
      set(by, E.out(prog(lt, .6, .4)));
      if (tg) { const a = prog(lt, p.tag_at != null ? p.tag_at - sc.start : .8, .35); set(tg, clamp(a * 2), `scale(${lerp(.5, 1, E.back(a))}) rotate(-2deg)`); }
    } };
  };

  // COMPARE A vs B
  M.compare = (root, p, sc) => {
    const h = header(root, p);
    const row = el("div", null, null, root); row.style.cssText = `position:absolute;left:calc(var(--u)*4);right:calc(var(--u)*4);top:${p.top || 34}%;display:flex;gap:calc(var(--u)*2.5);align-items:stretch`;
    const side = (s, i) => { const c = el("div", "card", null, row); c.style.cssText += ";flex:1;min-width:0;padding:calc(var(--u)*2.6)";
      if (s.photo) { const ph = img(s.photo); ph.style.cssText = "width:100%;height:calc(var(--u)*24);object-fit:cover;border-radius:calc(var(--u)*1.2);margin-bottom:calc(var(--u)*2)"; c.appendChild(ph); }
      el("div", "pillk", esc(s.kicker || ""), c).style.cssText += ";background:none;padding:0;color:var(--accent)";
      const t = el("div", "headline", mark(s.title || ""), c); t.style.fontSize = "calc(var(--u)*4.6)";
      if (s.value != null) { const v = el("div", "big", (s.prefix || "") + fmtNum(s.value, s.decimals) + (s.unit ? " " + s.unit : ""), c); v.style.fontSize = `calc(var(--u)*${p.value_size || 7.2})`; v.style.marginTop = ".2em"; v.style.whiteSpace = "nowrap"; if (i === 1) v.style.color = "var(--accent2)"; }
      (s.lines || []).forEach(l => el("div", "subline", "• " + mark(l), c).style.fontSize = "calc(var(--u)*2.6)");
      return c; };
    const L = side(p.left || {}, 0); const vs = el("div", "headline", esc(p.vs || "VS"), row); vs.style.cssText += ";align-self:center;font-size:calc(var(--u)*6);color:var(--accent)"; const R = side(p.right || {}, 1);
    const src = sourceLine(root, p);
    const aL = (p.left && p.left.at != null ? p.left.at - sc.start : .3), aR = (p.right && p.right.at != null ? p.right.at - sc.start : 1.1);
    return { update(lt) {
      headerUpdate(h, lt);
      const kl = prog(lt, aL, .5), kr = prog(lt, aR, .5);
      set(L, clamp(kl * 3), `translateX(${(1 - E.out(kl)) * -120}px)`); set(R, clamp(kr * 3), `translateX(${(1 - E.out(kr)) * 120}px)`);
      set(vs, E.out(prog(lt, aR - .2, .3)), `scale(${lerp(2, 1, E.back(prog(lt, aR - .2, .4)))})`); set(src, E.out(prog(lt, 1, .5)));
    } };
  };

  // ICON GRID (tiện ích / đặc điểm)
  M.icons = (root, p, sc) => {
    const h = header(root, p);
    const g = el("div", null, null, root); g.style.cssText = `position:absolute;left:calc(var(--u)*5);right:calc(var(--u)*5);top:${p.top || 30}%;display:grid;grid-template-columns:repeat(${p.cols || 2},1fr);gap:calc(var(--u)*2)`;
    const items = (p.items || []).map(it => { const c = el("div", "card", null, g); c.style.cssText += ";display:flex;align-items:center;gap:calc(var(--u)*1.6);padding:calc(var(--u)*1.8)";
      const b = el("div", null, null, c); b.style.cssText = "flex:none;width:calc(var(--u)*6.5);height:calc(var(--u)*6.5);border-radius:calc(var(--u)*1.2);background:var(--accent);display:flex;align-items:center;justify-content:center";
      const i = icon(it.icon || "star"); i.style.background = "#fff"; i.style.fontSize = "calc(var(--u)*3.2)"; b.appendChild(i);
      el("div", null, mark(it.label), c).style.cssText = "font-weight:800;text-transform:uppercase;font-size:calc(var(--u)*2.5);line-height:1.15";
      return { c, it }; });
    const ph = p.photo ? (() => { const f = el("div", "polaroid", null, root); f.style.cssText += `;left:12%;right:12%;bottom:calc(var(--u)*30);height:calc(var(--u)*30);transform:rotate(-2deg)`; f.appendChild(img(p.photo)); if (p.photo_caption) { const cp = el("div", null, esc(p.photo_caption), f); cp.style.cssText = "color:#333;font-size:calc(var(--u)*1.8);margin-top:.5em;font-weight:500"; } return f; })() : null;
    const src = sourceLine(root, p);
    return { update(lt) {
      headerUpdate(h, lt);
      items.forEach(({ c, it }, i) => { const a = it.at != null ? it.at - sc.start : .4 + i * .45; const k = prog(lt, a, .4); set(c, clamp(k * 3), `scale(${lerp(.6, 1, E.back(k))})`); });
      if (ph) { const k = prog(lt, p.photo_at != null ? p.photo_at - sc.start : 1.4, .6); set(ph, clamp(k * 2), `translateY(${(1 - E.out(k)) * 200}px) rotate(${lerp(-8, -2, E.out(k))}deg)`); }
      set(src, E.out(prog(lt, 1, .5)));
    } };
  };

  // PHOTO in frame (real photo + caption + source)
  M.photo = (root, p, sc) => {
    const h = header(root, p);
    const f = el("div", "polaroid", null, root);
    const vert = H > W; f.style.cssText += (vert ? ";left:9%;right:9%;top:28%;height:44%" : ";left:24%;right:24%;top:14%;height:56%") + ";display:flex;flex-direction:column";
    f.classList.add("qa-ev");  // ảnh dẫn chứng: chữ chốt không được đè (Q9)
    const im = img(p.photo, p.bw ? "bw" : ""); im.style.cssText += ";flex:1 1 0;min-height:0;width:100%;height:auto;object-fit:cover"; f.appendChild(im);
    const cp = el("div", null, mark(p.caption || ""), f); cp.style.cssText = "flex:none;color:#222;font-weight:700;font-size:calc(var(--u)*2.2);margin-top:.5em;line-height:1.2"; if (!p.caption) cp.style.display = "none";
    const sr = p.source ? el("div", null, "Nguồn: " + esc(p.source), f) : null; if (sr) sr.style.cssText = "flex:none;color:#666;font-size:calc(var(--u)*1.6);margin-top:.3em";
    return { update(lt, dur) {
      headerUpdate(h, lt);
      const k = prog(lt, .1, .6); set(f, clamp(k * 2), `translateY(${(1 - E.out(k)) * 160}px) rotate(${lerp(6, p.rot != null ? p.rot : -1.5, E.out(k))}deg)`);
      im.style.transform = `scale(${lerp(1.0, 1.08, lt / Math.max(dur, 1))})`;
    } };
  };

  // DOSSIER CARD (nhân vật: ảnh thật + tên + biệt danh) — for theme dossier
  M.dossier = (root, p, sc) => {
    const vert = H > W;
    const card = el("div", "paper", null, root); card.style.cssText += vert ? ";left:8%;right:8%;top:28%;height:40%;border-radius:4px" : ";left:24%;right:24%;top:20%;height:60%;border-radius:4px";
    card.style.background = "#d9c39a";
    const tab = el("div", null, esc(p.file_label || "HỒ SƠ"), card); tab.style.cssText = "position:absolute;left:5%;top:4%;font-family:OSW;font-weight:600;letter-spacing:.2em;font-size:calc(var(--u)*2);color:#5a4528";
    const ph = el("div", "polaroid", null, card); ph.style.cssText += ";left:6%;top:16%;width:38%;height:70%;transform:rotate(-3deg)";
    if (p.photo) ph.appendChild(img(p.photo, "bw")); else { const s = el("div", null, "?", ph); s.style.cssText = "width:100%;height:100%;background:#222;color:#b3151c;display:flex;align-items:center;justify-content:center;font-family:OSW;font-size:calc(var(--u)*14)"; }
    const info = el("div", null, null, card); info.style.cssText = "position:absolute;left:50%;right:5%;top:18%;color:#1b140d";
    if (p.alias) el("div", null, esc(p.alias), info).style.cssText = "font-family:PFD;font-style:italic;font-size:calc(var(--u)*2.6);color:#5a4528";
    const nm = el("div", "tag red", esc(p.name || ""), info); nm.style.cssText += ";position:relative;display:inline-block;font-size:calc(var(--u)*5.5);margin:.2em 0";
    if (p.role) el("div", null, mark(p.role), info).style.cssText = "font-weight:700;font-size:calc(var(--u)*2.3);margin-top:.4em";
    (p.facts || []).forEach(f => el("div", null, "— " + mark(f), info).style.cssText = "font-family:PFD;font-size:calc(var(--u)*2.1);margin-top:.35em");
    const src = p.source ? el("div", null, "Ảnh: " + esc(p.source), card) : null; if (src) src.style.cssText = "position:absolute;left:6%;bottom:3%;font-size:calc(var(--u)*1.5);color:#5a4528";
    return { update(lt, dur) {
      const k = prog(lt, 0, .6); set(card, clamp(k * 2), `translate(${(1 - E.out(k)) * 300}px,${(1 - E.out(k)) * 80}px) rotate(${lerp(9, -1.5, E.out(k))}deg) scale(${lerp(1, 1.05, lt / Math.max(dur, 1))})`);
      const s = prog(lt, .55, .35); set(nm, clamp(s * 3), `scale(${lerp(1.8, 1, E.slam(s))}) rotate(-2deg)`);
    } };
  };

  // NEWSPAPER: masthead + headline + torn red/black labels stamped
  M.news = (root, p, sc) => {
    const vert = H > W;
    const pg = el("div", "paper", null, root); pg.style.cssText += vert ? ";left:-6%;right:-6%;top:12%;height:76%" : ";left:6%;right:6%;top:-4%;height:108%";
    const mh = el("div", null, esc(p.masthead || "THỜI SỰ"), pg); mh.style.cssText = "font-family:PFD;font-weight:900;text-align:center;font-size:calc(var(--u)*7);border-bottom:4px double #1b140d;padding:.3em 0 .1em;margin:0 6%";
    if (p.date) { const d = el("div", null, esc(p.date), pg); d.style.cssText = "text-align:center;font-family:PFD;font-style:italic;font-size:calc(var(--u)*2);margin:.4em 0"; }
    const hl = el("div", null, mark(p.headline || ""), pg); hl.style.cssText = "font-family:PFD;font-weight:900;text-transform:uppercase;font-size:calc(var(--u)*7.5);line-height:1;margin:.3em 6%";
    const body = el("div", null, null, pg); body.style.cssText = "columns:3;column-gap:1.2em;font-family:PFD;font-size:calc(var(--u)*1.8);line-height:1.35;margin:0 6%;color:#3b3025;text-align:justify";
    const filler = (esc(p.body || p.headline || "") + " ").repeat(60); body.innerHTML = filler;
    if (p.photo) { const ph = el("div", null, null, pg); ph.style.cssText = "float:right;width:40%;height:30%;margin:0 6% 0 0"; ph.appendChild(img(p.photo, "bw")); pg.insertBefore(ph, body); }
    const tags = (p.labels || []).map((lb, i) => { const t = el("div", "tag " + (lb.style || "red"), "", root);
      if (lb.small) el("div", null, esc(lb.small), t).style.cssText = "font-family:PFD;font-style:italic;font-weight:400;text-transform:none;font-size:.32em";
      el("div", null, mark(lb.text), t); t.style.fontSize = `calc(var(--u)*${lb.size || (vert ? 7 : 8)})`; t.style.whiteSpace = "nowrap";
      const x = lb.x != null ? lb.x : (i % 2 ? 30 : 6); if (x > 50) { t.style.right = (100 - x) + "%"; } else { t.style.left = x + "%"; } t.style.maxWidth = "88%";
      t.style.top = (lb.y != null ? lb.y : 40 + i * 13) + "%";
      t.style.clipPath = "polygon(0 4%,6% 0,20% 5%,38% 0,55% 4%,74% 0,92% 5%,100% 1%,99% 96%,85% 100%,66% 95%,47% 100%,28% 96%,10% 100%,0 95%)"; return { t, lb, i }; });
    return { update(lt, dur) {
      const k = prog(lt, 0, .7); set(pg, clamp(k * 2), `perspective(1400px) rotateX(${lerp(28, 14, E.out(k))}deg) rotateZ(${lerp(-6, -2, E.out(k))}deg) scale(${lerp(1.3, 1.02, E.out(k)) + lt / Math.max(dur, 1) * .06})`);
      tags.forEach(({ t, lb, i }) => { const a = lb.at != null ? lb.at - sc.start : .7 + i * .9; const s = prog(lt, a, .32); set(t, clamp(s * 4), `scale(${lerp(2.4, 1, E.slam(s))}) rotate(${lb.rot != null ? lb.rot : (i % 2 ? 2 : -3)}deg)`); });
    } };
  };


  // EVIDENCE: ảnh "dự kiến / trước" → mũi tên → ảnh "thực tế / sau" (bằng chứng thật)
  M.evidence = (root, p, sc) => {
    const h = header(root, p); const vert = H > W;
    const mk = (s, after) => { const f = el("div", "polaroid", null, root);
      f.style.cssText += vert ? (after ? ";left:6%;right:6%;top:45%;height:29%;padding-bottom:calc(var(--u)*1.2)" : ";left:14%;right:30%;top:23%;height:20%;padding-bottom:calc(var(--u)*1.2)")
                              : (after ? ";left:46%;right:5%;top:22%;height:62%" : ";left:6%;right:58%;top:30%;height:40%");
      const im = img(s.photo, after ? "" : "bw"); f.appendChild(im);
      const lb = el("div", "tag " + (after ? "red" : "black"), esc(s.label || (after ? "THỰC TẾ" : "DỰ KIẾN")), f); lb.style.cssText += ";left:-2%;top:-6%;font-size:calc(var(--u)*" + (after ? 4.4 : 3.2) + ")";
      if (after) lb.style.background = "var(--accent)";
      if (s.caption) { const c = el("div", null, mark(s.caption), f); c.style.cssText = "position:absolute;left:0;right:0;bottom:0;padding:.5em .8em;background:linear-gradient(transparent,rgba(0,0,0,.8));color:#fff;font-weight:700;font-size:calc(var(--u)*2.3)"; }
      if (s.source) { const c = el("div", null, "Ảnh: " + esc(s.source), f); c.style.cssText = "position:absolute;right:.6em;top:.4em;color:#fff;font-size:calc(var(--u)*1.5);text-shadow:0 1px 3px #000"; }
      let stat = null; if (s.stat) { stat = el("div", "big", "", f); stat.style.cssText += ";position:absolute;left:4%;bottom:18%;font-size:calc(var(--u)*13);color:#fff;text-shadow:0 .05em .3em rgba(0,0,0,.9)"; }
      let stamp = null; if (s.stamp) { stamp = el("div", "tag", mark(s.stamp.text), f); stamp.style.cssText += ";right:4%;top:12%;font-size:calc(var(--u)*5);background:" + (s.stamp.color || "#16a34a") + ";color:#fff"; }
      return { f, im, stat, stamp, s }; };
    const B = mk(p.before || {}, false), A = mk(p.after || {}, true);
    const svgNS = "http://www.w3.org/2000/svg"; const sv = document.createElementNS(svgNS, "svg"); sv.setAttribute("viewBox", `0 0 ${W} ${H}`); sv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;z-index:3;overflow:visible";
    const x0 = vert ? W * .72 : W * .40, y0 = vert ? H * .36 : H * .40, x1 = vert ? W * .82 : W * .5, y1 = vert ? H * .47 : H * .40;
    const path = document.createElementNS(svgNS, "path"); path.setAttribute("d", vert ? `M${x0},${y0} C${W * .95},${H * .38} ${W * .95},${H * .44} ${x1},${y1}` : `M${x0},${y0} C${W * .44},${H * .30} ${W * .48},${H * .32} ${x1},${y1}`);
    path.setAttribute("fill", "none"); path.setAttribute("stroke", "var(--accent2)"); path.setAttribute("stroke-width", U * 1.1); path.setAttribute("stroke-linecap", "round");
    const head = document.createElementNS(svgNS, "path"); head.setAttribute("d", `M${x1 - U * 3.2},${y1 - U * 3.5} L${x1},${y1} L${x1 + U * 2.6},${y1 - U * 4}`); head.setAttribute("fill", "none"); head.setAttribute("stroke", "var(--accent2)"); head.setAttribute("stroke-width", U * 1.1); head.setAttribute("stroke-linecap", "round"); head.setAttribute("stroke-linejoin", "round");
    sv.appendChild(path); sv.appendChild(head); root.appendChild(sv);
    let L = 1000; try { L = path.getTotalLength() || 1000; } catch (e) { /* not laid out */ }
    path.style.strokeDasharray = L; const src = sourceLine(root, p);
    const at = (p.at != null ? p.at : sc.start + 1.4) - sc.start; const sa = A.s.stat_at != null ? A.s.stat_at - sc.start : at + .5; const st = A.s.stamp && A.s.stamp.at != null ? A.s.stamp.at - sc.start : at + 1.6;
    return { update(lt, dur) {
      headerUpdate(h, lt);
      const kb = E.out(prog(lt, .1, .6)); set(B.f, clamp(kb * 2), `translateX(${(1 - kb) * -200}px) rotate(${lerp(-8, -3, kb)}deg)`); B.im.style.transform = `scale(${1 + lt / Math.max(dur, 1) * .06})`;
      const ka = prog(lt, at - .55, .55); path.style.strokeDashoffset = L * (1 - E.inout(ka)); head.style.opacity = ka >= .98 ? 1 : 0;
      const kr = prog(lt, at, .5); set(A.f, clamp(kr * 3), `scale(${lerp(.85, 1, E.back(kr))}) rotate(${lerp(4, 1.5, E.out(kr))}deg)`); A.f.style.clipPath = `inset(-20% ${(1 - E.out(kr)) * 100}% -20% -5%)`; A.im.style.transform = `scale(${1.12 - E.out(prog(lt, at, dur - at)) * .1})`;
      if (A.stat) { const k = prog(lt, sa, 1.1); A.stat.textContent = (A.s.stat.prefix || "") + fmtNum(lerp(0, A.s.stat.value, E.out(k)), A.s.stat.decimals) + (A.s.stat.unit || ""); set(A.stat, clamp(k * 4)); }
      if (A.stamp) { const k = prog(lt, st, .3); set(A.stamp, clamp(k * 4), `scale(${lerp(2.4, 1, E.slam(k))}) rotate(-4deg)`); }
      set(src, E.out(prog(lt, at, .5)));
    } };
  };


  // LETTERBOX: clip 16:9 nằm giữa khung dọc (kiểu video đạo lý), dải trên/dưới đen cho tiêu đề, từ khoá, phụ đề
  M.letterbox = (root, p, sc) => {
    const vh = Math.round(W * 9 / 16), top = Math.round((H - vh) / 2 + (p.offset_y || 0) * H);
    const band = el("div", null, null, root); band.style.cssText = `position:absolute;left:0;right:0;top:${top}px;height:${vh}px;overflow:hidden;background:#000`;
    let v = null;
    if (TL.overlay_mode) { band.style.background = "transparent"; }
    else {
      v = el("video", null, null, band); v.src = p.video; v.muted = true; v.preload = "auto";
      v.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover";
      v._d = sc; v._rate = p.rate || 1; v._off = p.clip_start || 0; VIDS.push(v);
    }
    const shade = el("div", null, null, band); shade.style.cssText = "position:absolute;inset:0;box-shadow:inset 0 0 calc(var(--u)*10) rgba(0,0,0,.85)";
    if (p.warm) { const w = el("div", null, null, band); w.style.cssText = "position:absolute;inset:0;mix-blend-mode:soft-light;background:radial-gradient(60% 70% at 70% 30%,rgba(255,190,90,.75),transparent 70%)"; w._warm = 1; band._warm = w; }
    return { update(lt, dur) {
      const k = lt / Math.max(dur, 1);
      if (v) v.style.transform = `scale(${lerp(p.zoom_from || 1.02, p.zoom_to || 1.09, k)})`;
      if (band._warm) band._warm.style.opacity = E.out(prog(lt, (p.warm_at != null ? p.warm_at - sc.start : dur * .45), 1.4));
    } };
  };

  // CTA comment bubble
  M.cta = (root, p, sc) => {
    const c = el("div", "center", null, root);
    const hl = p.title ? el("div", "headline", mark(p.title), c) : null; if (hl) hl.style.fontSize = "calc(var(--u)*7)";
    const b = el("div", null, null, c); b.style.cssText = "margin-top:calc(var(--u)*4);background:#2d7ff9;border-radius:calc(var(--u)*3);padding:calc(var(--u)*3) calc(var(--u)*6);position:relative;box-shadow:0 calc(var(--u)*1) calc(var(--u)*4) rgba(0,0,0,.5)";
    el("div", "headline", esc(p.text || "COMMENT"), b).style.fontSize = "calc(var(--u)*6)";
    const kwd = el("div", "headline", "“" + esc(p.keyword || "") + "”", b); kwd.style.fontSize = "calc(var(--u)*7)";
    const tail = el("div", null, null, b); tail.style.cssText = "position:absolute;left:50%;bottom:calc(var(--u)*-2.5);width:calc(var(--u)*5);height:calc(var(--u)*5);background:#2d7ff9;transform:translateX(-50%) rotate(45deg)";
    return { update(lt) { set(hl, E.out(prog(lt, 0, .4))); const k = prog(lt, .3, .5); set(b, clamp(k * 3), `scale(${lerp(.3, 1, E.elastic(k))})`); } };
  };

  // ---------------- MAP (bay từ vũ trụ → vệ tinh → ghim → tuyến) ----------------
  const TILE = 256;
  const wx = (lon, z) => (lon + 180) / 360 * TILE * Math.pow(2, z);
  const wy = (lat, z) => { const s = Math.sin(lat * Math.PI / 180); return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * TILE * Math.pow(2, z); };
  let GLOBE = null; // {w,h,data}
  M.map = (root, p, sc) => {
    const cv = el("canvas", null, null, root); cv.width = W; cv.height = H; const ctx = cv.getContext("2d");
    const gcv = document.createElement("canvas"); const gs = .5; gcv.width = Math.round(W * gs); gcv.height = Math.round(H * gs); const gctx = gcv.getContext("2d"); const gimg = gctx.createImageData(gcv.width, gcv.height);
    const shade = el("div", null, null, root); shade.style.cssText = "position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.05) 35%,rgba(0,0,0,.05) 60%,rgba(0,0,0,.75) 100%)";
    const h = header(root, p);
    const levels = (p.levels || []).map(L => ({ ...L, im: IMGS[L.file] })).sort((a, b) => a.z - b.z);
    levels.forEach((L, i) => { if (i && L.im && L.im.naturalWidth) L.im = feather(L.file); }); // mép mờ: các mức zoom hoà vào nhau, không lộ khung
    const stops = (p.stops || []);
    const pins = stops.filter(s => s.label || s.pin !== false).map(s => { const d = el("div", "pin", null, root); el("div", "dot", null, d); if (s.label) el("div", "lab", esc(s.label), d); return { d, s }; });
    const routes = (p.routes || []).map(r => { let lab; if (V2) lab = el("div", "rchip", "", root); else { lab = el("div", "chip card", "", root); lab.style.cssText += ";position:absolute;font-size:calc(var(--u)*3.4);font-style:normal;white-space:nowrap"; } return { r, lab }; });
    const marks = (p.marks || []).map(m => { const d = el("div", "mark", esc(m.label), root); d.style.background = m.color || "#2563eb"; return { d, m }; });
    const borders = (p.borders || []).filter(b => GEO[b.iso]); const split = p.split && GEO[p.split.iso] ? p.split : null;
    const space = p.from_space ? (p.space_dur || 2.8) : 0;
    const stars = (() => { const R = rnd(7), a = []; for (let i = 0; i < 260; i++) a.push([R() * W, R() * H, R() * 1.6 + .3, R()]); return a; })();
    const clouds = (() => { const R = rnd(11), a = []; for (let i = 0; i < 26; i++) a.push([R() * 2 - 1, R() * 2 - 1, R() * .5 + .25]); return a; })();
    function camAt(lt) { // returns {lat,lon,z}
      const t = sc.start + lt; let cur = stops[0] || { lat: 0, lon: 0, zoom: 4 };
      let st = { lat: cur.lat, lon: cur.lon, z: cur.zoom || 12 };
      for (let i = 1; i < stops.length; i++) { const s = stops[i]; if (s.nomove) continue; const a = s.at != null ? s.at : sc.start + i * 2; const d = s.move || 1.8;
        if (t >= a) { const k = E.inout(prog(t, a, d)); const z0 = st.z, z1 = s.zoom || st.z;
          const zmid = Math.min(z0, z1) - (s.arc != null ? s.arc : 1.2) * Math.sin(Math.PI * k); // fly out a bit between stops
          const p0 = [wx(st.lon, 0), wy(st.lat, 0)], p1 = [wx(s.lon, 0), wy(s.lat, 0)];
          const X = lerp(p0[0], p1[0], k), Y = lerp(p0[1], p1[1], k);
          const lon = X / TILE * 360 - 180; const n = Math.PI - 2 * Math.PI * Y / TILE; const lat = 180 / Math.PI * Math.atan(.5 * (Math.exp(n) - Math.exp(-n)));
          st = { lat, lon, z: lerp(z0, z1, k) - (s.arc != null ? s.arc : 1.0) * Math.sin(Math.PI * k) }; } }
      if (space && lt < space + 1.6) { const k = E.inout(prog(lt, space * .55, space * .45 + 1.6)); st.z = lerp(3.2, st.z, k); }
      st.z += (p.drift != null ? p.drift : .08) * lt; // slow push-in
      return st;
    }
    function proj(lat, lon, cam) { const z = cam.z; return [W / 2 + wx(lon, z) - wx(cam.lon, z), H / 2 + wy(lat, z) - wy(cam.lat, z)]; }
    function drawFlat(cam, alpha) {
      ctx.globalAlpha = alpha;
      for (const L of levels) { if (!L.im || !L.im.complete) continue;
        const s = Math.pow(2, cam.z - L.z); if (s < .05) continue;
        const fade = L === levels[0] ? 1 : clamp((cam.z - (L.z - 1.6)) / 1.0);
        if (fade <= 0) continue;
        const cx = W / 2 + (wx(L.lon, cam.z) - wx(cam.lon, cam.z)), cy = H / 2 + (wy(L.lat, cam.z) - wy(cam.lat, cam.z));
        const w = L.im.naturalWidth * s, hh = L.im.naturalHeight * s;
        ctx.globalAlpha = alpha * fade; ctx.drawImage(L.im, cx - w / 2, cy - hh / 2, w, hh); }
      ctx.globalAlpha = 1;
    }
    function drawGlobe(lt, cam) { // orthographic globe from mercator world texture
      if (!GLOBE) return;
      const k = prog(lt, 0, space); const R = lerp(.32, 2.6, Math.pow(E.inout(k), 1.6)) * Math.min(W, H) * gs;
      const lon0 = lerp(cam.lon - 70, cam.lon, E.out(k)) * Math.PI / 180, lat0 = lerp(cam.lat - 20, cam.lat, E.out(k)) * Math.PI / 180;
      const cx = gcv.width / 2, cy = gcv.height / 2, d = gimg.data, G = GLOBE, gw = G.w, gh = G.h;
      const sl0 = Math.sin(lat0), cl0 = Math.cos(lat0);
      for (let y = 0; y < gcv.height; y++) for (let x = 0; x < gcv.width; x++) {
        const i = (y * gcv.width + x) * 4; const px = (x - cx) / R, py = (cy - y) / R; const rr = px * px + py * py;
        if (rr > 1) { d[i + 3] = 0; continue; }
        const pz = Math.sqrt(1 - rr); const lat = Math.asin(pz * sl0 + py * cl0); const lon = lon0 + Math.atan2(px, pz * cl0 - py * sl0);
        let u = ((lon / Math.PI + 1) / 2) % 1; if (u < 0) u += 1; const sy = Math.sin(clamp(lat, -1.48, 1.48)); const v = .5 - Math.log((1 + sy) / (1 - sy)) / (4 * Math.PI);
        const j = ((Math.floor(clamp(v) * (gh - 1)) * gw) + Math.floor(u * (gw - 1))) * 4; const lit = .55 + .45 * pz;
        d[i] = G.data[j] * lit; d[i + 1] = G.data[j + 1] * lit; d[i + 2] = G.data[j + 2] * lit; d[i + 3] = 255; }
      gctx.putImageData(gimg, 0, 0);
      ctx.save(); ctx.shadowColor = "rgba(90,160,255,.7)"; ctx.shadowBlur = 40; ctx.drawImage(gcv, 0, 0, W, H); ctx.restore();
      return R / gs;
    }
    return { update(lt, dur) {
      const cam = camAt(lt);
      ctx.fillStyle = "#03050a"; ctx.fillRect(0, 0, W, H);
      let flatA = 1;
      if (space && lt < space + .2) {
        const tw = 1 - prog(lt, space * .5, space * .4);
        for (const [x, y, r, a] of stars) { ctx.globalAlpha = tw * (.4 + .6 * a); ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
        ctx.globalAlpha = 1; drawGlobe(lt, cam);
        flatA = clamp((lt - space * .78) / (space * .22));
      }
      if (flatA > 0) drawFlat(cam, flatA);
      if (flatA > 0 && (borders.length || split)) { // lớp đồ hoạ phủ lên ảnh vệ tinh: viền phát sáng, tô nước được nhắc, tách mảng đất
        const geoPath = (rings, dx = 0, dy = 0) => { ctx.beginPath(); for (const r of rings) r.forEach(([lo, la], i) => { const [x, y] = proj(la, lo, cam); i ? ctx.lineTo(x + dx, y + dy) : ctx.moveTo(x + dx, y + dy); }); };
        const glow = (col, blur, lw, a) => { ctx.save(); ctx.shadowColor = col; ctx.shadowBlur = blur; ctx.strokeStyle = col; ctx.globalAlpha = a; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); ctx.restore(); };
        for (const b of borders) { if (split && b.iso === split.iso) continue; const k = prog(lt, (b.at != null ? b.at : sc.start) - sc.start, .8) * flatA; if (k <= 0) continue; geoPath(GEO[b.iso]);
          const col = b.color || '#6EA8FF'; ctx.save(); ctx.globalAlpha = k * (b.fill != null ? b.fill : .16); ctx.fillStyle = col; ctx.fill(); ctx.restore(); glow(col, U * 2, U * (b.width || .35), k); }
        if (split) { const b0 = borders.find(b => b.iso === split.iso) || {}; const col = b0.color || '#FF4D5A';
          const hl = prog(lt, (b0.at != null ? b0.at : sc.start) - sc.start, .4) * flatA, cut = E.out(prog(lt, (split.at != null ? split.at : sc.start + 2) - sc.start, .8));
          const dx = cut * (split.dx != null ? split.dx : 3) * U, dy = cut * (split.dy != null ? split.dy : 5) * U;
          if (cut > 0) { geoPath(GEO[split.iso]); ctx.fillStyle = `rgba(4,12,24,${.85 * cut})`; ctx.fill(); glow('#FACC15', 0, U * .2, .6 * cut); }
          ctx.save(); geoPath(GEO[split.iso], dx, dy); ctx.clip(); ctx.translate(dx, dy); drawFlat(cam, 1); ctx.restore();
          geoPath(GEO[split.iso], dx, dy); ctx.save(); ctx.globalAlpha = .16 * hl; ctx.fillStyle = col; ctx.fill(); ctx.restore(); glow(col, U * 2.4, U * .42, hl);
          if (cut > 0 && split.line) { const [x1, y1] = proj(split.line[0][0], split.line[0][1], cam), [x2, y2] = proj(split.line[1][0], split.line[1][1], cam);
            ctx.save(); ctx.setLineDash([U * 2.2, U * 1.3]); ctx.lineDashOffset = -lt * 70; ctx.strokeStyle = '#FACC15'; ctx.lineWidth = U * .65; ctx.shadowColor = '#FACC15'; ctx.shadowBlur = U * 2;
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(lerp(x1, x2, cut), lerp(y1, y2, cut)); ctx.stroke(); ctx.restore(); }
          split._d = [dx, dy]; } }
      if (space) { const ck = prog(lt, space * .62, 1.1); if (ck > 0 && ck < 1) { const a = Math.sin(Math.PI * ck);
        for (const [x, y, s] of clouds) { const sx = W / 2 + x * W * (0.4 + ck * 1.6), sy = H / 2 + y * H * (0.4 + ck * 1.6), r = s * W * (0.6 + ck * 1.8);
          const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, r); g.addColorStop(0, `rgba(255,255,255,${.85 * a})`); g.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = g; ctx.fillRect(sx - r, sy - r, 2 * r, 2 * r); } } }
      // routes
      for (const { r, lab } of routes) { const a = r.at != null ? r.at - sc.start : 1; const k = E.inout(prog(lt, a, r.dur || 1.6)); if (k <= 0) { lab.style.opacity = 0; continue; }
        const pts = r.points.map(q => proj(q[0], q[1], cam)); let tot = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); tot += l; }
        let rem = tot * k; const rc = r.color || (V2 ? "#FACC15" : "#F0784A"); ctx.lineWidth = r.width || U * (V2 ? 1.3 : 1.1); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.strokeStyle = rc; ctx.shadowColor = rc; ctx.shadowBlur = V2 ? 26 : 18;
        if (r.dash) ctx.setLineDash([U * 2.4, U * 1.4]); else ctx.setLineDash([]);
        ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); let end = pts[0];
        for (let i = 1; i < pts.length && rem > 0; i++) { const l = seg[i - 1]; const f = Math.min(1, rem / l); end = [lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)]; ctx.lineTo(end[0], end[1]); rem -= l; }
        ctx.stroke(); ctx.shadowBlur = 0; ctx.setLineDash([]);
        if (V2) { ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(end[0], end[1], U * 1.3, 0, 7); ctx.fill(); ctx.strokeStyle = "rgba(250,204,21,.55)"; ctx.lineWidth = U * .9; ctx.beginPath(); ctx.arc(end[0], end[1], U * (2.4 + .5 * Math.sin(lt * 9)), 0, 7); ctx.stroke();
          const v2 = r.value != null ? fmtNum(lerp(0, r.value, k), r.decimals) : ""; lab.innerHTML = `<b>${esc((r.prefix || "") + v2)}</b><span>${esc(r.unit || "")}${r.label ? " · " + esc(r.label) : ""}</span>`;
          lab.style.opacity = clamp(k * 3); const lw = lab.offsetWidth || 0; const mid = pts[Math.floor(pts.length * (r.chip_at != null ? r.chip_at : .8))] || end; let lx = mid[0] - lw - U * 4; if (lx < U * 3) lx = mid[0] + U * 4;
          lab.style.left = Math.min(W - lw - U * 3, lx) + "px"; lab.style.top = (mid[1] - U * 7) + "px"; continue; }
        const v = r.value != null ? fmtNum(lerp(0, r.value, k), r.decimals) : ""; lab.innerHTML = (r.icon ? "" : "") + mark((r.prefix || "") + v + (r.unit ? " " + r.unit : "")) + (r.label ? `<span style="font-weight:600;opacity:.85;margin-left:.5em">${esc(r.label)}</span>` : "");
        lab.style.opacity = clamp(k * 3); const lw = lab.offsetWidth || 0; let lx = end[0] + U * 2; if (lx + lw > W - U * 3) lx = end[0] - lw - U * 2; lab.style.left = Math.max(U * 3, lx) + "px"; lab.style.top = (end[1] + U * 2) + "px"; lab.style.borderColor = r.color || ""; }
      for (const { d, m } of marks) { let [x, y] = proj(m.lat, m.lon, cam); if (split && m.iso === split.iso && split._d) { x += split._d[0]; y += split._d[1]; }
        const k = E.back(prog(lt, (m.at != null ? m.at : sc.start + .5) - sc.start, .4)); d.style.left = (x + (m.dx || 0) * U) + "px"; d.style.top = (y + (m.dy || 0) * U) + "px";
        d.style.opacity = clamp(k * 2) * flatA * (1 - prog(lt, (m.at != null ? m.at : sc.start) - sc.start + (m.hold || 99), .3)); d.style.transform = `translate(-50%,-50%) scale(${lerp(.4, 1, k)})`; }
      for (const { d, s } of pins) { const a = (s.pin_at != null ? s.pin_at : (s.at != null ? s.at + (s.nomove ? 0 : (s.move || 1.8) * .8) : sc.start + space + .3)) - sc.start; const k = prog(lt, a, .45);
        const [x, y] = proj(s.lat, s.lon, cam); d.style.left = x + "px"; d.style.top = y + "px"; d.style.opacity = clamp(k * 3); d.style.transform = `translate(-50%,-100%) translateY(${(1 - E.back(k)) * -60}px)`; }
      headerUpdate(h, lt - (p.header_at != null ? p.header_at - sc.start : (space ? space * .8 : 0)));
      shade.style.opacity = flatA;
    } };
  };

  // ================= MODULE v2 (graphic mới: thanh đua, biểu đồ, diện tích, gạch X, trích lời, câu treo) =================
  const PORT = () => H > W;
  const flagImg = (f, size) => f ? `<img src="${f}" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:3px solid rgba(255,255,255,.85);box-shadow:0 .2em .6em rgba(0,0,0,.5)">` : "";
  // THANH ĐUA: so 2–4 giá trị cùng đơn vị (thu nhập, dân số, tốc độ…) — thanh chạy + số đếm đúng lúc đọc
  M.race = (root, p, sc) => {
    const h = header(root, p); const items = p.items || []; const max = p.max || Math.max(...items.map(i => i.value)) * 1.05;
    const top = (p.top != null ? p.top : PORT() ? 30 : 34) * H / 100, gap = (PORT() ? 15 : 17) * U, x0 = 6 * U, bw = W - 12 * U;
    const rows = items.map((it, i) => {
      const g = el("div", null, null, root); g.style.cssText = `position:absolute;left:${x0}px;top:${top + i * gap}px;width:${bw}px;height:${gap}px`;
      const lab = el("div", null, `${flagImg(it.flag, 5.4 * U)}${it.icon ? icon(it.icon).outerHTML : ""}<span>${mark(it.label || "")}</span>`, g);
      lab.style.cssText = `position:absolute;left:0;top:0;display:flex;align-items:center;gap:.6em;font-weight:800;font-size:${PORT() ? 3.8 : 3.6}em;letter-spacing:.05em;text-transform:uppercase;font-size:calc(var(--u)*${PORT() ? 3.6 : 3.4})`;
      const tr = el("div", null, null, g); tr.style.cssText = `position:absolute;left:0;top:${6.6 * U}px;width:100%;height:${6.4 * U}px;border-radius:${1.4 * U}px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12)`;
      const col = it.color || ["#EF3340", "#3C82F6", "#22C55E", "#F59E0B"][i % 4];
      const fill = el("div", null, null, tr); fill.style.cssText = `position:absolute;left:0;top:0;bottom:0;width:0;border-radius:${1.4 * U}px;background:linear-gradient(90deg,${col},color-mix(in srgb,${col} 70%,#fff));box-shadow:0 0 ${4 * U}px color-mix(in srgb,${col} 55%,transparent)`;
      const num = el("div", "num2", "", g); num.style.cssText = `position:absolute;right:0;top:${-1.6 * U}px;font-size:calc(var(--u)*${PORT() ? 8.5 : 9.5});text-shadow:0 .1em .4em rgba(0,0,0,.6)`;
      return { it, lab, fill, num, at: (it.at != null ? it.at : sc.start + .4 + i * 1.2) - sc.start };
    });
    const badge = p.badge ? el("div", "pill2", mark(p.badge.text || p.badge), root) : null;
    if (badge) badge.style.cssText += `;position:absolute;left:${x0}px;top:${top + items.length * gap + 1 * U}px;font-size:calc(var(--u)*3.6)`;
    sourceLine(root, p);
    return { update(lt) { headerUpdate(h, lt);
      for (const r of rows) { const a = E.out(prog(lt, r.at - .9, .5)); set(r.lab, a, `translateX(${(1 - a) * -40}px)`);
        const k = E.inout(prog(lt, r.at - .2, p.dur || 1.5)); r.fill.style.width = (k * r.it.value / max * 100) + "%";
        r.num.textContent = (r.it.prefix || "") + fmtNum(k >= 1 ? r.it.value : r.it.value * k, r.it.decimals || 0) + (r.it.unit || ""); set(r.num, clamp(k * 4)); }
      if (badge) { const b = E.back(prog(lt, (p.badge.at != null ? p.badge.at - sc.start : rows.length ? rows[rows.length - 1].at + 1.6 : 1), .4)); set(badge, clamp(b * 2), `scale(${lerp(.6, 1, b)})`); }
    } };
  };
  // BIỂU ĐỒ ĐƯỜNG: chuỗi số liệu thật theo năm, tự vẽ dần; nhãn chỉ hiện ĐÚNG mốc có trong dữ liệu
  M.line_chart = (root, p, sc) => {
    const h = header(root, p);
    const cv = el("canvas", null, null, root); cv.width = W; cv.height = H; cv.style.cssText = "position:absolute;inset:0"; const g = cv.getContext("2d");
    const S = p.series || {}; const xs = Object.keys(S).map(Number).sort((a, b) => a - b); const x0v = xs[0], x1v = xs[xs.length - 1];
    const vmax = p.y_max || Math.max(...xs.map(x => S[x])) * 1.08;
    const X0 = (PORT() ? 14 : 15) * U, X1 = W - (PORT() ? 10 : 13) * U, Y0 = H * (PORT() ? .7 : .78), Y1 = H * (PORT() ? .36 : .33);
    const xp = x => X0 + (x - x0v) / (x1v - x0v) * (X1 - X0), yp = v => Y0 - v / vmax * (Y0 - Y1);
    const val = x => { for (let i = 1; i < xs.length; i++) if (x <= xs[i]) return lerp(S[xs[i - 1]], S[xs[i]], (x - xs[i - 1]) / (xs[i] - xs[i - 1])); return S[x1v]; };
    const pre = p.prefix || "", suf = p.unit || "", dec = p.decimals || 0;
    const lab = el("div", "pill2", "", root); lab.style.cssText += ";position:absolute;font-family:OSW;font-size:calc(var(--u)*4.6);white-space:nowrap";
    const lab0 = el("div", "num2", pre + fmtNum(S[x0v], dec) + suf, root); lab0.style.cssText += `;position:absolute;left:${xp(x0v)}px;top:${yp(S[x0v]) - 7 * U}px;font-size:calc(var(--u)*4.2);color:#fff`;
    const badge = p.badge ? el("div", "num2", mark(p.badge.text || p.badge), root) : null;
    if (badge) badge.style.cssText += `;position:absolute;left:${X0 + 3 * U}px;top:${PORT() ? H * .4 : H * .36}px;font-size:calc(var(--u)*${PORT() ? 20 : 26});color:var(--accent2);text-shadow:0 0 .25em rgba(250,204,21,.45);transform-origin:0 50%`;
    sourceLine(root, p);
    const ticks = p.ticks || (() => { const n = 4, out = []; for (let i = 0; i <= n; i++) out.push(Math.round(lerp(x0v, x1v, i / n))); return out; })();
    const t0 = (p.at != null ? p.at - sc.start : .3), dd = p.dur || 2.8;
    return { update(lt) { headerUpdate(h, lt);
      g.clearRect(0, 0, W, H); g.font = `600 ${2.6 * U}px OSW`; g.textAlign = "right";
      for (let i = 0; i <= 4; i++) { const v = vmax * i / 4; g.strokeStyle = "rgba(255,255,255,.08)"; g.lineWidth = 2; g.beginPath(); g.moveTo(X0, yp(v)); g.lineTo(X1, yp(v)); g.stroke(); if (i) { g.fillStyle = "rgba(255,255,255,.42)"; g.fillText(pre + (v >= 1000 ? Math.round(v / 1000) + "K" : Math.round(v)) + (v >= 1000 ? "" : suf), X0 - 1.5 * U, yp(v) + U); } }
      g.textAlign = "center"; ticks.forEach(x => { g.fillStyle = "rgba(255,255,255,.5)"; g.fillText(x, xp(x), Y0 + 4.5 * U); });
      const k = E.inout(prog(lt, t0, dd)), xv = lerp(x0v, x1v, k);
      const path = () => { g.beginPath(); g.moveTo(xp(x0v), yp(S[x0v])); for (let x = x0v; x <= xv; x += (x1v - x0v) / 240) g.lineTo(xp(x), yp(val(x))); g.lineTo(xp(xv), yp(val(xv))); };
      path(); g.lineTo(xp(xv), Y0); g.lineTo(xp(x0v), Y0); g.closePath(); const ag = g.createLinearGradient(0, Y1, 0, Y0); ag.addColorStop(0, "rgba(250,204,21,.38)"); ag.addColorStop(1, "rgba(250,204,21,0)"); g.fillStyle = ag; g.fill();
      path(); g.strokeStyle = p.color || "#FACC15"; g.lineWidth = .75 * U; g.lineJoin = "round"; g.shadowColor = p.color || "#FACC15"; g.shadowBlur = 2.4 * U; g.stroke(); g.shadowBlur = 0;
      const hx = xp(xv), hy = yp(val(xv)); g.fillStyle = "#fff"; g.beginPath(); g.arc(hx, hy, 1.3 * U, 0, 7); g.fill(); g.strokeStyle = "rgba(250,204,21,.5)"; g.lineWidth = .9 * U; g.beginPath(); g.arc(hx, hy, (2.4 + .5 * Math.sin(lt * 8)) * U, 0, 7); g.stroke();
      const ly = xs.filter(x => x <= xv + 1e-6).pop(); lab.textContent = pre + fmtNum(S[ly], dec) + suf + "  ·  " + ly;
      lab.style.left = Math.max(U * 6, Math.min(hx - lab.offsetWidth / 2, W - lab.offsetWidth - 7 * U)) + "px"; lab.style.top = (hy - 10 * U) + "px"; set(lab, clamp((lt - t0) * 4));
      set(lab0, E.out(prog(lt, t0 - .2, .3)));
      if (badge) { const b = prog(lt, p.badge.at != null ? p.badge.at - sc.start : t0 + dd * .8, .35); set(badge, clamp(b * 3), `scale(${lerp(1.6, 1, E.out(b))})`); badge.style.filter = `blur(${(1 - clamp(b * 1.5)) * 10}px)`; }
    } };
  };
  // SO DIỆN TÍCH / QUY MÔ: cái nhỏ chiếm bao nhiêu phần cái lớn (≈ 1/5…)
  M.area_compare = (root, p, sc) => {
    const h = header(root, p); const sm = p.small || {}, bg = p.big || {}; const ratio = sm.value / bg.value; const parts = p.parts || Math.max(2, Math.round(1 / ratio));
    const L = el("div", null, `<div class="kicker">${mark(sm.kicker || sm.label || "")}</div><div class="num2" style="font-size:calc(var(--u)*${PORT() ? 18 : 21});color:#fff;margin-top:.35em"><span style="display:inline-block;line-height:.95">0</span><span style="font-size:.42em;color:#aab3c4"> ${esc(sm.unit || "")}</span></div>${sm.note ? `<div style="font-weight:700;font-size:calc(var(--u)*3.2);color:#aab3c4;margin-top:.9em">${mark(sm.note)}</div>` : ""}`, root);
    L.style.cssText = PORT() ? `position:absolute;left:${6 * U}px;top:${H * .15}px` : `position:absolute;left:${6 * U}px;top:${H * .3}px`;
    const nEl = L.children[1].firstChild; const side = PORT() ? W * .78 : H * .56;
    const box = el("div", null, null, root); box.style.cssText = PORT() ? `position:absolute;left:${(W - side) / 2}px;top:${H * .4}px;width:${side}px;height:${side * .55}px` : `position:absolute;left:${W * .56}px;top:${H * .22}px;width:${side}px;height:${side}px`;
    box.style.cssText += `;border-radius:${2 * U}px;border:${.4 * U}px solid rgba(255,255,255,.85);background:rgba(255,255,255,.03)`;
    const bl = el("div", null, `${mark(bg.label || "")}${bg.value ? " · " + fmtNum(bg.value, bg.decimals || 0) + " " + esc(bg.unit || "") : ""}`, box); bl.style.cssText = `position:absolute;left:0;right:0;top:${-6 * U}px;text-align:center;font-weight:800;font-size:calc(var(--u)*3.2);letter-spacing:.06em;text-transform:uppercase;white-space:nowrap`;
    const fill = el("div", null, `<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-90deg);white-space:nowrap;font-weight:800;font-size:calc(var(--u)*3);letter-spacing:.12em;text-transform:uppercase">${esc(sm.label || "")}</div>`, box);
    fill.style.cssText = `position:absolute;left:0;top:0;bottom:0;width:0;background:linear-gradient(180deg,${sm.color || "#ff4d5a"},color-mix(in srgb,${sm.color || "#ff4d5a"} 70%,#000));border-radius:${1.6 * U}px 0 0 ${1.6 * U}px;box-shadow:0 0 ${5 * U}px rgba(239,51,64,.55);overflow:hidden`;
    const divs = []; for (let i = 1; i < parts; i++) { const d = el("div", null, null, box); d.style.cssText = `position:absolute;left:${i / parts * 100}%;top:0;bottom:0;border-left:${.3 * U}px dashed rgba(255,255,255,.45);opacity:0`; divs.push(d); }
    const frac = el("div", "pill2", mark(p.frac || `≈ 1/${parts}`), root); frac.style.cssText += `;position:absolute;font-size:calc(var(--u)*5);white-space:nowrap;transform-origin:50% 50%`;
    sourceLine(root, p);
    const tc = (sm.at != null ? sm.at : sc.start + .8) - sc.start, tf = (p.at != null ? p.at : sc.start + 2.6) - sc.start;
    return { update(lt) { headerUpdate(h, lt);
      const a = E.out(prog(lt, .1, .5)); set(L, a, `translateX(${(1 - a) * -50}px)`); nEl.textContent = fmtNum(sm.value * E.out(prog(lt, tc, 1.3)), sm.decimals || 0);
      const b = E.out(prog(lt, .4, .6)); set(box, b, `scale(${lerp(.85, 1, b)})`);
      fill.style.width = (E.inout(prog(lt, tf, .9)) * ratio * 100) + "%"; divs.forEach((d, i) => d.style.opacity = E.out(prog(lt, tf + .6 + i * .1, .3)));
      const r = box.getBoundingClientRect(); frac.style.left = Math.min(r.right - frac.offsetWidth * .55, W - frac.offsetWidth - 7 * U) + "px"; frac.style.top = (PORT() ? r.bottom + 1.5 * U : r.bottom - frac.offsetHeight * .5) + "px";
      const f = E.back(prog(lt, tf + 1.0, .4)); set(frac, clamp(f * 2), `scale(${lerp(.4, 1, f)}) rotate(-6deg)`);
    } };
  };
  // THẺ BỊ GẠCH: "không có A, không có B…" — mỗi thẻ hiện + gạch X đúng lúc đọc
  M.strike_cards = (root, p, sc) => {
    const h = header(root, p); const items = p.items || []; const n = items.length;
    const cw = PORT() ? W * .78 : Math.min(40 * U, (W - 16 * U) / n - 4 * U), ch = PORT() ? Math.min(16 * U, H * .5 / n - 3 * U) : 44 * U;
    const cards = items.map((it, i) => {
      const x = PORT() ? (W - cw) / 2 : (W - (cw * n + 5 * U * (n - 1))) / 2 + i * (cw + 5 * U), y = PORT() ? H * .3 + i * (ch + 3.5 * U) : H * .34;
      const col = it.color || ["#f59e0b", "#a78bfa", "#38bdf8", "#22c55e"][i % 4];
      const c = el("div", "card2", `<div style="position:absolute;inset:0;display:flex;${PORT() ? "flex-direction:row;gap:calc(var(--u)*4);padding-left:calc(var(--u)*4)" : "flex-direction:column;gap:calc(var(--u)*3);justify-content:center"};align-items:center">
        <div class="ibox" style="width:${PORT() ? 10 : 17}em;height:${PORT() ? 10 : 17}em;font-size:calc(var(--u)*1);border-radius:3.6em;display:grid;place-items:center;background:color-mix(in srgb,${col} 18%,transparent);border:2px solid color-mix(in srgb,${col} 55%,transparent)"></div>
        <div style="font-weight:800;font-size:calc(var(--u)*${PORT() ? 4.4 : 4.6});letter-spacing:.05em;text-transform:uppercase">${mark(it.text || "")}</div></div>`, root);
      c.style.cssText += `;position:absolute;left:${x}px;top:${y}px;width:${cw}px;height:${ch}px`;
      const ib = c.querySelector(".ibox"); if (it.icon) { const ic = icon(it.icon); ic.style.width = ic.style.height = PORT() ? "6em" : "10em"; ic.style.background = col; ib.appendChild(ic); }
      const ibR = { x: PORT() ? 4 * U : (cw - 17 * U) / 2, y: PORT() ? (ch - 10 * U) / 2 : (ch - 17 * U) / 2 - 4 * U, s: (PORT() ? 10 : 17) * U };
      const xx = el("div", null, `<svg width="${cw}" height="${ch}" style="position:absolute;left:0;top:0;overflow:visible"><path d="M${ibR.x - U} ${ibR.y - U} L${ibR.x + ibR.s + U} ${ibR.y + ibR.s + U}" stroke="#EF3340" stroke-width="${1.8 * U}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/><path d="M${ibR.x + ibR.s + U} ${ibR.y - U} L${ibR.x - U} ${ibR.y + ibR.s + U}" stroke="#EF3340" stroke-width="${1.8 * U}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`, c);
      const [l1, l2] = xx.querySelectorAll("path");
      const st = el("div", "pill2", esc(it.stamp || p.stamp || "KHÔNG CÓ"), c); st.style.cssText += `;position:absolute;right:${-1.5 * U}px;top:${-2 * U}px;background:#EF3340;color:#fff;font-size:calc(var(--u)*2.8);opacity:0`;
      if (it.note) { const nt = el("div", null, mark(it.note), c); nt.style.cssText = `position:absolute;left:${-3 * U}px;right:${-3 * U}px;top:${ch + 1.5 * U}px;text-align:center;font-weight:700;font-size:calc(var(--u)*2.3);color:#7dd3fc`; it._note = nt; }
      return { c, l1, l2, st, it, inner: c.firstChild, at: (it.at != null ? it.at : sc.start + .1 + i * 1.2) - sc.start, xat: (it.strike_at != null ? it.strike_at : (it.at != null ? it.at : sc.start + .1 + i * 1.2) + .8) - sc.start };
    });
    sourceLine(root, p);
    return { update(lt) { headerUpdate(h, lt);
      for (const k of cards) { const a = E.back(prog(lt, k.at, .45)); set(k.c, clamp(a * 2), `translateY(${(1 - a) * 8 * U}px)`);
        const x = prog(lt, k.xat, .35); k.l1.style.strokeDashoffset = 1 - E.out(clamp(x * 2)); k.l2.style.strokeDashoffset = 1 - E.out(clamp(x * 2 - 1));
        k.inner.style.filter = `grayscale(${x}) brightness(${1 - x * .4})`; const s = E.back(prog(lt, k.xat + .3, .3)); set(k.st, clamp(s * 2), `rotate(8deg) scale(${lerp(1.8, 1, s)})`);
        if (k.it._note) set(k.it._note, E.out(prog(lt, k.xat + .5, .4))); }
    } };
  };
  // TRÍCH LỜI trên nền ảnh/tranh (bg_photo): ngoặc lớn, câu trích hiện từng dòng, người nói + dịp nói
  M.quote = (root, p, sc) => {
    const sh = el("div", null, null, root); sh.style.cssText = `position:absolute;inset:0;background:${PORT() ? "linear-gradient(0deg,rgba(5,8,15,.92) 0%,rgba(5,8,15,.55) 55%,transparent 80%)" : "linear-gradient(90deg,rgba(5,8,15,.92) 0%,rgba(5,8,15,.6) 45%,transparent 75%)"}`;
    if (p.caption) { const c = el("div", null, esc(p.caption), root); c.style.cssText = `position:absolute;right:${5 * U}px;top:${(PORT() ? 9 : 8.5) * U}px;font-size:calc(var(--u)*1.9);font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.62);z-index:6`; }
    const q = el("div", null, `<div style="font-family:OSW;font-size:calc(var(--u)*20);line-height:.6;color:var(--accent2)">“</div>
      <div style="font-weight:800;font-size:calc(var(--u)*${p.size || (PORT() ? 6.6 : 6.4)});line-height:1.14;margin-top:.3em;max-width:${PORT() ? 88 : 46}vw">${mark(p.text || "")}</div>
      <div style="margin-top:1.1em;font-size:calc(var(--u)*2.7);font-weight:700;color:#aab3c4;letter-spacing:.03em">— ${mark(p.by || "")}</div>`, root);
    q.style.cssText = PORT() ? `position:absolute;left:${6 * U}px;right:${6 * U}px;top:${H * .5}px` : `position:absolute;left:${10 * U}px;top:${H * .22}px`;
    sourceLine(root, p);
    return { update(lt) { [...q.children].forEach((c, i) => { const a = E.out(prog(lt, .15 + i * .35, .5)); set(c, a, `translateY(${(1 - a) * 3 * U}px)`); c.style.filter = `blur(${(1 - a) * 8}px)`; }); } };
  };
  // CÂU TREO (vòng lặp mở): câu hỏi lớn + các thẻ khoá "BÍ QUYẾT #1…" để người xem ở lại
  M.open_loop = (root, p, sc) => {
    const q = el("div", "center", `<div class="headline" style="font-size:calc(var(--u)*${p.size || (PORT() ? 7 : 10.5)})">${mark(p.title || "")}</div>`, root); q.style.cssText += PORT() ? ";top:-28%" : ";top:-18%";
    const n = (p.cards || []).length || p.n || 3; const labs = p.cards || Array.from({ length: n }, (_, i) => `${p.card_label || "BÍ QUYẾT"} #${i + 1}`);
    const cw = PORT() ? W * .72 : Math.min(40 * U, (W - 20 * U) / n - 4 * U), chh = 13 * U;
    const locks = labs.map((t, i) => { const c = el("div", "card2", `<div style="height:100%;display:flex;align-items:center;justify-content:center;gap:.6em;font-weight:800;font-size:calc(var(--u)*3.6);letter-spacing:.05em"><span style="font-size:1.2em">🔒</span>${mark(t)}</div>`, root);
      c.style.cssText += `;position:absolute;width:${cw}px;height:${chh}px;` + (PORT() ? `left:${(W - cw) / 2}px;top:${H * .52 + i * (chh + 3 * U)}px` : `left:${(W - (cw * n + 4 * U * (n - 1))) / 2 + i * (cw + 4 * U)}px;top:${H * .6}px`); return c; });
    return { update(lt) { const a = E.out(prog(lt, .05, .45)); set(q, a, `scale(${lerp(1.15, 1, a)})`); q.style.filter = `blur(${(1 - a) * 10}px)`;
      locks.forEach((l, i) => { const b = E.back(prog(lt, (p.at != null ? p.at - sc.start : .5) + i * .18, .45)); set(l, clamp(b * 2), `translateY(${(1 - b) * 9 * U}px)`); }); } };
  };

  // MÀN HÌNH THẬT (quay màn hình / quay app): video trong khung cửa sổ, cắt–lia–zoom theo vùng nguồn, khoanh vàng đúng lúc,
  // ô gõ câu lệnh, đồng hồ bấm giờ thật. p.video, p.src:[w,h], p.crop:[x,y,w,h] → p.crop_to (lia/zoom dần), p.rate, p.clip_start,
  // p.title, p.rings:[{x,y,w,h,label,cue,hold}] (toạ độ ẢNH NGUỒN), p.prompt:{text,cue,speed}, p.timer:{to,unit,cue,dur,label}
  M.screen = (root, p, sc) => {
    const h = header(root, { kicker: p.kicker, title: p.headline, title_size: p.headline_size }); const [sw, sh] = p.src || [1920, 1080];
    const c0 = p.crop || [0, 0, sw, sh], c1 = p.crop_to || c0, asp = c0[2] / c0[3];
    const topY = (h ? (PORT() ? 24 : 21) : (PORT() ? 14 : 9)) * H / 100, maxW = W * (PORT() ? .9 : p.side ? .6 : .84), maxH = PORT() ? H * .52 : Math.min(H * .7, H * .76 - topY - 3.6 * U);
    let fw = maxW, fh = fw / asp; if (fh > maxH) { fh = maxH; fw = fh * asp; }
    const bar = p.frame === "none" ? 0 : 3.6 * U, fx = PORT() || !p.side ? (W - fw) / 2 : p.side === "right" ? W - fw - 5 * U : 5 * U, fy = topY + (maxH - fh) / 2 * (PORT() ? 0 : .35);
    const win = el("div", "qa-ev", null, root); win.style.cssText = `position:absolute;left:${fx}px;top:${fy}px;width:${fw}px;height:${fh + bar}px;border-radius:${1.4 * U}px;overflow:hidden;background:#0b0f19;border:2px solid rgba(255,255,255,.16);box-shadow:0 ${3 * U}px ${8 * U}px rgba(0,0,0,.65),0 0 ${5 * U}px rgba(250,204,21,.12)`;
    if (bar) { const b = el("div", null, `<i></i><i></i><i></i><span>${esc(p.title || "")}</span>`, win); b.style.cssText = `position:absolute;left:0;right:0;top:0;height:${bar}px;display:flex;align-items:center;gap:${.8 * U}px;padding:0 ${1.6 * U}px;background:#161c2b;border-bottom:1px solid rgba(255,255,255,.08);font-weight:700;font-size:calc(var(--u)*2);color:#94a3b8`;
      [...b.querySelectorAll("i")].forEach((d, i) => d.style.cssText = `width:${1.2 * U}px;height:${1.2 * U}px;border-radius:50%;background:${["#ef4444", "#f59e0b", "#22c55e"][i]}`); b.lastChild.style.marginLeft = `${1.2 * U}px`; }
    const vp = el("div", null, null, win); vp.style.cssText = `position:absolute;left:0;top:${bar}px;width:${fw}px;height:${fh}px;overflow:hidden`;
    const v = el("video", null, null, vp); v.src = p.video; v.muted = true; v.preload = "auto"; v.style.cssText = `position:absolute;left:0;top:0;width:${sw}px;height:${sh}px;max-width:none;transform-origin:0 0`;
    VIDS.push(v); v._d = sc; v._rate = p.rate || 1; v._off = p.clip_start || 0;
    const fz = (p.freeze || []).map(f => ({ ...f, hold: f.dur || 1.8, _fz: true }));
    if (fz.length) v._map = T => { const L = Math.max(0, T - sc.start); let stop = 0; for (const f of fz) { const a = (f.at != null ? f.at : sc.start + 1) - sc.start; if (L > a) stop += Math.min(L - a, f.hold); } return (p.clip_start || 0) + (L - stop) * (p.rate || 1); };
    const fzTag = fz.length ? el("div", "pill2", "❚❚ DỪNG HÌNH", root) : null; if (fzTag) fzTag.style.cssText += `;position:absolute;left:${fx + 1.6 * U}px;top:${fy + bar + fh - 5.2 * U}px;font-size:calc(var(--u)*2.2);opacity:0;z-index:7`;
    const fzFlash = fz.length ? el("div", null, null, win) : null; if (fzFlash) fzFlash.style.cssText = "position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none";
    const rings = (p.rings || []).concat(fz).map(r => { const d = el("div", null, r.label ? `<span>${esc(r.label)}</span>` : "", root); d.style.cssText = `position:absolute;border:${.45 * U}px solid var(--accent2);border-radius:${1.2 * U}px;box-shadow:0 0 0 ${.3 * U}px rgba(0,0,0,.6),0 0 ${3 * U}px rgba(250,204,21,.6);pointer-events:none`;
      if (r.label) { const s = d.firstChild; s.className = "pill2"; s.style.cssText += `;position:absolute;${(r.x + r.w / 2) > (c0[0] + c0[2] * .6) ? "right:-.2em" : "left:-.2em"};top:-2.6em;font-size:calc(var(--u)*2.2);white-space:nowrap`; } return { d, r }; });
    let pr = null; if (p.prompt) { pr = el("div", null, `<b>›</b><span></span><i></i>`, root); pr.style.cssText = `position:absolute;left:${fx + fw * .05}px;width:${fw * .9}px;top:${fy + bar + 1.6 * U}px;display:flex;align-items:flex-start;line-height:1.35;white-space:normal;gap:${1.2 * U}px;padding:${1.4 * U}px ${2 * U}px;border-radius:${1.6 * U}px;background:rgba(10,14,24,.94);border:2px solid var(--accent2);box-shadow:0 ${2 * U}px ${5 * U}px rgba(0,0,0,.6);font-weight:700;font-size:calc(var(--u)*${fw < W * .5 ? 2 : 2.4});color:#fff;z-index:6`;
      pr.firstChild.style.color = "var(--accent2)"; pr.lastChild.style.cssText = `display:inline-block;width:${.25 * U}px;height:1.1em;background:var(--accent2)`; }
    let tm = null; if (p.timer) { tm = el("div", "pill2", "", root); tm.style.cssText += `;position:absolute;right:${fx - 1 * U}px;top:${fy - 3 * U}px;font-family:OSW;font-size:calc(var(--u)*4.4);z-index:7;background:#ef4444;color:#fff`; }
    sourceLine(root, p);
    return { update(lt) { headerUpdate(h, lt);
      const a = E.out(prog(lt, 0, .5)); win.style.opacity = a; win.style.transform = `translateY(${(1 - a) * 4 * U}px) scale(${lerp(.96, 1, a)})`;
      const k = E.inout(prog(lt, p.pan_at != null ? p.pan_at - sc.start : 0, p.pan_dur || (sc.end - sc.start))); const c = c0.map((x, i) => lerp(x, c1[i], k));
      const s = fw / c[2]; v.style.transform = `scale(${s}) translate(${-c[0]}px,${-c[1]}px)`;
      if (fz.length) { let on = 0, fl = 0; for (const f of fz) { const a = (f.at != null ? f.at : sc.start + 1) - sc.start; if (lt >= a && lt < a + f.hold) on = 1; if (lt >= a && lt < a + .18) fl = Math.max(fl, 1 - (lt - a) / .18); }
        vp.style.filter = on ? "saturate(.35) brightness(.8)" : ""; set(fzTag, on); fzFlash.style.opacity = clamp(fl) * .55; win.style.transform = (win.style.transform || "").replace(/ ?scale\([^)]*\)$/, "") + (on ? " scale(1.015)" : ""); }
      for (const { d, r } of rings) { const t0 = (r.at != null ? r.at : sc.start + .6) - sc.start; const q = prog(lt, t0, .35), out = prog(lt, t0 + (r.hold || 2.2), .3);
        d.style.left = (fx + (r.x - c[0]) * s - .8 * U) + "px"; d.style.top = (fy + bar + (r.y - c[1]) * s - .8 * U) + "px"; d.style.width = (r.w * s + 1.6 * U) + "px"; d.style.height = (r.h * s + 1.6 * U) + "px";
        d.style.opacity = clamp(q * 3) * (1 - out); d.style.transform = `scale(${lerp(1.25, 1, E.back(q))})`; }
      if (pr) { const t0 = (p.prompt.at != null ? p.prompt.at : sc.start + .3) - sc.start; const full = p.prompt.text, n = Math.floor(clamp((lt - t0) / Math.max(.4, full.length * (p.prompt.speed || .035))) * full.length);
        pr.children[1].textContent = full.slice(0, n); pr.lastChild.style.opacity = Math.floor(lt * 3) % 2 ? 1 : 0; set(pr, E.out(prog(lt, t0 - .2, .3)) * (1 - prog(lt, (p.prompt.hide_at != null ? p.prompt.hide_at - sc.start : 99), .3))); }
      if (tm) { const t0 = (p.timer.at != null ? p.timer.at : sc.start + .5) - sc.start; const val = (p.timer.from || 0) + ((p.timer.to || 0) - (p.timer.from || 0)) * E.out(prog(lt, t0, p.timer.dur || 2));
        tm.textContent = `${p.timer.label ? p.timer.label + " " : "⏱ "}${Math.round(val)}${p.timer.unit || " GIÂY"}`; set(tm, clamp((lt - t0 + .2) * 4), `scale(${lerp(1.3, 1, E.out(prog(lt, t0, .3)))})`); }
    } };
  };

  // ======== NHỊP GRAPHIC (dùng trong p.then của title, hoặc làm module riêng) ========
  const at0 = (o, k, sc, def) => (o && o[k] != null ? o[k] - sc.start : def);
  const iconBox = (name, size, col, parent) => { const b = el("div", null, null, parent); b.style.cssText = `width:${size * U}px;height:${size * U}px;border-radius:${size * .24 * U}px;display:grid;place-items:center;background:color-mix(in srgb,${col} 20%,rgba(10,14,24,.9));border:2px solid color-mix(in srgb,${col} 60%,transparent);box-shadow:0 0 ${size * .4 * U}px color-mix(in srgb,${col} 30%,transparent)`;
    if (name) { const i = icon(name); i.style.width = i.style.height = (size * .5 * U) + "px"; i.style.background = col; b.appendChild(i); } return b; };
  const kick = (root, p, sc, xy) => { if (!p.kicker) return null; const k = el("div", "pill2", mark(p.kicker), root); k._c = !xy;
    k.style.cssText += xy ? `;position:absolute;left:${xy[0]}px;top:${xy[1]}px;font-size:calc(var(--u)*2.4)` : `;position:absolute;left:50%;top:${PORT() ? 16 : 12}%;font-size:calc(var(--u)*2.6);transform:translateX(-50%)`; k._at = at0(p, "kicker_at", sc, .1); return k; };
  const kickUp = (k, lt) => { if (k) { const a = E.out(prog(lt, k._at, .35)); k.style.opacity = a; k.style.transform = `${k._c ? "translateX(-50%) " : ""}translateY(${(1 - a) * 2 * U}px)`; } };

  // HỘI TỤ: hạt (người/dữ liệu) hoặc thẻ vai trò bay về một lõi. p.center{icon,text,cue}, p.items[{icon,label,cue}], p.merge_cue, p.particles, p.kicker
  M.converge = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const cx = W / 2, cy = H * (PORT() ? .45 : .5), k = kick(root, p, sc);
    const cv = el("canvas", null, null, root); cv.width = W; cv.height = H; cv.style.cssText = "position:absolute;inset:0"; const g = cv.getContext("2d");
    const R = rnd(7), N = p.particles != null ? p.particles : (p.items ? 0 : 160);
    const P = Array.from({ length: N }, () => ({ a: R() * 6.283, v: .25 + R() * .45, ph: R(), s: 1.5 + R() * 3 }));
    const core = el("div", null, null, root); const cs = (PORT() ? 20 : 17) * U;
    core.style.cssText = `position:absolute;left:${cx - cs / 2}px;top:${cy - cs / 2}px;width:${cs}px;height:${cs}px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle,rgba(250,204,21,.35),rgba(250,204,21,.06) 60%,transparent 72%);border:2px solid var(--accent2);box-shadow:0 0 ${5 * U}px rgba(250,204,21,.55)`;
    const ce = p.center || {}; if (ce.icon) { const i = icon(ce.icon); i.style.width = i.style.height = (cs * .46) + "px"; i.style.background = "#fff"; core.appendChild(i); }
    const lab = ce.text ? el("div", "pill2", mark(ce.text), root) : null; if (lab) lab.style.cssText += `;position:absolute;left:50%;top:${cy + cs / 2 + 2 * U}px;font-size:calc(var(--u)*${PORT() ? 3.4 : 3});white-space:nowrap`;
    const its = (p.items || []).map((it, i, A) => { const ang = -Math.PI / 2 + i * 2 * Math.PI / A.length, rx = (PORT() ? 34 : 40) * U, ry = (PORT() ? 30 : 23) * U;
      const c = el("div", null, null, root); c.style.cssText = "position:absolute;display:flex;flex-direction:column;align-items:center;gap:.5em;opacity:0"; iconBox(it.icon, 8, it.color || "#38bdf8", c);
      const t = el("div", null, mark(it.label || ""), c); t.style.cssText = "font-weight:800;font-size:calc(var(--u)*2.3);text-transform:uppercase;white-space:nowrap;text-shadow:0 2px 6px #000";
      return { c, x: cx + Math.cos(ang) * rx, y: cy + Math.sin(ang) * ry, at: at0(it, "at", sc, .15 + i * .18) }; });
    const mAt = at0(p, "merge_at", sc, 99), cAt = at0(ce, "at", sc, .1);
    return { update(lt) { kickUp(k, lt);
      g.clearRect(0, 0, W, H); const fade = 1 - prog(lt, mAt + .4, .5) * .7;
      for (const q of P) { const f = (lt * q.v + q.ph) % 1, r = (1 - E.inout(f)) * Math.hypot(W, H) * .55 + cs * .45;
        g.globalAlpha = clamp(f * 4) * (1 - f) * fade * clamp(lt * 2); g.fillStyle = f > .8 ? "#FACC15" : "#cbd5e1";
        g.beginPath(); g.arc(cx + Math.cos(q.a) * r, cy + Math.sin(q.a) * r * .8, q.s, 0, 6.283); g.fill(); }
      g.globalAlpha = 1;
      const ca = E.back(prog(lt, cAt, .5)), pulse = 1 + Math.sin(lt * 6) * .03 + (lt > mAt ? (1 - prog(lt, mAt + .3, .6)) * .2 : 0);
      set(core, clamp(ca * 2), `scale(${lerp(.3, 1, ca) * pulse})`); if (lab) set(lab, clamp(prog(lt, cAt + .2, .3) * 2), "translateX(-50%)");
      its.forEach((it, j) => { const a = E.back(prog(lt, it.at, .45)), m = E.inout(prog(lt, mAt + j * .05, .5));
        it.c.style.left = lerp(it.x, cx, m) + "px"; it.c.style.top = lerp(it.y, cy, m) + "px";
        set(it.c, clamp(a * 2) * (1 - m), `translate(-50%,-50%) scale(${lerp(.4, 1, a) * lerp(1, .2, m)})`); });
    } };
  };

  // BIẾN ĐỔI: cách cũ bị gạch → mũi tên → kết quả mới sáng lên. p.from{icon,text,strike_cue}, p.to{icon,text,cue}, p.arrow_cue, p.kicker
  M.transform = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), f = p.from || {}, t = p.to || {};
    const cw = PORT() ? W * .7 : 36 * U, ch = PORT() ? 24 * U : 32 * U;
    const pos = PORT() ? [[(W - cw) / 2, H * .24], [(W - cw) / 2, H * .24 + ch + 12 * U]] : [[W / 2 - cw - 8 * U, H * .3], [W / 2 + 8 * U, H * .3]];
    const card = (o, i) => { const c = el("div", "card2", null, root); c.style.cssText += `;position:absolute;left:${pos[i][0]}px;top:${pos[i][1]}px;width:${cw}px;height:${ch}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${2 * U}px;opacity:0`;
      iconBox(o.icon, PORT() ? 9 : 11, i ? "#FACC15" : "#94a3b8", c); const tx = el("div", null, mark(o.text || ""), c); tx.style.cssText = `font-weight:900;text-transform:uppercase;text-align:center;font-size:calc(var(--u)*${PORT() ? 3.6 : 3.4});line-height:1.12;padding:0 ${2 * U}px`; return c; };
    const A = card(f, 0), B = card(t, 1);
    const sx = el("div", null, `<svg width="${cw}" height="${ch}" style="position:absolute;left:0;top:0;overflow:visible"><path d="M${2 * U} ${ch - 2 * U} L${cw - 2 * U} ${2 * U}" stroke="#EF3340" stroke-width="${1.4 * U}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`, A); const sl = sx.querySelector("path");
    const okB = el("div", "pill2", "✓", B); okB.style.cssText += `;position:absolute;right:${-1.8 * U}px;top:${-1.8 * U}px;background:#22c55e;color:#fff;font-size:calc(var(--u)*3);opacity:0`;
    const L = PORT() ? 8 * U : 12 * U;
    const ar = el("div", null, PORT() ? `<svg width="${4 * U}" height="${L}"><path d="M${2 * U} 0 V${L - 2 * U} M${.4 * U} ${L - 3.4 * U} L${2 * U} ${L - 1.2 * U} L${3.6 * U} ${L - 3.4 * U}" stroke="#FACC15" stroke-width="${.9 * U}" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`
      : `<svg width="${L}" height="${4 * U}"><path d="M0 ${2 * U} H${L - 1.4 * U} M${L - 3.4 * U} ${.4 * U} L${L - 1.2 * U} ${2 * U} L${L - 3.4 * U} ${3.6 * U}" stroke="#FACC15" stroke-width="${.9 * U}" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`, root);
    ar.style.cssText = PORT() ? `position:absolute;left:${W / 2 - 2 * U}px;top:${pos[0][1] + ch + 2 * U}px` : `position:absolute;left:${W / 2 - L / 2}px;top:${pos[0][1] + ch / 2 - 2 * U}px`; const ap = ar.querySelector("path");
    const sAt = at0(f, "strike_at", sc, .6), aAt = at0(p, "arrow_at", sc, sAt + .4), tAt = at0(t, "at", sc, aAt + .3);
    return { update(lt) { kickUp(k, lt);
      const a = E.back(prog(lt, 0, .45)); set(A, clamp(a * 2), `translateX(${(1 - a) * -6 * U}px)`);
      const x = prog(lt, sAt, .35); sl.style.strokeDashoffset = 1 - E.out(x); A.style.filter = `grayscale(${x}) brightness(${1 - x * .45})`;
      ap.style.strokeDashoffset = 1 - E.out(prog(lt, aAt, .4));
      const b = E.back(prog(lt, tAt, .5)); set(B, clamp(b * 2), `scale(${lerp(.6, 1, b)})`); B.style.boxShadow = `0 0 ${lerp(0, 5, clamp(b)) * U}px rgba(250,204,21,.45)`;
      const o = E.back(prog(lt, tAt + .35, .35)); set(okB, clamp(o * 2), `scale(${lerp(2, 1, o)})`);
    } };
  };

  // Ô VUÔNG 100: p.value (vd 45), p.total (100), p.cue (lúc tô), p.color, p.caption{…}, p.caption_cue, p.kicker, p.source
  M.waffle = (root, p, sc) => {
    const k = kick(root, p, sc), tot = p.total || 100, n = Math.round(p.value || 0), cols = 10, rows = Math.ceil(tot / cols);
    const side = PORT() ? W * .7 : 46 * U, cell = side / cols;
    const g = el("div", null, null, root); g.style.cssText = `position:absolute;left:${PORT() ? (W - side) / 2 : W / 2 - side - 4 * U}px;top:${PORT() ? H * .22 : H * .24}px;width:${side}px;height:${cell * rows}px`;
    const cells = Array.from({ length: tot }, (_, i) => { const c = el("div", null, null, g); c.style.cssText = `position:absolute;left:${(i % cols) * cell + cell * .1}px;top:${Math.floor(i / cols) * cell + cell * .1}px;width:${cell * .8}px;height:${cell * .8}px;border-radius:${cell * .18}px;background:rgba(148,163,184,.22)`; return c; });
    const side2 = el("div", null, null, root); side2.style.cssText = PORT() ? `position:absolute;left:0;right:0;top:${H * .22 + side + 4 * U}px;text-align:center` : `position:absolute;left:${W / 2 + 4 * U}px;right:${6 * U}px;top:${H * .3}px`;
    const big = el("div", "big", "0%", side2); big.style.cssText += `;font-family:OSW;font-size:calc(var(--u)*${PORT() ? 16 : 17});line-height:1;color:${p.color || "#EF4444"}`;
    const cap = p.caption ? el("div", null, mark(p.caption), side2) : null; if (cap) cap.style.cssText = `font-weight:800;font-size:calc(var(--u)*${PORT() ? 3.6 : 3.4});line-height:1.2;margin-top:.4em;text-transform:uppercase`;
    const src = sourceLine(root, p); const fAt = at0(p, "at", sc, .4), cAt = at0(p, "caption_at", sc, fAt + 1);
    return { update(lt) { kickUp(k, lt);
      cells.forEach((c, i) => { c.style.opacity = prog(lt, i * .004, .25); const on = i < n && lt >= fAt + (i / Math.max(n, 1)) * 1.2;
        c.style.background = on ? (p.color || "#EF4444") : "rgba(148,163,184,.22)"; c.style.boxShadow = on ? `0 0 ${cell * .3}px ${p.color || "#EF4444"}` : "none"; });
      const v = E.out(prog(lt, fAt, 1.2)); big.textContent = (p.prefix || "") + Math.round(n * v) + (p.unit != null ? p.unit : "%"); set(big, clamp(prog(lt, fAt - .1, .3) * 2));
      if (cap) { const a = E.out(prog(lt, cAt, .4)); set(cap, a, `translateY(${(1 - a) * 2 * U}px)`); } set(src, E.out(prog(lt, .6, .5)));
    } };
  };

  // HAI THẺ PHÁN ĐỊNH: p.items[{icon,title,verdict,tone:"ok"|"warn"|"bad",cue}], p.kicker
  M.duo = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), its = p.items || [], n = its.length || 1, TONE = { ok: ["#22c55e", "✓"], warn: ["#F59E0B", "⚠"], bad: ["#EF4444", "✗"] };
    const cw = PORT() ? W * .78 : Math.min(42 * U, (W - 14 * U) / n - 4 * U), ch = PORT() ? 22 * U : 36 * U;
    const cards = its.map((it, i) => { const [col, sym] = TONE[it.tone || "ok"];
      const x = PORT() ? (W - cw) / 2 : (W - (cw * n + 5 * U * (n - 1))) / 2 + i * (cw + 5 * U), y = PORT() ? H * .26 + i * (ch + 4 * U) : H * .28;
      const c = el("div", "card2", null, root); c.style.cssText += `;position:absolute;left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;display:flex;${PORT() ? "flex-direction:row;padding-left:" + 4 * U + "px" : "flex-direction:column;justify-content:center"};align-items:center;gap:${2.2 * U}px;opacity:0;border-color:color-mix(in srgb,${col} 50%,transparent)`;
      iconBox(it.icon, PORT() ? 9 : 10, col, c); const tx = el("div", null, null, c); tx.style.cssText = `text-align:${PORT() ? "left" : "center"}`;
      const t = el("div", null, mark(it.title || ""), tx); t.style.cssText = `font-weight:900;text-transform:uppercase;font-size:calc(var(--u)*${PORT() ? 4 : 4.2})`;
      const v = el("div", "pill2", sym + " " + mark(it.verdict || ""), tx); v.style.cssText += `;margin-top:${1.2 * U}px;background:${col};color:${it.tone === "warn" ? "#111" : "#fff"};font-size:calc(var(--u)*2.6)`;
      return { c, v, at: at0(it, "at", sc, .2 + i * 1.2) }; });
    return { update(lt) { kickUp(k, lt); for (const q of cards) { const a = E.back(prog(lt, q.at, .45)); set(q.c, clamp(a * 2), `translateY(${(1 - a) * 6 * U}px)`); const b = E.back(prog(lt, q.at + .45, .35)); set(q.v, clamp(b * 2), `scale(${lerp(1.6, 1, b)})`); } } };
  };

  // CÂU LỆNH → VIDEO: ô gõ prompt thật, rồi khung video (clip thật) bật ra, kèm chip. p.prompt{text,cue,speed}, p.video, p.video_cue, p.rate, p.clip_start, p.chips[{icon,text,cue}], p.caption, p.ring_cue, p.kicker
  M.prompt_video = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const pr = p.prompt || {};
    const lw = PORT() ? W * .86 : W * .4, lx = PORT() ? (W - lw) / 2 : 6 * U, ly = PORT() ? H * .2 : H * .3; const k = kick(root, p, sc, [lx, ly - 6 * U]);
    const box = el("div", null, `<div style="font-size:calc(var(--u)*2.2);letter-spacing:.14em;color:var(--accent2);font-weight:800;margin-bottom:.6em">CÂU LỆNH</div><span></span><i></i>`, root);
    box.style.cssText = `position:absolute;left:${lx}px;top:${ly}px;width:${lw}px;box-sizing:border-box;padding:${2.2 * U}px ${2.6 * U}px;border-radius:${1.8 * U}px;background:rgba(10,14,24,.92);border:2px solid rgba(250,204,21,.6);font-weight:700;line-height:1.4;font-size:calc(var(--u)*${PORT() ? 3 : 2.7});color:#fff;opacity:0`;
    const sp = box.children[1], cur = box.children[2]; cur.style.cssText = "display:inline-block;width:.12em;height:1em;background:var(--accent2);vertical-align:-.12em;margin-left:.08em";
    const tall = p.aspect === "9:16" && !PORT(); const vw = PORT() ? W * .86 : tall ? H * .64 * 9 / 16 : W * .44, vh = tall ? H * .64 : vw * 9 / 16, vx = PORT() ? (W - vw) / 2 : W - vw - (tall ? 12 : 5) * U, vy = PORT() ? H * .48 : tall ? H * .15 : H * .26; // p.aspect "9:16": khung dọc cho video TikTok/Reels
    const fr = el("div", "qa-ev", null, root); fr.style.cssText = `position:absolute;left:${vx}px;top:${vy}px;width:${vw}px;height:${vh}px;border-radius:${1.4 * U}px;overflow:hidden;border:${.4 * U}px solid #fff;box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.7);background:#000;opacity:0`;
    const vAt = at0(p, "video_at", sc, 1.5);
    if (p.video) { const v = el("video", null, null, fr); v.src = p.video; v.muted = true; v.preload = "auto"; v.style.cssText = "width:100%;height:100%;object-fit:cover"; v._d = { start: sc.start + vAt, end: sc.end }; v._rate = p.rate || 1; v._off = p.clip_start || 0; VIDS.push(v); }
    const capE = p.caption ? el("div", "co-src", "Ảnh: " + esc(p.caption), root) : null; if (capE) capE.style.cssText = `position:absolute;left:${vx}px;top:${vy + vh + 1 * U}px;font-size:calc(var(--u)*1.6);color:rgba(255,255,255,.75)`;
    const crow = el("div", null, null, root); crow.style.cssText = `position:absolute;left:${lx}px;top:${PORT() ? vy + vh + 4 * U : ly + 30 * U}px;display:flex;gap:${1.6 * U}px;flex-wrap:wrap;width:${lw}px`;
    const chips = (p.chips || []).map((c, i) => { const e = el("div", "pill2", "", crow); if (c.icon) { const ic = icon(c.icon); ic.style.cssText += ";width:1.1em;height:1.1em;background:#111;margin-right:.4em;vertical-align:-.15em"; e.appendChild(ic); } e.appendChild(document.createTextNode(c.text || ""));
      e.style.cssText += `;font-size:calc(var(--u)*2.8);opacity:0`; return { e, at: at0(c, "at", sc, 2 + i * .6) }; });
    const tAt = at0(pr, "at", sc, .2), sp0 = pr.speed || .035, rAt = at0(p, "ring_at", sc, 99);
    return { update(lt) { kickUp(k, lt);
      const a = E.out(prog(lt, tAt - .25, .3)); set(box, a, `translateY(${(1 - a) * 2 * U}px)`); const full = pr.text || "", n = Math.floor(clamp((lt - tAt) / Math.max(.4, full.length * sp0)) * full.length);
      sp.textContent = full.slice(0, n); cur.style.opacity = n < full.length && Math.floor(lt * 3) % 2 ? 1 : 0;
      const r = prog(lt, rAt, .3); box.style.borderColor = r > 0 ? "var(--accent2)" : "rgba(250,204,21,.6)"; box.style.boxShadow = r > 0 ? `0 0 ${4 * U}px rgba(250,204,21,.6)` : "none";
      const b = E.back(prog(lt, vAt, .5)); set(fr, clamp(b * 2), `scale(${lerp(.7, 1, b)})`); if (capE) set(capE, clamp(b * 2));
      for (const c of chips) { const q = E.back(prog(lt, c.at, .4)); set(c.e, clamp(q * 2), `scale(${lerp(.4, 1, q)})`); }
    } };
  };

  // AI CŨNG LÀM ĐƯỢC: hàng người, mỗi người nhận một thẻ (video ✓); chip "điều kiện cũ" bị gạch. p.n, p.badge_icon, p.badge_cue, p.caption{text,cue}, p.strike{text,cue,strike_cue}, p.kicker
  M.people = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), n = p.n || 5, cols = ["#38bdf8", "#f472b6", "#a78bfa", "#34d399", "#fb923c", "#facc15"], gap = PORT() ? W * .86 / n : Math.min(17 * U, W * .7 / n);
    const y = H * (PORT() ? .42 : .44), x0 = W / 2 - gap * (n - 1) / 2, bAt = at0(p, "badge_at", sc, .8);
    const ps = Array.from({ length: n }, (_, i) => { const c = el("div", null, null, root); c.style.cssText = `position:absolute;left:${x0 + i * gap}px;top:${y}px;display:flex;flex-direction:column;align-items:center;opacity:0`;
      const card = el("div", null, null, c); const cw = Math.min(gap * .82, 13 * U); card.style.cssText = `width:${cw}px;height:${cw * .62}px;border-radius:${.9 * U}px;background:linear-gradient(135deg,#1e293b,#0f172a);border:2px solid ${cols[i % 6]};display:grid;place-items:center;margin-bottom:${1.4 * U}px;position:relative;opacity:0`;
      const pl = icon(p.badge_icon || "play"); pl.style.cssText += `;width:${cw * .3}px;height:${cw * .3}px;background:#fff`; card.appendChild(pl);
      const ok = el("div", null, "✓", card); ok.style.cssText = `position:absolute;right:-.6em;top:-.6em;width:1.5em;height:1.5em;border-radius:50%;background:#22c55e;color:#fff;font-weight:900;display:grid;place-items:center;font-size:calc(var(--u)*1.8)`;
      const av = iconBox("user", PORT() ? 8 : 9, cols[i % 6], c); av.style.borderRadius = "50%"; return { c, card }; });
    const cp = p.caption || {}; const cap = cp.text ? el("div", "headline", mark(cp.text), root) : null; if (cap) cap.style.cssText += `;position:absolute;left:6%;right:6%;margin:0;text-align:center;top:${y + 24 * U}px;font-size:calc(var(--u)*${PORT() ? 5 : 5.4})`;
    const s = p.strike || {}; const ch = s.text ? el("div", "pill2", mark(s.text), root) : null;
    if (ch) { ch.style.cssText += `;position:absolute;left:50%;top:${y - 19 * U}px;font-size:calc(var(--u)*2.8);background:#334155;color:#fff`; const ln = el("div", null, null, ch); ln.style.cssText = "position:absolute;left:-4%;right:-4%;top:50%;height:.18em;background:#EF3340;transform-origin:0 50%"; ch._ln = ln; }
    return { update(lt) { kickUp(k, lt);
      ps.forEach((q, i) => { const a = E.back(prog(lt, i * .1, .45)); set(q.c, clamp(a * 2), `translateX(-50%) translateY(${(1 - a) * 4 * U}px)`);
        const b = E.back(prog(lt, bAt + i * .18, .4)); set(q.card, clamp(b * 2), `scale(${lerp(.3, 1, b)}) translateY(${(1 - b) * 2 * U}px)`); });
      if (cap) { const a = E.out(prog(lt, at0(cp, "at", sc, bAt + 1), .4)); set(cap, a, `translateY(${(1 - a) * 2 * U}px)`); }
      if (ch) { const sa = at0(s, "strike_at", sc, 99); set(ch, E.out(prog(lt, at0(s, "at", sc, 99), .3)), "translateX(-50%)"); ch._ln.style.transform = `scaleX(${E.out(prog(lt, sa, .35))})`; ch.style.filter = `brightness(${1 - prog(lt, sa, .3) * .35})`; }
    } };
  };

  // ======== CHUYỂN ĐỘNG MỚI (học từ video-shotcraft, viết lại cho engine HTML) ========
  const fmtV = (v, p) => (p.prefix || "") + fmtNum(v, p.decimals) + (p.unit || "");

  // BIỂU ĐỒ VƯỢT KHUNG: đường số liệu leo dần, điểm cuối VỌT qua "trần" cũ, khựng nửa nhịp rồi trục y đổi thang.
  // p.points[{x,v}], p.ceiling (trần ban đầu), p.at (cue lúc vọt), p.unit/prefix/decimals, p.ceiling_label, p.kicker/title, p.source
  M.breakout = (root, p, sc) => {
    const h = header(root, p), pts = p.points || [], n = pts.length;
    const X0 = 12 * U, X1 = W - 14 * U, Y0 = H * (PORT() ? .34 : .36), Y1 = H * (PORT() ? .7 : .78);
    const sv = el("div", null, null, root); sv.style.cssText = "position:absolute;inset:0";
    const vmax = Math.max(...pts.map(q => q.v)), ceil0 = p.ceiling || vmax * .55; const nice = v => { const e = Math.pow(10, Math.floor(Math.log10(v))); return [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].map(m => m * e).find(x => x >= v); }; const ceil1 = nice(vmax * 1.06);
    const lab = el("div", "pill2", "", root); lab.style.cssText += `;position:absolute;font-size:calc(var(--u)*3.4);opacity:0;background:var(--accent2);color:#111;white-space:nowrap`;
    const src = sourceLine(root, p); const bAt = at0(p, "at", sc, (sc.end - sc.start) * .55);
    return { update(lt) { headerUpdate(h, lt);
      const grow = clamp(lt / Math.max(.5, bAt - .2)), rs = E.inout(prog(lt, bAt + .65, .7)), ymax = lerp(ceil0, ceil1, rs);
      const shake = (lt > bAt && lt < bAt + .35) ? Math.sin(lt * 90) * U * .5 * (1 - (lt - bAt) / .35) : 0;
      const yOf = v => Y1 - (v / ymax) * (Y1 - Y0), xOf = i => X0 + i * (X1 - X0) / Math.max(1, n - 1);
      const shown = Math.min(n - 1, grow * (n - 2)); let d = "";
      for (let i = 0; i <= Math.floor(shown); i++) d += (i ? "L" : "M") + xOf(i) + " " + yOf(pts[i].v);
      const fi = Math.floor(shown); if (fi < n - 2 && shown > fi) { const f = shown - fi; d += `L${lerp(xOf(fi), xOf(fi + 1), f)} ${yOf(lerp(pts[fi].v, pts[fi + 1].v, f))}`; }
      const kb = E.back(prog(lt, bAt, .3)); let last = "";
      if (lt >= bAt) last = `M${xOf(n - 2)} ${yOf(pts[n - 2].v)}L${lerp(xOf(n - 2), xOf(n - 1), clamp(kb * 1.2))} ${yOf(lerp(pts[n - 2].v, pts[n - 1].v, kb))}`;
      let grid = ""; for (let g = 1; g <= 4; g++) { const v = ymax * g / 4, y = yOf(v); grid += `<line x1="${X0}" x2="${X1}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,.1)"/><text x="${X0 - 1.2 * U}" y="${y + .8 * U}" fill="#94a3b8" font-size="${2.8 * U}" font-weight="700" text-anchor="end">${esc(fmtV(v, p))}</text>`; }
      const xs = pts.map((q, i) => `<text x="${xOf(i)}" y="${Y1 + 3.6 * U}" fill="#94a3b8" font-size="${2.8 * U}" font-weight="700" text-anchor="middle">${esc(String(q.x))}</text>`).join("");
      const cy = yOf(ceil0), broke = lt >= bAt + .12, fadeC = 1 - rs;
      sv.innerHTML = `<svg width="${W}" height="${H}" style="overflow:visible;transform:translate(${shake}px,0)">${grid}${xs}
        <line x1="${X0}" x2="${X1}" y1="${cy}" y2="${cy}" stroke="${broke ? "#ef4444" : "rgba(255,255,255,.55)"}" stroke-width="${.35 * U}" stroke-dasharray="${1.2 * U} ${.8 * U}" opacity="${fadeC}"/>
        <text x="${X1}" y="${cy - 1.2 * U}" fill="${broke ? "#ef4444" : "#cbd5e1"}" font-size="${2.3 * U}" font-weight="800" text-anchor="end" opacity="${fadeC}">${esc(p.ceiling_label || "MỨC CAO NHẤT TRƯỚC ĐÂY")}</text>
        <path d="${d}" fill="none" stroke="#e2e8f0" stroke-width="${.55 * U}" stroke-linejoin="round" stroke-linecap="round"/>
        <path d="${last}" fill="none" stroke="var(--accent2)" stroke-width="${.9 * U}" stroke-linecap="round" style="filter:drop-shadow(0 0 ${1.2 * U}px rgba(250,204,21,.8))"/></svg>`;
      const lx = xOf(n - 1), ly = yOf(lerp(pts[n - 2] ? pts[n - 2].v : 0, pts[n - 1].v, kb)); const la = E.back(prog(lt, bAt + 1.2, .4));
      lab.textContent = fmtV(pts[n - 1].v, p); set(lab, clamp(la * 2), `translate(-100%,-130%) scale(${lerp(.5, 1, la)})`); lab.style.left = lx + "px"; lab.style.top = ly + "px";
      set(src, E.out(prog(lt, .8, .5)));
    } };
  };

  // ĐÀN CHẤM THÀNH SỐ: hàng trăm chấm (mỗi chấm = một người/một đơn vị) bay lượn rồi gom lại thành con số. p.text, p.at, p.color, p.caption{text,cue}, p.kicker
  M.dot_number = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), cv = el("canvas", null, null, root); cv.width = W; cv.height = H; cv.style.cssText = "position:absolute;inset:0"; const g = cv.getContext("2d");
    const off = document.createElement("canvas"); off.width = W; off.height = H; const o = off.getContext("2d");
    const fsz = Math.min(H * (PORT() ? .2 : .36), W * 1.5 / Math.max(3, String(p.text || "").length)); o.fillStyle = "#fff"; o.font = `700 ${fsz}px OSW, sans-serif`; o.textAlign = "center"; o.textBaseline = "middle";
    o.fillText(String(p.text || ""), W / 2, H * (PORT() ? .42 : .46)); const id = o.getImageData(0, 0, W, H).data;
    const step = Math.max(6, Math.round(fsz / 22)), tg = []; for (let y = 0; y < H; y += step) for (let x = 0; x < W; x += step) if (id[(y * W + x) * 4 + 3] > 128) tg.push([x, y]);
    const R = rnd(11), col = p.color || "#FACC15", D = tg.map(([x, y]) => ({ tx: x, ty: y, sx: R() * W, sy: H * .15 + R() * H * .7, ph: R() * 6.28, d: R() }));
    const fAt = at0(p, "at", sc, .8), cp = p.caption || {}; const cap = cp.text ? el("div", "headline", mark(cp.text), root) : null;
    if (cap) cap.style.cssText += `;position:absolute;left:6%;right:6%;margin:0;text-align:center;top:${H * (PORT() ? .55 : .68)}px;font-size:calc(var(--u)*${PORT() ? 4.4 : 4.6})`;
    return { update(lt) { kickUp(k, lt); g.clearRect(0, 0, W, H);
      for (const q of D) { const m = E.inout(prog(lt, fAt + q.d * .5, .9)); const wx = q.sx + Math.sin(lt * 1.3 + q.ph) * 2 * U, wy = q.sy + Math.cos(lt * 1.1 + q.ph) * 2 * U;
        const x = lerp(wx, q.tx, m), y = lerp(wy, q.ty, m); g.globalAlpha = clamp(lt * 2) * (.55 + .45 * m); g.fillStyle = m > .98 ? col : "#cbd5e1";
        g.beginPath(); g.arc(x, y, step * .36, 0, 6.283); g.fill(); }
      g.globalAlpha = 1; if (cap) { const a = E.out(prog(lt, at0(cp, "at", sc, fAt + 1.4), .4)); set(cap, a, `translateY(${(1 - a) * 2 * U}px)`); }
    } };
  };

  // TRỤC THỜI GIAN: máy quay lướt ngang theo các mốc, mỗi mốc bật một thẻ đúng lúc đọc. p.events[{label (năm), text, icon?, photo?, cue}], p.kicker
  M.timeline = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), ev = p.events || [], gap = PORT() ? W * .62 : 46 * U, ay = H * (PORT() ? .62 : .66);
    const track = el("div", null, null, root); track.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${H}px`;
    const line = el("div", null, null, track); line.style.cssText = `position:absolute;left:${W / 2 - 20 * U}px;top:${ay}px;height:${.4 * U}px;width:${gap * (ev.length - 1) + 40 * U}px;background:linear-gradient(90deg,transparent,rgba(250,204,21,.7) 8%,rgba(250,204,21,.7) 92%,transparent);transform-origin:0 50%`;
    const it = ev.map((e, i) => { const x = W / 2 + i * gap;
      const dot = el("div", null, null, track); dot.style.cssText = `position:absolute;left:${x - 1.3 * U}px;top:${ay - 1.1 * U}px;width:${2.6 * U}px;height:${2.6 * U}px;border-radius:50%;background:#111;border:${.45 * U}px solid var(--accent2)`;
      const yr = el("div", null, esc(e.label || ""), track); yr.style.cssText = `position:absolute;left:${x}px;top:${ay + 2.6 * U}px;transform:translateX(-50%);font-family:OSW;font-weight:700;font-size:calc(var(--u)*4.6);color:#fff;white-space:nowrap`;
      const cw = PORT() ? W * .6 : 44 * U; const c = el("div", "card2 qa-ev", null, track); c.style.cssText += `;position:absolute;left:${x - cw / 2}px;width:${cw}px;bottom:${H - ay + 3.4 * U}px;padding:${2 * U}px;display:flex;flex-direction:column;gap:${1.2 * U}px;opacity:0`;
      if (e.photo) { const ph = img(e.photo); ph.style.cssText = `width:100%;height:${cw * .5}px;object-fit:cover;border-radius:${U}px`; c.appendChild(ph); }
      if (e.icon && !e.photo) iconBox(e.icon, 9, "#FACC15", c);
      const tx = el("div", null, mark(e.text || ""), c); tx.style.cssText = `font-weight:800;font-size:calc(var(--u)*${PORT() ? 3.8 : 3.6});line-height:1.2`;
      return { c, dot, yr, at: at0(e, "at", sc, .3 + i * 1.6), x }; });
    return { update(lt) { kickUp(k, lt);
      let cur = -1; it.forEach((q, i) => { if (lt >= q.at - .35) cur = i; }); let cam = 0;
      it.forEach((q, i) => { if (i === 0) return; cam += E.inout(prog(lt, q.at - .55, .6)) * gap; });
      track.style.transform = `translateX(${-cam}px)`; line.style.transform = `scaleX(${E.out(prog(lt, 0, .8))})`;
      it.forEach((q, i) => { const a = E.back(prog(lt, q.at, .45)); set(q.c, clamp(a * 2) * (i === cur ? 1 : .38), `translateY(${(1 - a) * 3 * U}px) scale(${i === cur ? 1 : .9})`);
        q.dot.style.background = lt >= q.at ? "var(--accent2)" : "#111"; q.dot.style.boxShadow = i === cur && lt >= q.at ? `0 0 ${2.4 * U}px var(--accent2)` : "none"; set(q.yr, clamp(prog(lt, q.at - .6, .4) * 2) * (i === cur ? 1 : .5), "translateX(-50%)"); });
    } };
  };

  // TRƯỚC / SAU: hai ảnh chồng nhau, thanh chia vụt sang rồi trượt chậm để lộ bản "sau". p.before{photo,label}, p.after{photo,label}, p.at, p.source
  M.slider = (root, p, sc) => {
    const b = p.before || {}, a = p.after || {}; const fw = PORT() ? W * .9 : W * .76, fh = PORT() ? fw * 1.1 : fw * 9 / 16 > H * .66 ? H * .66 : fw * 9 / 16;
    const fx = (W - fw) / 2, fy = PORT() ? H * .2 : H * .17;
    const box = el("div", "qa-ev", null, root); box.style.cssText = `position:absolute;left:${fx}px;top:${fy}px;width:${fw}px;height:${fh}px;border-radius:${1.4 * U}px;overflow:hidden;border:2px solid rgba(255,255,255,.2);box-shadow:0 ${3 * U}px ${8 * U}px rgba(0,0,0,.6)`;
    const A = img(a.photo); A.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover"; box.appendChild(A);
    const Bi = img(b.photo); Bi.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover"; box.appendChild(Bi);
    const bar = el("div", null, `<i></i>`, box); bar.style.cssText = `position:absolute;top:0;bottom:0;width:${.5 * U}px;background:#fff;box-shadow:0 0 ${2 * U}px rgba(0,0,0,.7)`;
    bar.firstChild.style.cssText = `position:absolute;left:50%;top:50%;width:${5 * U}px;height:${5 * U}px;margin:${-2.5 * U}px 0 0 ${-2.5 * U}px;border-radius:50%;background:#fff;box-shadow:0 0 0 ${.5 * U}px rgba(0,0,0,.35)`;
    const lb = el("div", "pill2", esc(b.label || "TRƯỚC"), box), la = el("div", "pill2", esc(a.label || "SAU"), box);
    lb.style.cssText += `;position:absolute;left:${1.6 * U}px;top:${1.6 * U}px;font-size:calc(var(--u)*2.6);background:#334155;color:#fff`; la.style.cssText += `;position:absolute;right:${1.6 * U}px;top:${1.6 * U}px;font-size:calc(var(--u)*2.6)`;
    const src = sourceLine(root, p); const sAt = at0(p, "at", sc, 1);
    return { update(lt) { const e = E.out(prog(lt, 0, .45)); set(box, e, `scale(${lerp(.94, 1, e)})`);
      const f = E.out(prog(lt, sAt, .32)), s2 = E.inout(prog(lt, sAt + .32, 1.6)); const x = lerp(lerp(100, 18, f), p.rest != null ? p.rest : 50, s2);
      Bi.style.clipPath = `inset(0 ${100 - x}% 0 0)`; bar.style.left = `calc(${x}% - ${.25 * U}px)`; set(la, clamp(prog(lt, sAt + .1, .3) * 2)); set(src, E.out(prog(lt, .8, .5)));
    } };
  };

  // 3D — BĂNG CHUYỀN THẺ: các thẻ xếp vòng tròn trong không gian, vòng xoay dừng đúng thẻ đang được đọc. p.items[{icon|photo,label,cue}], p.kicker, p.tilt
  M.orbit3d = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), its = p.items || [], n = Math.max(1, its.length), cw = (PORT() ? 38 : 30) * U, chh = cw * .78, stp = p.step || Math.min(360 / n, 38), Rr = cw * 1.08 / (2 * Math.sin(stp * Math.PI / 360));
    const stg = el("div", null, null, root); stg.style.cssText = `position:absolute;inset:0;perspective:${W * 1.1}px;perspective-origin:50% ${PORT() ? 40 : 38}%`;
    const ring = el("div", null, null, stg); ring.style.cssText = `position:absolute;left:50%;top:${PORT() ? 44 : 50}%;width:0;height:0;transform-style:preserve-3d`;
    const cards = its.map((it, i) => { const c = el("div", "card2", null, ring); c.style.cssText += `;position:absolute;left:${-cw / 2}px;top:${-chh / 2}px;width:${cw}px;height:${chh}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${1.6 * U}px;backface-visibility:hidden;transform:rotateY(${i * stp}deg) translateZ(${Rr}px)`;
      if (it.photo) { const ph = img(it.photo); ph.style.cssText = `width:86%;height:56%;object-fit:cover;border-radius:${U}px`; c.appendChild(ph); } else iconBox(it.icon || "star", 9, it.color || "#FACC15", c);
      const t = el("div", null, mark(it.label || ""), c); t.style.cssText = `font-weight:900;text-transform:uppercase;text-align:center;font-size:calc(var(--u)*${PORT() ? 3.4 : 2.8});padding:0 ${1.4 * U}px;line-height:1.15`;
      return { c, at: at0(it, "at", sc, .6 + i * 1.1) }; });
    return { update(lt) { kickUp(k, lt);
      let ang = 0; cards.forEach((q, i) => { if (i) ang += E.inout(prog(lt, q.at - .5, .7)) * stp; });
      const intro = E.out(prog(lt, 0, .9)); ring.style.transform = `translateZ(${-Rr}px) rotateX(${-(p.tilt != null ? p.tilt : 8)}deg) rotateY(${-ang - (1 - intro) * 70}deg)`; set(stg, intro);
      cards.forEach((q, i) => { const front = Math.abs(((i * stp - ang) % 360 + 540) % 360 - 180); const f = clamp(1 - front / (stp * 1.2));
        q.c.style.borderColor = f > .5 ? "var(--accent2)" : ""; q.c.style.boxShadow = f > .5 ? `0 0 ${4 * U}px rgba(250,204,21,.45)` : ""; q.c.style.filter = `brightness(${.45 + .55 * f})`; q.c.style.opacity = front > 100 ? 0 : 1; });
    } };
  };

  // 3D — TÁCH LỚP: các lớp xếp chồng nghiêng 3D, rồi tách ra theo chiều sâu, mỗi lớp hiện nhãn đúng lúc đọc. p.layers[{label,icon,color,cue}] (dưới → trên), p.explode_cue, p.merge_cue, p.kicker
  M.exploded3d = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), L = p.layers || [], n = L.length, pw = (PORT() ? 56 : 40) * U, ph = pw * .62;
    const stg = el("div", null, null, root); stg.style.cssText = `position:absolute;inset:0;perspective:${W * 1.4}px`;
    const grp = el("div", null, null, stg); grp.style.cssText = `position:absolute;left:${PORT() ? 50 : 40}%;top:${PORT() ? 46 : 54}%;width:0;height:0;transform-style:preserve-3d`;
    const cols = ["#38bdf8", "#a78bfa", "#34d399", "#fb923c", "#f472b6", "#facc15"];
    const ls = L.map((l, i) => { const c = l.color || cols[i % 6]; const d = el("div", null, null, grp);
      d.style.cssText = `position:absolute;left:${-pw / 2}px;top:${-ph / 2}px;width:${pw}px;height:${ph}px;border-radius:${1.6 * U}px;background:linear-gradient(135deg,color-mix(in srgb,${c} 38%,#0b1120),#0b1120 75%);border:2px solid color-mix(in srgb,${c} 75%,transparent);box-shadow:0 0 ${3 * U}px color-mix(in srgb,${c} 35%,transparent);display:grid;place-items:center`;
      if (l.icon) { const ic = icon(l.icon); ic.style.width = ic.style.height = (ph * .34) + "px"; ic.style.background = c; d.appendChild(ic); }
      const tg = el("div", "pill2", mark(l.label || ""), root); tg.style.cssText += `;position:absolute;font-size:calc(var(--u)*${PORT() ? 3 : 2.7});opacity:0;white-space:nowrap;border-left:${.6 * U}px solid ${c}`;
      return { d, tg, at: at0(l, "at", sc, 1.2 + i * .6) }; });
    const eAt = at0(p, "explode_at", sc, .8), mAt = at0(p, "merge_at", sc, 99);
    return { update(lt) { kickUp(k, lt);
      const intro = E.out(prog(lt, 0, .7)), ex = E.back(prog(lt, eAt, .9)) * (1 - E.inout(prog(lt, mAt, .7))), spin = lt * 4;
      grp.style.transform = `rotateX(58deg) rotateZ(${-38 + spin * .4}deg) scale(${lerp(.8, 1, intro)})`; set(stg, intro);
      const gapZ = (PORT() ? 9 : 8.5) * U;
      ls.forEach((q, i) => { const z = (i - (n - 1) / 2) * lerp(1.2 * U, gapZ, ex); q.d.style.transform = `translateZ(${z}px)`;
        const r = q.d.getBoundingClientRect(), S0 = stage.getBoundingClientRect(); const a = E.out(prog(lt, q.at, .35)) * clamp(ex * 1.4);
        q.tg.style.left = (r.right - S0.left + 3 * U) + "px"; q.tg.style.top = (r.top - S0.top + r.height / 2 - 2 * U) + "px"; set(q.tg, a, `translateX(${(1 - a) * -2 * U}px)`); });
    } };
  };

  // CHỮ BAY QUA MÁY QUAY: các từ khoá xếp trên elip, bay từ xa tới sát ống kính rồi lướt qua. p.words[], p.speed, p.kicker
  M.flying_words = (root, p, sc) => {
    sourceLine(root, p); // luật Q1: số liệu / khẳng định luôn kèm nguồn
    const k = kick(root, p, sc), ws = p.words || [], n = ws.length, R = rnd(5);
    const stg = el("div", null, null, root); stg.style.cssText = `position:absolute;inset:0;perspective:${W * .7}px;overflow:hidden`;
    const items = ws.map((w, i) => { const a = i * 2.39996, d = el("div", null, mark(w), stg); d.style.cssText = `position:absolute;left:50%;top:50%;font-weight:900;text-transform:uppercase;white-space:nowrap;font-size:calc(var(--u)*${PORT() ? 6 : 5.4});color:${i % 3 ? "#fff" : "var(--accent2)"}`;
      return { d, x: Math.cos(a) * W * .32, y: Math.sin(a) * H * .26, ph: i / n + R() * .05 }; });
    const sp = p.speed || .22;
    return { update(lt) { kickUp(k, lt); for (const q of items) { const f = (lt * sp + q.ph) % 1, z = lerp(-W * 2.2, W * .62, E.in ? E.in(f) : f * f);
      q.d.style.transform = `translate(-50%,-50%) translate3d(${q.x}px,${q.y}px,${z}px)`; q.d.style.opacity = clamp(f * 5) * (1 - clamp((f - .86) * 7)) * clamp(lt * 2); q.d.style.filter = `blur(${f > .8 ? (f - .8) * 30 : 0}px)`; } } };
  };

  // ---------------- KEYWORD EFFECTS (logic từ khoá) ----------------
  const K = {};
  function kwBox(kw) { const b = el("div", null, null, kwRoot); const pos = kw.pos || "center";
    b.style.cssText = `position:absolute;${kw.x != null ? `left:${kw.x - (kw.w || 28) / 2}%;width:${kw.w || 28}%` : "left:0;right:0;padding:0 4%"};text-align:center;top:${typeof pos === "number" ? pos + "%" : pos === "upper" ? "22%" : pos === "lower" ? "62%" : "42%"};transform-origin:50% 50%`;
    if (kw.sub) { const s = el("div", null, mark(kw.sub), b); s.style.cssText = V2 ? "display:inline-block;font-weight:800;text-transform:uppercase;letter-spacing:.16em;font-size:calc(var(--u)*2.8);color:#111;background:var(--accent2);padding:.25em .7em;border-radius:.35em;margin-bottom:.9em;box-shadow:0 .3em 1em rgba(0,0,0,.5)" : "font-family:PFD;font-style:italic;font-size:calc(var(--u)*3.2);color:#fff;text-shadow:0 2px 8px #000;margin-bottom:.1em"; }
    const m = el("div", "headline", mark(kw.text), b); m.style.fontSize = `calc(var(--u)*${kw.size || 11})`; if (V2 && kw.sub) m.style.marginTop = ".22em"; return { b, m }; }
  const life = (t, kw) => { const a = kw.at, hold = Math.max(.5, Math.min(kw.hold || 1.9, (kw._end != null ? kw._end : 1e9) - a - .35)); return { k: prog(t, a, .4), out: prog(t, a + hold, .3), on: t >= a - .05 && t <= a + hold + .3 }; };
  K.stamp_slam = kw => { const { b, m } = kwBox(kw); m.style.cssText += ";display:inline-block;background:" + (kw.color || "#b3151c") + ";padding:.12em .4em;clip-path:polygon(0 6%,8% 0,22% 5%,40% 0,58% 6%,76% 0,94% 4%,100% 2%,98% 95%,82% 100%,64% 94%,45% 100%,26% 95%,9% 100%,0 94%)";
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); const s = prog(t, kw.at, .28); set(b, clamp(s * 5) * (1 - out), `scale(${lerp(2.6, 1, E.slam(s))}) rotate(-3deg)`); return s > .5 && s < 1 ? 1 : 0; }; };
  K.giftbox = kw => { const { b, m } = kwBox(kw); const box = el("div", null, "🎁", b); box.style.cssText = "font-size:calc(var(--u)*16);line-height:1;position:absolute;left:0;right:0;top:-.2em"; m.style.color = kw.color || "var(--accent2)";
    const conf = []; const R = rnd(3); for (let i = 0; i < 26; i++) { const c = el("div", null, null, b); c.style.cssText = `position:absolute;left:50%;top:40%;width:${8 + R() * 10}px;height:${6 + R() * 6}px;background:${["#F5E14A", "#F0784A", "#fff", "#4ade80"][i % 4]}`; conf.push([c, R() * 2 - 1, -R() * 1.2 - .2, R() * 720]); }
    return t => { const { on, out } = life(t, kw); if (!on) return set(b, 0); set(b, 1 - out);
      const sh = prog(t, kw.at, .45); box.style.transform = `rotate(${Math.sin(sh * 40) * 8 * (1 - sh)}deg) scale(${lerp(.6, 1, E.back(clamp(sh * 2)))})`; box.style.opacity = 1 - prog(t, kw.at + .45, .2);
      const o = prog(t, kw.at + .45, .5); set(m, clamp(o * 3), `translateY(${(1 - E.back(o)) * 120}px) scale(${lerp(.3, 1, E.back(o))})`);
      conf.forEach(([c, vx, vy, r]) => { const q = prog(t, kw.at + .45, 1.2); c.style.opacity = q > 0 && q < 1 ? 1 - q : 0; c.style.transform = `translate(${vx * 500 * q}px,${(vy * 600 * q + 900 * q * q)}px) rotate(${r * q}deg)`; });
      return sh > 0 && sh < 1 ? .35 : 0; }; };
  K.bounce = kw => { const { b, m } = kwBox(kw); m.style.color = kw.color || "var(--accent2)"; m.style.webkitTextStroke = "calc(var(--u)*.35) #111"; m.style.paintOrder = "stroke fill";
    return t => { const { on, out } = life(t, kw); if (!on) return set(b, 0); const k = prog(t, kw.at, .7); set(b, clamp(k * 4) * (1 - out), `scale(${lerp(.2, 1, E.elastic(k))}) rotate(${Math.sin(t * 9) * 3}deg)`); return 0; }; };
  K.fade = kw => { const { b } = kwBox(kw); return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, E.out(k) * (1 - out), `translateY(${(1 - E.out(k)) * 20}px)`); b.style.filter = `blur(${(1 - k) * 8}px)`; return 0; }; };
  K.typewriter = kw => { const { b, m } = kwBox(kw); const full = kw.text; m.style.fontFamily = "BVP"; m.style.fontStyle = "normal";
    return t => { const { on, out } = life(t, kw); if (!on) return set(b, 0); const n = Math.floor(prog(t, kw.at, Math.max(.5, full.length * .045)) * full.length); m.innerHTML = mark(full.slice(0, n)) + (Math.floor(t * 3) % 2 ? "▌" : ""); set(b, 1 - out); return 0; }; };
  K.rise = kw => { const { b, m } = kwBox(kw); m.style.color = kw.color || "#4ade80"; m.innerHTML = "▲ " + m.innerHTML;
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, clamp(k * 3) * (1 - out), `translateY(${(1 - E.back(k)) * 220}px)`); return 0; }; };
  K.crack = kw => { const { b, m } = kwBox(kw); m.style.color = kw.color || "#ef4444";
    return t => { const { on, out } = life(t, kw); if (!on) return set(b, 0); const k = prog(t, kw.at, .3), f = prog(t, kw.at + 1.1, .6); set(b, clamp(k * 4) * (1 - out), `translateY(${E.inout(f) * 300}px) rotate(${f * 14}deg) scale(${lerp(1.5, 1, E.slam(k))})`); return k > .5 && k < 1 ? .6 : 0; }; };
  K.warning = kw => { const { b, m } = kwBox(kw); m.style.cssText += ";display:inline-block;color:#111;padding:.15em .5em;background:repeating-linear-gradient(-45deg,#F5E14A 0 .35em,#111 .35em .7em);-webkit-text-stroke:0";
    const inner = m.innerHTML; m.innerHTML = `<span style="background:#F5E14A;padding:0 .2em">${inner}</span>`;
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, clamp(k * 4) * (1 - out) * (Math.floor(t * 8) % 2 ? 1 : .75), `scale(${lerp(1.4, 1, E.slam(k))})`); return k < 1 ? .4 : 0; }; };
  K.redact = kw => { const { b, m } = kwBox(kw); m.style.position = "relative"; const bar = el("div", null, null, m); bar.style.cssText = "position:absolute;inset:-.05em -.1em;background:#000;transform-origin:100% 50%";
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, clamp(k * 4) * (1 - out)); bar.style.transform = `scaleX(${1 - E.inout(prog(t, kw.at + .35, .7))})`; return 0; }; };
  K.speed = kw => { const { b } = kwBox(kw); return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, clamp(k * 3) * (1 - out), `translateX(${(1 - E.out(k)) * -900}px) skewX(${(1 - E.out(k)) * -20}deg)`); b.style.filter = `blur(${(1 - k) * 18}px)`; return 0; }; };
  K.zoom_big = kw => { const { b } = kwBox(kw); return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); set(b, clamp(k * 3) * (1 - out), `scale(${lerp(.1, 1, E.out(k))})`); return 0; }; };
  K.year_roll = kw => { const { b, m } = kwBox(kw); m.style.fontFamily = "OSW"; m.style.fontWeight = 700; m.style.fontStyle = "normal";
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); const r = E.inout(prog(t, kw.at + .15, kw.roll || 1.1)); const y = Math.round(lerp(kw.from, kw.to, r));
      m.innerHTML = `<span style="color:#fff">${kw.from}</span><span style="color:var(--accent2);margin:0 .18em">→</span><span style="color:var(--accent2);text-shadow:0 0 .4em rgba(250,204,21,.6)">${y}</span>`;
      set(b, clamp(k * 3) * (1 - out), `scale(${lerp(1.3, 1, E.out(k))})`); b.style.filter = `blur(${(1 - clamp(k * 2)) * 10}px)`; return r > .97 && r < 1 ? .35 : 0; }; };
  K.count = kw => { const { b, m } = kwBox(kw); m.classList.add("big"); m.style.fontFamily = "OSW";
    return t => { const { k, out, on } = life(t, kw); if (!on) return set(b, 0); m.textContent = (kw.prefix || "") + fmtNum(lerp(0, kw.value || 0, E.out(prog(t, kw.at, .9))), kw.decimals) + (kw.unit || ""); set(b, clamp(k * 3) * (1 - out), `scale(${lerp(.7, 1, E.back(k))})`); return 0; }; };

  // ---------------- CALLOUTS (tên riêng → logo chính thức / ảnh thật, bật đúng lúc đọc tên) ----------------
  // d.callouts: [{items:[{logo|photo, name, at, source}], pos:"tl|tr|top|center|bl|br"|{x,y}, hold}] (1 món thì để logo/photo/name ngay trong nhóm)
  let coRoot = null; const CO = [];
  function buildCallouts(d) {
    for (const g0 of d.callouts || []) {
      const g = g0.items ? g0 : { ...g0, items: [g0] }; const pos = g.pos || "top";
      const box = el("div", "co-row", null, coRoot); const P = { tl: [6, 13, 0], tr: [94, 13, 2], top: [50, 13, 1], center: [50, 36, 1], bl: [6, 56, 0], br: [94, 56, 2] }[pos] || [pos.x || 50, pos.y || 13, 1];
      box.style.cssText = `position:absolute;top:${P[1]}%;${P[2] === 0 ? `left:${P[0]}%` : P[2] === 2 ? `right:${100 - P[0]}%` : `left:${P[0]}%;transform:translateX(-50%)`};display:flex;gap:${2.4 * U}px;align-items:flex-start;display:none`;
      const its = g.items.map(it => {
        const c = el("div", "co-card qabox", null, box); c.dataset.qname = it.name || "logo"; c.style.cssText = `display:flex;flex-direction:column;align-items:center;gap:${1 * U}px;transform-origin:50% 60%`;
        const tile = el("div", null, null, c); const ph = !!it.photo;
        tile.style.cssText = ph ? `width:${(g.size || 22) * U}px;height:${(g.size || 22) * (g.ratio || .72) * U}px;border-radius:${1.2 * U}px;overflow:hidden;border:${.45 * U}px solid #fff;box-shadow:0 ${1.5 * U}px ${4 * U}px rgba(0,0,0,.6);background:#111`
          : `height:${(g.size || 9) * U}px;min-width:${(g.size || 9) * U}px;box-sizing:border-box;padding:${1.1 * U}px ${1.6 * U}px;border-radius:${1.8 * U}px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 ${1.5 * U}px ${4 * U}px rgba(0,0,0,.55)`;
        if (!it.photo && !it.logo) { tile.textContent = it.name || ""; tile.style.cssText += `;font-family:OSW;font-weight:700;font-size:${(g.size || 9) * .42 * U}px;color:#111;letter-spacing:.04em;text-transform:uppercase`; } else { const im = img(it.photo || it.logo); im.style.cssText = ph ? "width:100%;height:100%;object-fit:cover;display:block" : `max-height:100%;max-width:${(g.size || 9) * 2.6 * U}px;object-fit:contain;display:block`; tile.appendChild(im); }
        let nm = null, bar = null; if (it.name && (it.logo || it.photo)) { nm = el("div", null, esc(it.name), c); nm.style.cssText = `position:relative;font-weight:900;font-size:calc(var(--u)*${g.name_size || 2.9});color:#fff;white-space:nowrap;letter-spacing:.02em;text-shadow:0 2px 8px #000,0 0 .6em rgba(250,204,21,.55);padding:.05em .35em`;
          bar = el("div", null, null, nm); bar.style.cssText = `position:absolute;left:0;right:0;bottom:-.12em;height:.16em;border-radius:.1em;background:var(--accent2);box-shadow:0 0 .6em var(--accent2);transform-origin:0 50%`; }
        if (it.source) { const s = el("div", "co-src", (ph ? "Ảnh: " : "Nguồn: ") + esc(it.source), c); s.style.cssText = "margin-top:calc(var(--u)*.6);font-size:calc(var(--u)*1.5);color:rgba(255,255,255,.75);text-shadow:0 1px 4px #000;white-space:nowrap"; }
        return { c, tile, nm, bar, at: it.at != null ? it.at : d.start + .3 }; });
      const end = (g.until != null ? g.until : g.until_at != null ? g.until_at : Math.max(...its.map(x => x.at)) + (g.hold || 2.6));
      CO.push({ d, box, its, end });
    }
  }
  function calloutsAt(t) {
    for (const { d, box, its, end } of CO) {
      const on = t >= Math.min(...its.map(x => x.at)) - .05 && t <= end + .35 && t >= d.start - .05 && t < d.end + .05; box.style.display = on ? "flex" : "none"; if (!on) continue;
      const out = prog(t, Math.min(end, d.end - .3), .3);
      for (const x of its) { const k = prog(t, x.at, .5); const vis = t >= x.at - .02;
        x.c.style.display = vis ? "flex" : "none"; if (!vis) continue;
        set(x.c, clamp(k * 3) * (1 - out), `translateY(${(1 - E.back(k)) * 3 * U - out * 2 * U}px) scale(${lerp(.35, 1, E.back(k))}) rotate(${(1 - E.out(k)) * -8}deg)`);
        x.tile.style.outline = k < 1 ? `${.35 * U * (1 - k)}px solid rgba(250,204,21,${1 - k})` : "none"; x.tile.style.outlineOffset = `${(.4 + k * 1.6) * U}px`;
        if (x.bar) x.bar.style.transform = `scaleX(${E.out(prog(t, x.at + .25, .45))})`; }
    }
  }

  // ---------------- SUBTITLES ----------------
  let SUBS = [];
  function buildSubs() {
    const mode = (TL.profile || {}).subtitle || "story_pop_compact";
    subsEl.style.bottom = ((TL.profile || {}).sub_bottom != null ? TL.profile.sub_bottom : (H > W ? 15 : 7)) + "%";
    const fs = (TL.profile || {}).sub_size || (mode === "sentence_small" ? (H > W ? 3.0 : 2.4) : (H > W ? 4.2 : (V2 ? 4.4 : 3.2))); // v2 ngang: sub ≥4.4% chiều cao, đọc được trên điện thoại
    SUBS = (TL.subs || []).map(s => { const d = el("div", "ln", null, subsEl); d.style.fontSize = `calc(var(--u)*${fs})`; d.style.display = "none";
      d.style.textShadow = "0 2px 6px rgba(0,0,0,.9),0 0 2px #000"; if (mode === "sentence_small") d.style.background = "rgba(0,0,0,.35)";
      const ws = (s.words || []).map(w => { const e = el("span", "w", esc(w.text), d); return { e, w }; }); return { d, s, ws, mode }; });
  }
  function subsAt(t) {
    for (const { d, s, ws, mode } of SUBS) { const on = t >= s.start - .05 && t <= s.end + .15; d.style.display = on ? "inline-block" : "none"; if (!on) continue;
      for (const { e, w } of ws) { if (mode === "sentence_small") { e.style.opacity = 1; e.style.color = "#fff"; continue; }
        const said = t >= w.start - .03; const act = t >= w.start - .03 && t < w.end + .05; const k = prog(t, w.start - .05, .15);
        e.style.opacity = said ? clamp(.25 + k) : .0; e.style.color = act ? "var(--accent2)" : "#fff"; e.style.transform = `translateY(${(1 - E.out(k)) * 8}px) scale(${act ? 1.06 : 1})`; } }
  }

  // ---------------- TRANSITIONS ----------------
  function transIn(sc, t) { // returns {op, tr, blur, flash}
    const d = sc.d, kind = d.transition_in || "cut", k = prog(t, d.start, .38), e = E.out(k);
    if (k >= 1 || kind === "cut") return { op: 1, tr: "", blur: 0, flash: 0 };
    if (kind === "fade") return { op: e, tr: "", blur: 0, flash: 0 };
    if (kind === "whip") return { op: clamp(k * 3), tr: `translateX(${(1 - e) * W * .45}px)`, blur: (1 - e) * 26, flash: 0 };
    if (kind === "zoom") return { op: clamp(k * 3), tr: `scale(${lerp(1.35, 1, e)})`, blur: (1 - e) * 20, flash: 0 };
    if (kind === "flash" || kind === "flash_red") return { op: 1, tr: `scale(${lerp(1.08, 1, e)})`, blur: 0, flash: (1 - k) * .9, red: kind === "flash_red" };
    if (kind === "slam") return { op: 1, tr: `scale(${lerp(1.25, 1, E.slam(k))})`, blur: (1 - k) * 8, flash: (1 - k) * .4 };
    if (kind === "pop") return { op: clamp(k * 4), tr: `scale(${lerp(.6, 1, E.elastic(k))}) rotate(${(1 - k) * -6}deg)`, blur: 0, flash: 0 };
    if (kind === "black") return { op: clamp((k - .4) * 2), tr: "", blur: 0, flash: 0 };
    return { op: e, tr: "", blur: 0, flash: 0 };
  }

  // ---------------- init / render ----------------
  function feather(src) { // ảnh vệ tinh: mờ dần 12% mép để các mức zoom hoà vào nhau (hết lộ khung chữ nhật khi bay)
    if (FEATH[src]) return FEATH[src]; const im = IMGS[src]; const w = im.naturalWidth, h = im.naturalHeight; const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d");
    x.drawImage(im, 0, 0); x.globalCompositeOperation = "destination-in"; const f = .12;
    for (const [a, b] of [[w, 0], [0, h]]) { const g = x.createLinearGradient(0, 0, a, b); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(f, "#000"); g.addColorStop(1 - f, "#000"); g.addColorStop(1, "rgba(0,0,0,0)"); x.fillStyle = g; x.fillRect(0, 0, w, h); }
    c.complete = true; c.naturalWidth = w; c.naturalHeight = h; return (FEATH[src] = c); }
  async function loadImg(src) { return new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(i); i.src = src; IMGS[src] = i; }); }
  window.init = async function (tl) {
    TL = tl; W = tl.W; H = tl.H; U = Math.min(W, H) / 100; ICON = tl.icon_base || ""; V2 = (tl.design || "v1") === "v2"; GEO = tl.geo || {};
    stage = document.getElementById("stage"); stage.style.width = W + "px"; stage.style.height = H + "px"; if (V2) stage.classList.add("v2"); if (V2 && W > H) stage.classList.add("land");
    const btag = (tl.brand || {}).tag; if (V2 && btag) { const bt = document.getElementById("brandtag"); bt.style.display = "flex"; bt.lastChild.textContent = btag; }
    if (tl.overlay_mode) { document.documentElement.style.background = "transparent"; document.body.style.background = "transparent"; }
    const b = tl.brand || {}; const st = stage.style;
    st.setProperty("--u", U + "px"); st.setProperty("--accent", b.accent || "#F0784A"); st.setProperty("--accent2", b.accent2 || "#F5E14A");
    st.setProperty("--bgc", b.bg || "#141519"); st.setProperty("--glow", b.glow || "rgba(240,90,40,.55)");
    scenesRoot = document.getElementById("scenes"); subsEl = document.getElementById("subs"); kwRoot = document.getElementById("kw");
    coRoot = document.getElementById("co"); flashEl = document.getElementById("flash"); grainEl = document.getElementById("grain"); vigEl = document.getElementById("vig");
    const pend = [];
    const flags = []; JSON.stringify(tl.scenes, (k, v) => { if (k === "flag" && typeof v === "string") flags.push(v); return v; }); flags.forEach(f => pend.push(loadImg(f)));
    const nested = new Set(); JSON.stringify(tl.scenes, (k, v) => { if (k === "photo" && typeof v === "string" && !IMGS[v]) nested.add(v); return v; }); nested.forEach(f => pend.push(loadImg(f)));
    for (const s of tl.scenes) { const p = s.p || {}; for (const k of ["photo"]) if (p[k]) pend.push(loadImg(p[k])); (p.levels || []).forEach(L => pend.push(loadImg(L.file)));
      for (const o of [p.left, p.right, p.before, p.after]) if (o && o.photo) pend.push(loadImg(o.photo)); if (p.bg_photo) pend.push(loadImg(p.bg_photo));  for (const g of s.callouts || []) for (const it of (g.items || [g])) if (it.logo || it.photo) pend.push(loadImg(it.logo || it.photo)); }
    if (tl.globe) { const gi = await loadImg(tl.globe); const c = document.createElement("canvas"); c.width = gi.naturalWidth; c.height = gi.naturalHeight; const x = c.getContext("2d"); x.drawImage(gi, 0, 0); GLOBE = { w: c.width, h: c.height, data: x.getImageData(0, 0, c.width, c.height).data }; }
    await Promise.all(pend); await document.fonts.ready;
    for (const d of tl.scenes) {
      const root = el("div", "scene th-" + (d.theme || "dark_glow"), null, scenesRoot); const cam = el("div", "cam", null, root);
      el("div", "bg", null, cam);
      const P = d.p || {}; let bgm = null;
      if (P.bg_photo || P.bg_video) {
        if (P.bg_video) { bgm = el("video", null, null, cam); bgm.src = P.bg_video; bgm.muted = true; bgm.preload = "auto"; VIDS.push(bgm); bgm._d = d; bgm._rate = P.bg_rate || 1; bgm._off = P.bg_start || 0; }
        else { bgm = img(P.bg_photo); cam.appendChild(bgm); }
        bgm.style.cssText = `position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(${P.bg_dim != null ? P.bg_dim : .42}) saturate(.9)${P.bg_blur ? ` blur(${P.bg_blur}px)` : ""}`;
        const ov = el("div", null, null, cam); ov.style.cssText = "position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.1) 40%,rgba(0,0,0,.25) 70%,rgba(0,0,0,.8) 100%)";
        if (P.bg_source) { const s = el("div", "bgsrc", "Ảnh: " + esc(P.bg_source), cam); s.style.cssText = "position:absolute;right:calc(var(--u)*4);top:calc(var(--u)*4);font-size:calc(var(--u)*1.6);color:rgba(255,255,255,.75);z-index:6"; }
      }
      if ((d.theme || "dark_glow") === "dark_glow" && !P.noframe) el("div", "frame", null, cam);
      const f = M[d.module] || M.title; const mod = f(cam, d.p || {}, d);
      const kws = (d.keywords || []).map(kw => { kw._end = d.end; return (K[kw.effect] || K.fade)(kw); });
      S.push({ d, root, cam, mod, kws, bgm }); buildCallouts(d);
    }
    await Promise.all(VIDS.map(v => v.readyState >= 1 ? 0 : new Promise(r => { v.onloadedmetadata = r; v.onerror = r; setTimeout(r, 8000); })));
    if (tl.header) {
      const hd = el("div", null, null, stage); const hp = tl.header;
      hd.style.cssText = `position:absolute;left:0;right:0;top:${hp.y != null ? hp.y : 22}%;text-align:center;z-index:26;pointer-events:none`;
      const a = el("div", "headline", esc(hp.top || ""), hd); a.style.cssText += `;font-size:calc(var(--u)*${hp.size || 6.4});font-style:normal;letter-spacing:.01em`;
      const b = el("div", "headline", esc(hp.accent || ""), hd); b.style.cssText += `;font-size:calc(var(--u)*${hp.size || 6.4});font-style:normal;color:var(--accent2)`;
      HEADER = hd;
    }
    buildSubs();
    return { scenes: S.length };
  };
  window.renderAtAsync = async function (t) {
    const waits = [];
    for (const v of VIDS) { const d = v._d; if (t < d.start - .05 || t > d.end + .05) continue;
      const dur = v.duration || 1; let ct = v._map ? v._map(t) : v._off + Math.max(0, t - d.start) * v._rate; if (ct > dur - .05) ct = ct % dur;
      if (Math.abs(v.currentTime - ct) > .001) waits.push(new Promise(r => { const f = () => { v.removeEventListener("seeked", f); r(); }; v.addEventListener("seeked", f); v.currentTime = ct; setTimeout(r, 1500); })); }
    await Promise.all(waits);
    if (waits.length) await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); // chờ compositor vẽ xong khung video vừa tua, tránh chụp hụt 1 khung
    window.renderAt(t);
  };
  window.renderAt = function (t) {
    let flash = 0, red = false, shakeAmp = 0, mood = MOODS.neutral;
    const kickOf = new Map(); for (const sc of S) { let k = 0; for (const f of sc.kws) k = Math.max(k, f(t) || 0); kickOf.set(sc, k); }
    for (const sc of S) { const d = sc.d; const on = t >= d.start - .001 && t < d.end + .001; sc.root.style.display = on ? "block" : "none"; if (!on) continue;
      mood = MOODS[d.mood] || MOODS[(TL.profile || {}).mood] || MOODS.neutral;
      const lt = t - d.start, dur = d.end - d.start; sc.mod.update(lt, dur, t);
      const push = d.camera === "static" ? 1 : lerp(1, d.camera === "push_fast" ? 1.09 : 1.04, lt / Math.max(dur, 1));
      const tr = transIn(sc, t); flash = Math.max(flash, tr.flash || 0); red = red || tr.red;
      sc.root.style.opacity = tr.op; sc.root.style.transform = tr.tr; sc.root.style.filter = (mood.filter || "") + (tr.blur ? ` blur(${tr.blur}px)` : "");
      const kick = kickOf.get(sc) || 0;
      shakeAmp = mood.shake + kick * 6;
      const sx = shakeAmp ? (Math.sin(t * 53) + Math.sin(t * 31)) * shakeAmp : 0, sy = shakeAmp ? (Math.cos(t * 47) + Math.sin(t * 23)) * shakeAmp : 0;
      sc.cam.style.transform = `translate(${sx}px,${sy}px) scale(${push})`;
      if (sc.bgm && !sc.d.p.bg_video) sc.bgm.style.transform = `scale(${lerp(1.04, 1.14, lt / Math.max(dur, 1))}) translateX(${lerp(-1, 1, lt / Math.max(dur, 1)) * 1.5}%)`;
    }
    kwRoot.style.transform = shakeAmp ? `translate(${Math.sin(t * 61) * shakeAmp * .6}px,${Math.cos(t * 43) * shakeAmp * .6}px)` : "";
    flashEl.style.opacity = flash; flashEl.style.background = red ? "#c0141b" : "#fff";
    grainEl.style.opacity = mood.grain; grainEl.style.transform = `translate(${(Math.floor(t * 24) * 37) % 100 - 50}px,${(Math.floor(t * 24) * 53) % 100 - 50}px)`;
    vigEl.style.background = `radial-gradient(ellipse at center,transparent 50%,${mood.vig} 100%)`;
    if (HEADER) HEADER.style.opacity = E.out(prog(t, 0, .6));
    subsAt(t); calloutsAt(t);
    if (V2) document.getElementById("prog").style.width = (t / TL.duration * 100) + "%";
  };
})();
