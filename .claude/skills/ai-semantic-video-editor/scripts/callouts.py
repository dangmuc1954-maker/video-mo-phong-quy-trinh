"""Lớp CALLOUT: nhấn mạnh tên riêng / chỉ đích danh / liệt kê bằng hình, ghép lên lớp chữ trong suốt.

Quy tắc chọn (references/bo-nao-dao-dien.md mục 4b):
  - phần mềm, app, sản phẩm số được gọi đích danh  → "logo"   (icon/logo chính thức của nó)
  - nhiều phần mềm liền nhau                          → "logo_row" (cộng dồn từng logo đúng lúc đọc)
  - danh xưng (tổ chức, người, địa danh, sự kiện)     → "photo"  (ảnh/video thật, có ghi nguồn)
  - liệt kê DANH TỪ / sự vật (bò, ngựa…; trung tâm dữ liệu, chip…) → hình TỪNG THỨ, hiện đúng lúc đọc:
      "photo_row" (ảnh thật) · "sticker_row" (nhãn dán: PNG nền trong suốt, viền trắng, nảy vào)
      · "logo_row" (icon/logo) — mỗi item một trong "photo" | "sticker" | "logo"
  - liệt kê HOẠT ĐỘNG / ý không vẽ được bằng hình    → "checklist" (bảng gradient, số 01→tick, mục đang đọc phát sáng)

storyboard["callouts"] = [
  {"type": "logo", "at": 26.5, "dur": 3.0, "logo": "assets/logos/claude.png", "name": "Claude", "sub": "Anthropic"},
  {"type": "logo_row", "end": 66.5, "items": [{"logo": "...", "name": "Veo", "at": 61.1}, ...]},
  {"type": "photo", "at": 81.4, "dur": 2.9, "photo": "assets/photos/x.jpg", "name": "...", "sub": "...", "credit": "Ảnh: ..."},
  {"type": "checklist", "at": 31.7, "end": 35.2, "title": "...", "items": ["...", ...], "times": [31.7, 32.9, 34.1]}
]  # tuỳ chọn mỗi mục: "y" = tâm dọc theo tỉ lệ khung (mặc định 0.2 — vùng trên, tránh chữ nhấn giữa và phụ đề dưới)

Dùng:
  python callouts.py projects/<slug>/storyboard.json                 # ghép vào narration/build/final/text_layer.mov (giữ bản gốc *.orig.mov)
  python callouts.py projects/<slug>/storyboard.json --stills 27,62   # ảnh kiểm tra: callout vẽ lên video 2-xuat
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mograph import SS, Ctx, card, ease_back, ease_out, t_checklist  # noqa: E402

FPS = 30
IN, OUT = 0.35, 0.3  # thời gian vào / ra


def _fade(t, dur):
    """hệ số hiện (0..1) theo vào/ra"""
    return min(ease_out(t / IN), ease_out((dur - t) / OUT))


def _tile(ctx, path, size):
    """logo đặt trên ô trắng bo góc (logo đen vẫn rõ trên nền tối)"""
    s = ctx.s(size)
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.24), fill=(255, 255, 255, 255))
    lg = Image.open(path).convert("RGBA")
    bb = lg.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()   # cắt sát phần có hình
    if bb:
        lg = lg.crop(bb)
    if max(lg.size) < s:                                                       # logo nhỏ thì phóng lên cho đầy ô
        k = s / max(lg.size)
        lg = lg.resize((int(lg.width * k), int(lg.height * k)), Image.LANCZOS)
    pad = int(s * 0.16)
    lg.thumbnail((s - 2 * pad, s - 2 * pad), Image.LANCZOS)
    tile.alpha_composite(lg, ((s - lg.width) // 2, (s - lg.height) // 2))
    return tile


def _photo_tile(ctx, path, size):
    """ảnh thật cắt vuông vừa ô, bo góc, viền màu nhấn"""
    s = ctx.s(size)
    src = Image.open(path).convert("RGB")
    k = max(s / src.width, s / src.height)
    src = src.resize((max(s, int(src.width * k)), max(s, int(src.height * k))), Image.LANCZOS)
    src = src.crop(((src.width - s) // 2, (src.height - s) // 2, (src.width + s) // 2, (src.height + s) // 2))
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.16), fill=255)
    tile.paste(src, (0, 0), mask)
    ImageDraw.Draw(tile).rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * 0.16), outline=ctx.acc + (255,), width=ctx.s(5))
    return tile


def _sticker_tile(ctx, path, size):
    """nhãn dán: hình PNG nền trong suốt (con bò, con ngựa…) + viền trắng dày + bóng nhẹ, không có ô"""
    s = ctx.s(size)
    im = Image.open(path).convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if bb:
        im = im.crop(bb)
    k = (s * 0.8) / max(im.size)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    tile = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ox, oy = (s - im.width) // 2, (s - im.height) // 2
    a = Image.new("L", (s, s), 0)
    a.paste(im.getchannel("A"), (ox, oy))
    stroke = a.filter(ImageFilter.MaxFilter(max(3, (ctx.s(14) // 2) * 2 + 1)))
    shadow = stroke.filter(ImageFilter.GaussianBlur(ctx.s(8))).point(lambda v: int(v * 0.5))
    tile.paste((0, 0, 0, 255), (ctx.s(4), ctx.s(8)), shadow)
    tile.paste((255, 255, 255, 255), (0, 0), stroke)
    tile.alpha_composite(im, (ox, oy))
    return tile


def _glow(ctx, size, alpha):
    s = ctx.s(size)
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    m = int(s * 0.18)
    ImageDraw.Draw(g).rounded_rectangle((m, m, s - m, s - m), radius=int(s * 0.22), fill=ctx.acc + (alpha,))
    return g.filter(ImageFilter.GaussianBlur(ctx.s(22)))


def make_logo(ctx, c, proj):
    dur = c["dur"]
    tile = _tile(ctx, proj / c["logo"], 170)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    fname, fsub = ctx.font(76), ctx.font(40)
    tw = max(d0.textlength(c["name"], font=fname), d0.textlength(c.get("sub", ""), font=fsub))
    w = int(ctx.s(60) + tile.width + ctx.s(44) + tw + ctx.s(70))
    h = ctx.s(250)

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1))
        pulse = 0.5 + 0.5 * ease_out(min(1, t / 0.6)) * (0.75 + 0.25 * __import__("math").sin(t * 6))
        gl = _glow(ctx, 260, int(200 * pulse))
        ty = (h - tile.height) // 2
        img.alpha_composite(gl, (ctx.s(60) + tile.width // 2 - gl.width // 2, h // 2 - gl.height // 2))
        sc = 0.55 + 0.45 * ease_back(t / 0.45)
        tl = tile.resize((max(1, int(tile.width * sc)), max(1, int(tile.height * sc))), Image.LANCZOS)
        img.alpha_composite(tl, (ctx.s(60) + (tile.width - tl.width) // 2, ty + (tile.height - tl.height) // 2))
        d = ImageDraw.Draw(img)
        p = ease_out((t - 0.12) / 0.4)
        x = int(ctx.s(60) + tile.width + ctx.s(44) + (1 - p) * ctx.s(60))
        d.text((x, ctx.s(46)), c["name"], font=fname, fill=ctx.fg + (int(255 * p),))
        if c.get("sub"):
            d.text((x, ctx.s(150)), c["sub"], font=fsub, fill=ctx.fg + (int(190 * p),))
        u = ease_out((t - 0.35) / 0.45)
        if u > 0:
            uw = int(d.textlength(c["name"], font=fname) * u)
            d.rounded_rectangle((x, ctx.s(136), x + uw, ctx.s(144)), radius=ctx.s(4), fill=ctx.acc + (255,))
        return img
    return (w, h), draw


def make_logo_row(ctx, c, proj):
    items = c["items"]
    t0 = items[0]["at"]
    big = any("photo" in it or "sticker" in it for it in items)
    ts = 210 if big else 150

    def tile_of(it):
        if "photo" in it:
            return _photo_tile(ctx, proj / it["photo"], ts)
        if "sticker" in it:
            return _sticker_tile(ctx, proj / it["sticker"], ts)
        return _tile(ctx, proj / it["logo"], ts)
    tiles = [tile_of(it) for it in items]
    fname = ctx.font(40 if big else 44)
    slot = ctx.s(290 if big else 230)
    w = slot * len(items) + ctx.s(60)
    h = ctx.s(360 if big else 300)

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1), accent_bar=False)
        d = ImageDraw.Draw(img)
        for i, (it, tile) in enumerate(zip(items, tiles)):
            lt = t - (it["at"] - t0)
            if lt <= 0:
                continue
            cx = ctx.s(30) + slot * i + slot // 2
            gl = _glow(ctx, 230, int(190 * ease_out(lt / 0.5)))
            img.alpha_composite(gl, (cx - gl.width // 2, ctx.s(30) + tile.height // 2 - gl.height // 2))
            sc = 0.5 + 0.5 * ease_back(lt / 0.45)
            tl = tile.resize((max(1, int(tile.width * sc)), max(1, int(tile.height * sc))), Image.LANCZOS)
            img.alpha_composite(tl, (cx - tl.width // 2, ctx.s(30) + (tile.height - tl.height) // 2))
            p = ease_out((lt - 0.15) / 0.35)
            nw = d.textlength(it["name"], font=fname)
            d.text((cx - nw / 2, ctx.s(30) + tile.height + ctx.s(20)), it["name"], font=fname, fill=ctx.fg + (int(255 * p),))
        return img
    return (w, h), draw


def make_photo(ctx, c, proj):
    dur = c["dur"]
    pw, ph = ctx.s(900), ctx.s(520)
    src = Image.open(proj / c["photo"]).convert("RGB")
    k = max(pw / src.width, ph / src.height) * 1.12
    big = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ctx.s(30), fill=255)
    fname, fsub, fcred = ctx.font(56), ctx.font(36), ctx.font(24)
    w, h = pw + ctx.s(40), ph + ctx.s(220)

    def draw(t):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        card(img, ctx, (0, 0, w - 1, h - 1))
        z = 1 + 0.08 * min(1, t / max(dur, 0.1))            # zoom chậm (Ken Burns)
        bw, bh = int(pw * 1.0 / z * 1.12), int(ph * 1.0 / z * 1.12)
        bw, bh = min(bw, big.width), min(bh, big.height)
        crop = big.crop(((big.width - bw) // 2, (big.height - bh) // 2, (big.width + bw) // 2, (big.height + bh) // 2)).resize((pw, ph), Image.LANCZOS)
        img.paste(crop, (ctx.s(20), ctx.s(20)), mask)
        d = ImageDraw.Draw(img)
        p = ease_out((t - 0.15) / 0.4)
        y = ph + ctx.s(40)
        d.rounded_rectangle((ctx.s(36), y + ctx.s(8), ctx.s(48), y + ctx.s(118)), radius=ctx.s(6), fill=ctx.acc + (int(255 * p),))
        d.text((ctx.s(70), y), c["name"], font=ctx.fit(d, c["name"], w - ctx.s(100), 56), fill=ctx.fg + (int(255 * p),))
        if c.get("sub"):
            d.text((ctx.s(70), y + ctx.s(78)), c["sub"], font=fsub, fill=ctx.acc + (int(255 * p),))
        if c.get("credit"):
            d.text((ctx.s(70), y + ctx.s(140)), c["credit"], font=fcred, fill=ctx.fg + (int(150 * p),))
        return img
    return (w, h), draw


def make_checklist_basic(ctx, c, proj):
    data = {"title": c.get("title"), "items": c["items"], "times": c.get("times")}
    return t_checklist(ctx, data, c["end"] - c["at"], offset=c["at"])


FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _font(ctx, weight, size):
    f = FONT_DIR / f"BeVietnamPro-{weight}.ttf"
    return ImageFont.truetype(str(f), max(8, int(size * ctx.k))) if f.exists() else ctx.font(size)


def _hgrad(w, h, c1, c2, alpha=255):
    """dải màu ngang c1 → c2"""
    g = Image.linear_gradient("L").rotate(90).resize((w, h))
    a = Image.new("RGBA", (w, h), c1 + (alpha,))
    b = Image.new("RGBA", (w, h), c2 + (alpha,))
    return Image.composite(b, a, g.transpose(Image.FLIP_LEFT_RIGHT))


def _round_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def make_checklist(ctx, c, proj):
    """bảng liệt kê HOẠT ĐỘNG: khung gradient, huy hiệu số → tick, mục đang đọc phát sáng, thanh tiến độ"""
    items, n = c["items"], len(c["items"])
    rel = [max(0.2, t - c["at"]) for t in (c.get("times") or [c["at"] + 0.3 + i * 0.7 for i in range(n)])]
    dur = c["end"] - c["at"]
    cyan = (34, 211, 238)
    orange = (249, 115, 22)
    f_chip, f_title = _font(ctx, "Bold", 26), _font(ctx, "ExtraBold", 50)
    f_item, f_num = _font(ctx, "Bold", 42), _font(ctx, "ExtraBold", 30)
    W = ctx.s(920)
    pad, row_h, gap = ctx.s(40), ctx.s(96), ctx.s(16)
    head = ctx.s(170)
    H = head + n * row_h + (n - 1) * gap + ctx.s(70)
    m = ctx.s(30)  # lề cho bóng đổ
    chip = c.get("kicker") or f"{n} VIỆC"

    # nền tĩnh: bóng + khung gradient + viền gradient
    base = Image.new("RGBA", (W + 2 * m, H + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + ctx.s(14), m + W, m + H + ctx.s(14)), radius=ctx.s(40), fill=(0, 0, 0, 150))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(ctx.s(18))))
    border = _hgrad(W, H, ctx.acc, cyan)
    base.paste(border, (m, m), _round_mask(W, H, ctx.s(40)))
    bw = ctx.s(3)
    body = Image.linear_gradient("L").resize((W - 2 * bw, H - 2 * bw))
    body = Image.composite(Image.new("RGBA", body.size, (10, 16, 32, 246)), Image.new("RGBA", body.size, (17, 29, 56, 246)), body)
    base.paste(body, (m + bw, m + bw), _round_mask(W - 2 * bw, H - 2 * bw, ctx.s(38)))

    def draw(t):
        img = base.copy()
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))   # vẽ lên lớp riêng rồi phủ lên khung (vẽ thẳng lên RGBA sẽ đục thủng nền)
        d = ImageDraw.Draw(layer)
        x0, y0 = m + pad, m + ctx.s(34)
        # nhãn + tiêu đề + vạch quét
        cw = int(d.textlength(chip, font=f_chip)) + ctx.s(36)
        d.rounded_rectangle((x0, y0, x0 + cw, y0 + ctx.s(44)), radius=ctx.s(22), fill=ctx.acc + (255,))
        d.text((x0 + ctx.s(18), y0 + ctx.s(6)), chip, font=f_chip, fill=ctx.bg + (255,))
        d.text((x0, y0 + ctx.s(58)), c.get("title", ""), font=f_title, fill=(255, 255, 255, 255))
        u = ease_out((t - 0.15) / 0.6)
        if u > 0:
            uw = max(1, int((W - 2 * pad) * u))
            layer.alpha_composite(_hgrad(uw, ctx.s(5), ctx.acc, cyan), (x0, y0 + ctx.s(124)))
        shown = sum(1 for r in rel if t >= r)
        for i, txt in enumerate(items):
            p = ease_out((t - rel[i]) / 0.4)
            if p <= 0:   # hàng chờ: mờ, có số thứ tự — báo trước còn mấy mục
                q = ease_out((t - 0.25 - i * 0.08) / 0.4) * 0.9
                if q > 0:
                    y = m + head + i * (row_h + gap)
                    d.rounded_rectangle((x0, y, m + W - pad, y + row_h), radius=ctx.s(24), fill=(255, 255, 255, int(10 * q)),
                                        outline=(255, 255, 255, int(28 * q)), width=ctx.s(2))
                    r = ctx.s(30)
                    cx, cy = x0 + ctx.s(24) + r, y + row_h // 2
                    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, int(70 * q)), width=ctx.s(3))
                    num = f"{i + 1:02d}"
                    d.text((cx - d.textlength(num, font=f_num) / 2, cy - ctx.s(20)), num, font=f_num, fill=(255, 255, 255, int(90 * q)))
                continue
            active = i == shown - 1
            y = m + head + i * (row_h + gap)
            dx = int((1 - p) * ctx.s(-70))
            rx0, rx1 = x0 + dx, m + W - pad + dx
            a = int(255 * p * (1.0 if active or shown == i + 1 else 0.82))
            if active:  # mục đang đọc: phát sáng + viền vàng
                gl = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(gl).rounded_rectangle((rx0, y, rx1, y + row_h), radius=ctx.s(24), fill=ctx.acc + (int(90 * p),))
                img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(ctx.s(14))))
                d.rounded_rectangle((rx0, y, rx1, y + row_h), radius=ctx.s(24), fill=(24, 40, 78, int(250 * p)),
                                    outline=ctx.acc + (int(255 * p),), width=ctx.s(3))
            else:
                d.rounded_rectangle((rx0, y, rx1, y + row_h), radius=ctx.s(24), fill=(255, 255, 255, int(16 * p)))
            # huy hiệu: số 01 → tick
            r = ctx.s(30)
            cx, cy = rx0 + ctx.s(24) + r, y + row_h // 2
            sc = 0.6 + 0.4 * ease_back((t - rel[i]) / 0.4)
            rr = int(r * sc)
            bad = _hgrad(2 * rr, 2 * rr, ctx.acc, orange, int(255 * p))
            bm = Image.new("L", bad.size, 0)
            ImageDraw.Draw(bm).ellipse((0, 0, 2 * rr - 1, 2 * rr - 1), fill=255)
            layer.paste(bad, (cx - rr, cy - rr), bm)
            pk = ease_out((t - rel[i] - 0.45) / 0.25)
            num = f"{i + 1:02d}"
            na = max(0.0, 1 - pk * 4)          # số tắt nhanh rồi tick mới vẽ ra, không chồng nhau
            if na > 0:
                nw = d.textlength(num, font=f_num)
                d.text((cx - nw / 2, cy - ctx.s(20)), num, font=f_num, fill=ctx.bg + (int(255 * p * na),))
            pk = max(0.0, (pk - 0.25) / 0.75)
            if pk > 0:
                lw = ctx.s(6)
                p1, p2, p3 = (cx - r * .42, cy + r * .02), (cx - r * .1, cy + r * .34), (cx + r * .45, cy - r * .3)
                d.line((p1, p2), fill=ctx.bg + (int(255 * pk),), width=lw)
                d.line((p2, p3), fill=ctx.bg + (int(255 * pk),), width=lw)
            d.text((cx + r + ctx.s(26), cy - ctx.s(30)), txt, font=f_item, fill=(255, 255, 255, a))
        # thanh tiến độ
        ty = m + H - ctx.s(40)
        d.rounded_rectangle((x0, ty, m + W - pad, ty + ctx.s(8)), radius=ctx.s(4), fill=(255, 255, 255, 40))
        prog = (shown - 1 + ease_out((t - rel[shown - 1]) / 0.5)) / n if shown else 0
        if prog > 0:
            pw = max(1, int((W - 2 * pad) * min(1, prog)))
            layer.alpha_composite(_hgrad(pw, ctx.s(8), ctx.acc, cyan), (x0, ty))
        img.alpha_composite(layer)
        # trượt nhẹ xuống khi xuất hiện
        drop = int((1 - ease_out(t / 0.45)) * ctx.s(-30))
        if drop:
            out = Image.new("RGBA", img.size, (0, 0, 0, 0))
            out.alpha_composite(img, (0, drop)) if drop > 0 else out.paste(img.crop((0, -drop, img.width, img.height)), (0, 0))
            return out
        return img
    return (W + 2 * m, H + 2 * m), draw


MAKERS = {"logo": make_logo, "logo_row": make_logo_row, "photo_row": make_logo_row, "sticker_row": make_logo_row,
          "photo": make_photo, "checklist": make_checklist, "checklist_basic": make_checklist_basic}


def build(story, proj):
    ctx = Ctx({"palette": story.get("palette"), "font": story.get("font", "Roboto")})
    out = []
    for c in story.get("callouts", []):
        if c["type"] in ("logo_row", "photo_row", "sticker_row"):
            c.setdefault("at", c["items"][0]["at"])
        c.setdefault("dur", (c["end"] - c["at"]) if "end" in c else 3.0)
        (w, h), fn = MAKERS[c["type"]](ctx, c, proj)
        out.append((c, (w, h), fn))
    return out


def frame_overlay(callouts, t, W=1080, H=1920):
    """ảnh RGBA cỡ khung chứa mọi callout đang hiện ở giây t (None nếu không có)"""
    canvas = None
    for c, (w, h), fn in callouts:
        lt = t - c["at"]
        if lt < 0 or lt > c["dur"]:
            continue
        a = _fade(lt, c["dur"])
        if a <= 0:
            continue
        im = fn(lt).resize((w // SS, h // SS), Image.LANCZOS)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        if canvas is None:
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cy = int(H * c.get("y", 0.2))
        canvas.alpha_composite(im, ((W - im.width) // 2, max(0, cy - im.height // 2)))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--layer", help="lớp chữ trong suốt (mặc định narration/build/final/text_layer.mov)")
    ap.add_argument("--stills", help="giây kiểm tra, cách nhau dấu phẩy: vẽ callout lên video 2-xuat")
    a = ap.parse_args()
    sp = Path(a.storyboard).resolve()
    proj = sp.parent
    story = json.loads(sp.read_text(encoding="utf-8"))
    callouts = build(story, proj)
    print(f"{len(callouts)} callout")

    if a.stills:
        vid = next((proj / "2-xuat").glob("*.mp4"))
        qa = proj / "build" / "qa_callouts"
        qa.mkdir(parents=True, exist_ok=True)
        for s in a.stills.split(","):
            t = float(s)
            png = qa / f"t{t:06.2f}.png"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(vid), "-frames:v", "1", str(png)], check=True)
            base = Image.open(png).convert("RGBA")
            ov = frame_overlay(callouts, t, base.width, base.height)
            if ov:
                base.alpha_composite(ov)
            base.convert("RGB").save(png)
            print("  ", png)
        return

    layer = Path(a.layer) if a.layer else proj / "narration" / "build" / "final" / "text_layer.mov"
    orig = layer.with_suffix(".orig.mov")
    if not orig.exists():
        shutil.copy2(layer, orig)              # luôn dựng từ bản gốc, chạy lại không chồng 2 lần
    W, H = 1080, 1920
    tmp = layer.with_suffix(".new.mov")
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(orig), "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                            str(tmp)], stdin=subprocess.PIPE)
    n = 0
    fsz = W * H * 4
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz:
            break
        ov = frame_overlay(callouts, n / FPS, W, H)
        if ov is not None:
            fr = Image.frombuffer("RGBA", (W, H), buf, "raw", "RGBA", 0, 1).copy()
            fr.alpha_composite(ov)
            buf = fr.tobytes()
        enc.stdin.write(buf)
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    shutil.move(str(tmp), str(layer))
    print(f"Xong: {n} khung ({n / FPS:.2f}s) → {layer}  (bản gốc: {orig.name})")


if __name__ == "__main__":
    main()
