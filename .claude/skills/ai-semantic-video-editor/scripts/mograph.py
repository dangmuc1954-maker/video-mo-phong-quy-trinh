"""Render a motion-graphic card with alpha to .mov (ProRes 4444), usable in FFmpeg and CapCut.

Templates: counter | bar_chart | checklist | callout | compare | kinetic_text

Usage:
  python mograph.py spec.json -o build/g1.mov
spec = {"template": "counter", "duration": 3.0, "data": {...},
        "width": 1080, "height": 1920, "fps": 30, "palette": ["#0F172A","#FFFFFF","#FACC15"], "font": "Roboto",
        "time_offset": 0}   # time_offset = layer start (for checklist absolute "times")
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vse_common import find_font, hex_to_rgb, need  # noqa: E402

SS = 2  # supersampling


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


class Ctx:
    def __init__(self, spec):
        self.W = spec.get("width", 1080)
        self.H = spec.get("height", 1920)
        self.k = self.W / 1080 * SS
        pal = spec.get("palette") or ["#0F172A", "#FFFFFF", "#FACC15"]
        self.bg = hex_to_rgb(pal[0])
        self.fg = hex_to_rgb(pal[1] if len(pal) > 1 else "#FFFFFF")
        self.acc = hex_to_rgb(pal[2] if len(pal) > 2 else "#FACC15")
        self.font_path = str(find_font(spec.get("font", "Roboto")))
        self._fonts = {}

    def font(self, size):
        size = max(8, int(size * self.k))
        if size not in self._fonts:
            self._fonts[size] = ImageFont.truetype(self.font_path, size)
        return self._fonts[size]

    def fit(self, draw, text, max_w, size):
        while size > 14:
            f = self.font(size)
            if draw.textlength(text, font=f) <= max_w:
                return f
            size -= 2
        return self.font(size)

    def s(self, v):
        return int(v * self.k)


def card(img, ctx, box, radius=36, alpha=225, accent_bar=True):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=ctx.s(radius), fill=ctx.bg + (alpha,))
    if accent_bar:
        d.rounded_rectangle((x0, y0 + ctx.s(28), x0 + ctx.s(12), y1 - ctx.s(28)), radius=ctx.s(6), fill=ctx.acc + (255,))


def source_note(d, ctx, data, x, y, max_w):
    note = "Minh họa giả định" if data.get("illustrative") else (f"Nguồn: {data['source']}" if data.get("source") else "")
    if note:
        d.text((x, y), note, font=ctx.fit(d, note, max_w, 26), fill=ctx.fg + (170,))


# ---------------- templates: return (size_wh, draw_fn(t) -> RGBA image) ----------------

def t_counter(ctx, data, dur):
    w, h = ctx.s(780), ctx.s(380)

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1))
        d = ImageDraw.Draw(img)
        p = ease_out((t - 0.15) / 1.1)
        v0, v1 = float(data.get("from", 0)), float(data["value"])
        val = v0 + (v1 - v0) * p
        dec = int(data.get("decimals", 0))
        num = f"{data.get('prefix', '')}{val:,.{dec}f}".replace(",", ".") if dec == 0 else f"{data.get('prefix', '')}{val:.{dec}f}".replace(".", ",")
        unit = data.get("unit", "")
        fnum = ctx.fit(d, num + unit, w - ctx.s(120), 150)
        d.text((ctx.s(60), ctx.s(40)), num, font=fnum, fill=ctx.acc + (255,))
        if unit:
            nx = ctx.s(60) + d.textlength(num, font=fnum) + ctx.s(8)
            d.text((nx, ctx.s(40)), unit, font=fnum, fill=ctx.acc + (255,))
        lab = data.get("label", "")
        d.text((ctx.s(62), ctx.s(225)), lab, font=ctx.fit(d, lab, w - ctx.s(120), 54), fill=ctx.fg + (255,))
        source_note(d, ctx, data, ctx.s(62), ctx.s(318), w - ctx.s(120))
        return img
    return (w, h), draw


def t_bar_chart(ctx, data, dur):
    items = data["items"]
    n = len(items)
    w = ctx.s(960)
    top = ctx.s(130)
    row = ctx.s(108)
    h = top + n * row + ctx.s(80)
    vmax = max(float(i["value"]) for i in items) or 1
    unit = data.get("unit", "")

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1))
        d = ImageDraw.Draw(img)
        title = data.get("title", "")
        d.text((ctx.s(56), ctx.s(40)), title, font=ctx.fit(d, title, w - ctx.s(110), 52), fill=ctx.fg + (255,))
        lab_w = ctx.s(230)
        bar_x0 = ctx.s(56) + lab_w
        bar_max = w - bar_x0 - ctx.s(170)
        for i, it in enumerate(items):
            y = top + i * row
            p = ease_out((t - 0.2 - i * 0.15) / 0.7)
            d.text((ctx.s(56), y + ctx.s(18)), str(it["label"]), font=ctx.fit(d, str(it["label"]), lab_w - ctx.s(16), 40), fill=ctx.fg + (230,))
            col = ctx.acc if it.get("highlight") else tuple(int(c * 0.75) for c in ctx.fg)
            bw = max(ctx.s(6), int(bar_max * float(it["value"]) / vmax * p))
            d.rounded_rectangle((bar_x0, y + ctx.s(14), bar_x0 + bw, y + ctx.s(78)), radius=ctx.s(14), fill=col + (255,))
            v = float(it["value"]) * p
            txt = (f"{v:.0f}" if float(it["value"]).is_integer() else f"{v:.1f}".replace(".", ",")) + unit
            d.text((bar_x0 + bw + ctx.s(16), y + ctx.s(18)), txt, font=ctx.font(42), fill=col + (int(255 * min(1, p * 2)),))
        source_note(d, ctx, data, ctx.s(56), h - ctx.s(60), w - ctx.s(110))
        return img
    return (w, h), draw


def t_checklist(ctx, data, dur, offset=0.0):
    items = data["items"]
    n = len(items)
    times = data.get("times")
    rel = [max(0.15, float(x) - offset) for x in times] if times else [0.25 + i * 0.55 for i in range(n)]
    has_title = bool(data.get("title"))
    w = ctx.s(900)
    top = ctx.s(120) if has_title else ctx.s(40)
    row = ctx.s(104)
    h = top + n * row + ctx.s(30)
    cross = data.get("icon") == "cross"

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1))
        d = ImageDraw.Draw(img)
        if has_title:
            d.text((ctx.s(56), ctx.s(36)), data["title"], font=ctx.fit(d, data["title"], w - ctx.s(110), 50), fill=ctx.acc + (255,))
        for i, txt in enumerate(items):
            p = ease_out((t - rel[i]) / 0.35)
            if p <= 0:
                continue
            a = int(255 * p)
            y = top + i * row
            dx = int((1 - p) * ctx.s(-60))
            cx, cy, r = ctx.s(90) + dx, y + ctx.s(46), ctx.s(30)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ctx.acc + (a,))
            lw = ctx.s(7)
            if cross:
                d.line((cx - r * .45, cy - r * .45, cx + r * .45, cy + r * .45), fill=ctx.bg + (a,), width=lw)
                d.line((cx - r * .45, cy + r * .45, cx + r * .45, cy - r * .45), fill=ctx.bg + (a,), width=lw)
            else:
                pk = ease_out((t - rel[i] - 0.1) / 0.25)
                p1, p2, p3 = (cx - r * .5, cy), (cx - r * .12, cy + r * .4), (cx + r * .52, cy - r * .38)
                if pk > 0:
                    m = (p1[0] + (p2[0] - p1[0]) * min(1, pk * 2), p1[1] + (p2[1] - p1[1]) * min(1, pk * 2))
                    d.line((p1, m), fill=ctx.bg + (a,), width=lw)
                if pk > 0.5:
                    q = (pk - 0.5) * 2
                    d.line((p2, (p2[0] + (p3[0] - p2[0]) * q, p2[1] + (p3[1] - p2[1]) * q)), fill=ctx.bg + (a,), width=lw)
            d.text((ctx.s(146) + dx, y + ctx.s(18)), txt, font=ctx.fit(d, txt, w - ctx.s(200), 50), fill=ctx.fg + (a,))
        return img
    return (w, h), draw


def t_callout(ctx, data, dur):
    W, H = ctx.W * SS, ctx.H * SS
    tx, ty = data.get("target", [0.6, 0.5])
    tx, ty = int(tx * W), int(ty * H)
    on_right = tx < W / 2
    cw = ctx.s(560)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    sub = data.get("sub", "")
    ch = ctx.s(150 if sub else 110)
    cx0 = (tx + ctx.s(140)) if on_right else (tx - ctx.s(140) - cw)
    cx0 = min(max(ctx.s(30), cx0), W - cw - ctx.s(30))
    cy0 = max(ctx.s(30), ty - ctx.s(260))
    anchor_pt = (cx0 if on_right else cx0 + cw, cy0 + ch // 2)
    f1 = ctx.fit(tmp, data["text"], cw - ctx.s(60), 52)
    f2 = ctx.fit(tmp, sub, cw - ctx.s(60), 36) if sub else None

    def draw(t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pr = ease_out(t / 0.3)
        pulse = 1 + 0.15 * math.sin(t * 6)
        r = int(ctx.s(26) * pr * pulse)
        d.ellipse((tx - r, ty - r, tx + r, ty + r), outline=ctx.acc + (255,), width=ctx.s(6))
        d.ellipse((tx - ctx.s(9), ty - ctx.s(9), tx + ctx.s(9), ty + ctx.s(9)), fill=ctx.acc + (int(255 * pr),))
        pl = ease_out((t - 0.15) / 0.35)
        if pl > 0:
            ex = tx + (anchor_pt[0] - tx) * pl
            ey = ty + (anchor_pt[1] - ty) * pl
            d.line((tx, ty, ex, ey), fill=ctx.acc + (255,), width=ctx.s(5))
        pc = ease_back((t - 0.4) / 0.35)
        if pc > 0:
            c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            card(c, ctx, (0, 0, cw - 1, ch - 1), radius=28)
            cd = ImageDraw.Draw(c)
            cd.text((ctx.s(36), ctx.s(22)), data["text"], font=f1, fill=ctx.fg + (255,))
            if sub:
                cd.text((ctx.s(36), ctx.s(90)), sub, font=f2, fill=ctx.acc + (255,))
            sc = max(0.05, pc)
            c = c.resize((max(1, int(cw * sc)), max(1, int(ch * sc))), Image.LANCZOS)
            img.alpha_composite(c, (int(cx0 + (cw - c.width) / 2), int(cy0 + (ch - c.height) / 2)))
        return img
    return (W, H), draw


def t_compare(ctx, data, dur):
    L, R = data["left"], data["right"]
    nlines = max(len(L.get("lines", [])), len(R.get("lines", [])), 1)
    w, h = ctx.s(980), ctx.s(150 + nlines * 80 + 40)

    def col(d, x, colw, side, color, p):
        a = int(255 * p)
        d.text((x, ctx.s(50)), side.get("title", ""), font=ctx.fit(d, side.get("title", ""), colw, 54), fill=color + (a,))
        for i, line in enumerate(side.get("lines", [])):
            pi = ease_out((p - 0.2 - i * 0.15) / 0.5) if p < 1 else 1
            d.text((x, ctx.s(150) + i * ctx.s(80)), "• " + line, font=ctx.fit(d, "• " + line, colw, 42), fill=ctx.fg + (int(255 * pi),))

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1), accent_bar=False)
        d = ImageDraw.Draw(img)
        colw = w // 2 - ctx.s(110)
        pl = ease_out((t - 0.1) / 0.5)
        pr = ease_out((t - 0.5) / 0.5)
        col(d, ctx.s(50), colw, L, tuple(int(c * 0.8) for c in ctx.fg), pl)
        col(d, w // 2 + ctx.s(60), colw, R, ctx.acc, pr)
        d.line((w // 2, ctx.s(50), w // 2, h - ctx.s(50)), fill=ctx.fg + (60,), width=ctx.s(3))
        pv = ease_back((t - 0.3) / 0.4)
        if pv > 0:
            r = int(ctx.s(52) * pv)
            cx, cy = w // 2, h // 2
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ctx.acc + (255,))
            vs = data.get("vs_text", "VS")
            f = ctx.font(40 * pv + 1)
            d.text((cx, cy), vs, font=f, fill=ctx.bg + (255,), anchor="mm")
        return img
    return (w, h), draw


def t_kinetic(ctx, data, dur):
    """Kinetic text. style: word_pop (default: words pop in one by one with bounce; emphasis line glows
    in the accent colour and gets an underline that wipes out from the centre) | pop | slide | typewriter."""
    from PIL import ImageFilter
    lines = data["lines"]
    emph = data.get("emphasis_index", 0)
    style = data.get("style", "word_pop")
    glow_on = data.get("glow", True)
    w = ctx.s(1000)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fonts = [ctx.fit(tmp, ln, w - ctx.s(170), 124 if i == emph else 90) for i, ln in enumerate(lines)]
    heights = [int(f.size * 1.32) for f in fonts]
    pad = ctx.s(50)
    h = sum(heights) + 2 * pad + ctx.s(30)

    if style == "word_pop":
        # layout: each word with its centre x, line top y, start time
        items, k, y = [], 0, pad
        line_end = []
        for i, ln in enumerate(lines):
            f = fonts[i]
            words = ln.split()
            space = tmp.textlength(" ", font=f)
            widths = [tmp.textlength(wd, font=f) for wd in words]
            total = sum(widths) + space * (len(words) - 1)
            x = (w - total) / 2
            for wd, ww in zip(words, widths):
                items.append({"t": 0.05 + k * 0.09, "word": wd, "cx": x + ww / 2, "y": y, "line": i, "f": f})
                x += ww + space
                k += 1
            line_end.append((items[-1]["t"], y, (w - total) / 2, (w + total) / 2))
            y += heights[i]
        anim_end = items[-1]["t"] + 0.9
        cache = {}

        def word_img(it, color):
            f = it["f"]
            bw = int(tmp.textlength(it["word"], font=f)) + ctx.s(40)
            bh = int(f.size * 1.45)
            im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((bw // 2, bh // 2), it["word"], font=f, fill=color + (255,), anchor="mm",
                                    stroke_width=ctx.s(6), stroke_fill=(0, 0, 0, 210))
            return im

        imgs = [word_img(it, ctx.acc if it["line"] == emph else ctx.fg) for it in items]

        def draw(t):
            if t >= anim_end and "final" in cache:
                return cache["final"].copy()
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            emph_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for it, wi in zip(items, imgs):
                q = (t - it["t"]) / 0.38
                if q <= 0:
                    continue
                sc = max(0.05, 0.35 + 0.65 * ease_back(q))
                al = min(1.0, (t - it["t"]) / 0.14)
                im = wi.resize((max(1, int(wi.width * sc)), max(1, int(wi.height * sc))), Image.LANCZOS)
                if al < 1:
                    im.putalpha(im.getchannel("A").point(lambda v, al=al: int(v * al)))
                dy = int((1 - min(1.0, q)) * ctx.s(36))
                cy = it["y"] + heights[it["line"]] // 2 + dy
                pos = (int(it["cx"] - im.width / 2), int(cy - im.height / 2))
                img.alpha_composite(im, pos)
                if it["line"] == emph:
                    emph_layer.alpha_composite(im, pos)
            # underline wipe under the emphasis line
            if 0 <= emph < len(lines):
                t_last, ly, x0, x1 = line_end[emph]
                u = ease_out((t - t_last - 0.15) / 0.4)
                if u > 0:
                    cx, half = (x0 + x1) / 2, (x1 - x0) / 2 * u
                    uy = ly + heights[emph] - ctx.s(14)
                    ImageDraw.Draw(img).rounded_rectangle((cx - half, uy, cx + half, uy + ctx.s(11)),
                                                          radius=ctx.s(6), fill=ctx.acc + (255,))
            if glow_on:
                g = emph_layer.getchannel("A").filter(ImageFilter.GaussianBlur(ctx.s(16)))
                glow = Image.new("RGBA", (w, h), ctx.acc + (0,))
                glow.putalpha(g.point(lambda v: int(min(255, v * 0.9))))
                out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                out.alpha_composite(glow)
                out.alpha_composite(img)
                img = out
            if t >= anim_end:
                cache["final"] = img.copy()
            return img
        return (w, h), draw

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        y = pad
        for i, ln in enumerate(lines):
            f = fonts[i]
            color = ctx.acc if i == emph else ctx.fg
            t0 = 0.05 + i * 0.18
            text = ln
            if style == "typewriter":
                n = int(len(ln) * min(1, max(0, (t - t0) / max(0.4, len(ln) * 0.045))))
                text = ln[:n]
                p = 1 if n else 0
            else:
                p = ease_back((t - t0) / 0.4) if style == "pop" else ease_out((t - t0) / 0.4)
            if p > 0 and text:
                layer = Image.new("RGBA", (w, heights[i]), (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                ld.text((w // 2, heights[i] // 2), text, font=f, fill=color + (255,), anchor="mm",
                        stroke_width=ctx.s(6), stroke_fill=(0, 0, 0, 200))
                if style == "pop":
                    sc = max(0.05, p)
                    layer = layer.resize((max(1, int(w * sc)), max(1, int(heights[i] * sc))), Image.LANCZOS)
                    img.alpha_composite(layer, ((w - layer.width) // 2, y + (heights[i] - layer.height) // 2))
                elif style == "slide":
                    a = layer.getchannel("A").point(lambda v, p=p: int(v * min(1, p)))
                    layer.putalpha(a)
                    img.alpha_composite(layer, (int((1 - p) * -ctx.s(200)), y))
                else:
                    img.alpha_composite(layer, (0, y))
            y += heights[i]
        return img
    return (w, h), draw


TEMPLATES = {"counter": t_counter, "bar_chart": t_bar_chart, "checklist": t_checklist,
             "callout": t_callout, "compare": t_compare, "kinetic_text": t_kinetic}


def render_mograph(spec: dict, out: Path) -> dict:
    """Render spec to out (.mov ProRes 4444 with alpha). Returns {'width','height','full_frame'}."""
    need("ffmpeg")
    tpl = spec["template"]
    if tpl not in TEMPLATES:
        sys.exit(f"Template không hợp lệ: {tpl}. Chọn: {', '.join(TEMPLATES)}")
    ctx = Ctx(spec)
    dur = float(spec.get("duration", 3.0))
    fps = int(spec.get("fps", 30))
    data = spec.get("data", {})
    if tpl == "checklist":
        (w, h), draw = t_checklist(ctx, data, dur, float(spec.get("time_offset", 0)))
    else:
        (w, h), draw = TEMPLATES[tpl](ctx, data, dur)
    ow, oh = (w // SS) // 2 * 2, (h // SS) // 2 * 2
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{ow}x{oh}",
           "-r", str(fps), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
           "-vendor", "apl0", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    full = tpl == "callout"
    nframes = max(1, int(round(dur * fps)))
    intro, outro = 0.3, 0.25
    try:
        for fi in range(nframes):
            t = fi / fps
            frame = draw(t)
            # global intro/outro (scale + fade) — callout animates itself
            a = min(1.0, ease_out(t / intro)) if not full else 1.0
            a *= min(1.0, max(0.0, (dur - t) / outro))
            if not full and tpl != "kinetic_text":
                sc = 0.88 + 0.12 * ease_out(t / intro)
                if sc < 0.999:
                    sw, sh = int(frame.width * sc), int(frame.height * sc)
                    small = frame.resize((sw, sh), Image.LANCZOS)
                    frame = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                    frame.alpha_composite(small, ((frame.width - sw) // 2, (frame.height - sh) // 2))
            frame = frame.resize((ow, oh), Image.LANCZOS)
            if a < 0.999:
                frame.putalpha(frame.getchannel("A").point(lambda v, a=a: int(v * a)))
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        sys.exit(f"FFmpeg lỗi khi render graphic: {err[-1500:]}")
    return {"width": ow, "height": oh, "full_frame": full}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default="graphic.mov")
    a = ap.parse_args()
    info = render_mograph(json.loads(Path(a.spec).read_text(encoding="utf-8")), Path(a.out))
    print(f"Đã tạo {a.out} ({info['width']}x{info['height']})")


if __name__ == "__main__":
    main()
