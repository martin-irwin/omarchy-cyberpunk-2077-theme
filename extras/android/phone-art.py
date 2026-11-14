#!/usr/bin/env python3
"""Night City art for phones: wallpapers and Telegram's chat background.

    phone-art.py wallpaper <out.png> <fonts-dir> <width> <height> [--title T] [--fact KEY=VALUE ...]
    phone-art.py chat <out.jpg> <width> <height>

wallpaper: the node-wallpaper look (glitch title, NODE readout, telemetry),
laid out for a phone. Tall screens (a cover screen) stack it in one column
and keep the top third clear for the lock-screen clock; wide or square ones
(a foldable's inner screen) put the NODE panel beside the title.
chat: the Cyberphone grid with scanlines, dark enough to read messages over;
build-attheme.py embeds it in the Telegram theme.

Defaults are generic (title NETRUNNER, no facts); pass your own:
    phone-art.py wallpaper findn5-cover.png ../../fonts 1116 2376 \
      --title "FIND N5" --fact "DEVICE=OPPO FIND N5" --fact "OS=ANDROID"
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (13, 11, 16); BG2 = (6, 5, 8); PANEL = (24, 13, 18); OX = (90, 30, 36)
INK = BG; CORAL = (255, 97, 89); CORAL_DIM = (163, 70, 63); CYAN = (94, 246, 255)
MUTED = (125, 68, 70); TEAL = (16, 53, 58)


def grid(W, H, S, seed, scan=True, dim=1.0):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = (y / H) * 0.6
        d.line([(0, y), (W, y)], fill=tuple(int(BG[i] * (1 - t) + BG2[i] * t) for i in range(3)))
    step = max(20, int(40 * S))
    line = tuple(int(c * dim) for c in (22, 13, 18))
    for x in range(0, W, step): d.line([(x, 0), (x, H)], fill=line)
    for y in range(0, H, step): d.line([(0, y), (W, y)], fill=line)
    if scan:
        for y in range(0, H, max(2, int(3 * S))): d.line([(0, y), (W, y)], fill=(8, 7, 10))
    rnd = random.Random(seed)
    for _ in range(int(26 * W * H / (1600 * 900))):
        x, y = rnd.randrange(0, W, step), rnd.randrange(0, H, step)
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=rnd.choice([OX, MUTED, TEAL]))
    return im


def chat(out, W, H):
    S = W / 1080
    im = grid(W, H, S, seed=77, dim=0.8)
    im.save(out, quality=88)
    print(out)


def wallpaper(out, fonts, W, H, title, facts):
    tall = H > W * 1.25
    S = (W / 900) if tall else min(W / 1600, H / 1100)
    def u(v): return int(round(v * S))
    def font(rel, size): return ImageFont.truetype(str(fonts / rel), max(8, u(size)))
    def raj(size, w="Bold"): return font(f"rajdhani/Rajdhani-{w}.ttf", size)
    def mono(size): return font("sharetechmono/ShareTechMono-Regular.ttf", size)

    seed = sum(map(ord, title))
    im = grid(W, H, S, seed)
    d = ImageDraw.Draw(im)

    def brackets(box, length=38, width=2):
        x0, y0, x1, y1 = box; L = u(length); w = max(1, u(width))
        for x, y, dx, dy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
            d.line([(x, y), (x + dx * L, y)], fill=CORAL, width=w)
            d.line([(x, y), (x, y + dy * L)], fill=CORAL, width=w)

    def tri(x, y, s, col):
        d.polygon([(x, y), (x + s, y), (x, y + s)], fill=col)

    def glitch(xy, text, fnt):
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        x, y = xy
        ld.text((x - u(6), y + u(3)), text, font=fnt, fill=CYAN + (140,))
        ld.text((x, y), text, font=fnt, fill=CORAL + (255,))
        bbox = ld.textbbox((x, y), text, font=fnt)
        rnd = random.Random(seed)
        top, bot = bbox[1], bbox[3]; span = bot - top; used = []
        for _ in range(2):
            for _try in range(20):
                sh = rnd.randint(max(12, span // 6), max(18, span // 4))
                lo = top + int(span * 0.22); hi = max(lo, bot - int(span * 0.18) - sh)
                sy = rnd.randint(lo, hi)
                if all(sy + sh < a or sy > b for a, b in used): break
            used.append((sy - 6, sy + sh + 6))
            dx = rnd.choice([-1, 1]) * rnd.randint(u(5), u(11))
            x0, x1 = max(0, bbox[0] - 30), min(W, bbox[2] + 30)
            band = layer.crop((x0, sy, x1, sy + sh))
            layer.paste((0, 0, 0, 0), (x0, sy, x1, sy + sh))
            layer.paste(band, (x0 + dx, sy))
        im.paste(layer, (0, 0), layer)
        return bbox

    def fit(text, size, max_w):
        f = raj(size)
        while d.textlength(text, font=f) > max_w and size > 40:
            size -= 8; f = raj(size)
        return f

    def node_panel(x0, y0, x1):
        row_h = u(40)
        y1 = y0 + u(46) + row_h * len(facts) + u(24)
        over = Image.new("RGBA", im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(over)
        cut = u(16)
        shape = [(x0, y0), (x1, y0), (x1, y1), (x0 + cut, y1), (x0, y1 - cut)]
        od.polygon(shape, fill=PANEL + (235,))
        im.paste(over, (0, 0), over)
        dd = ImageDraw.Draw(im)
        dd.line(shape + [shape[0]], fill=OX, width=1)
        dd.rectangle([x0, y0, x1, y0 + u(30)], fill=CORAL)
        tri(x0 + u(10), y0 + u(9), u(13), INK)
        dd.text((x0 + u(32), y0 + u(4)), "NODE", font=mono(20), fill=INK)
        dd.text((x1 - u(76), y0 + u(7)), "SYS.07", font=mono(15), fill=INK)
        fy = y0 + u(48)
        for i, (k, v) in enumerate(facts):
            dd.text((x0 + u(18), fy + i * row_h), k, font=mono(17), fill=MUTED)
            vw = dd.textlength(v, font=mono(18))
            dd.text((x1 - u(18) - vw, fy + i * row_h - u(1)), v, font=mono(18),
                    fill=CYAN if k == "TSNET" else CORAL)
            if i < len(facts) - 1:
                dd.line([(x0 + u(18), fy + i * row_h + u(30)), (x1 - u(18), fy + i * row_h + u(30))], fill=(40, 20, 26))
        tri(x1 - u(15), y1 - u(15), u(15), CORAL)
        return y1

    def telemetry(x, y, rows=4):
        rnd = random.Random(seed + 1); f = mono(15)
        for r in range(rows):
            line = "  ".join(f"{rnd.getrandbits(16):04X}" for _ in range(6))
            d.text((x, y + r * u(20)), line, font=f, fill=OX if r % 2 else MUTED)
        bx = x
        while bx < x + u(300):
            w = rnd.choice([1, 1, 2, 3])
            d.rectangle([bx, y + rows * u(20) + u(10), bx + max(1, u(w)) - 1, y + rows * u(20) + u(36)], fill=MUTED)
            bx += max(1, u(w)) + rnd.choice([2, 3, 4])
        return y + rows * u(20) + u(36)

    margin = u(64)
    if tall:
        # status bar on top, gesture bar at the bottom; clock in the top third
        brackets((u(24), u(110), W - u(24), H - u(90)))
        x = margin
        # 2:1 phones keep the top third for the lock-screen clock; shorter
        # screens (KEYone, 3:2) start higher so the panel still fits
        ty = int(H * (0.36 if H > W * 1.8 else 0.27))
        tri(x, ty - u(36), u(16), CYAN)
        d.text((x + u(26), ty - u(42)), "NIGHT CITY NET  //  NODE ONLINE", font=mono(22), fill=CORAL_DIM)
        bbox = glitch((x - u(8), ty), title, fit(title, 230, W - 2 * margin))
        d = ImageDraw.Draw(im)
        ry = bbox[3] + u(24)
        d.rectangle([x, ry - u(1), x + u(90), ry + u(2)], fill=CYAN)
        d.line([(x + u(100), ry), (W - margin - u(30), ry)], fill=CORAL, width=max(1, u(2)))
        d.text((x, ry + u(20)), "WAKE UP, NETRUNNER.", font=raj(52, "SemiBold"), fill=CYAN)
        py = ry + u(120)
        if facts:
            py = node_panel(margin, py, W - margin) + u(40)
        tele_end = telemetry(x, max(py, H - u(330)))
    else:
        brackets((u(20), u(80), W - u(20), H - u(40)))
        pw = u(420)
        px1 = W - margin; px0 = px1 - pw
        x = margin
        ty = int(H * 0.30)
        right = (px0 - u(80)) if facts else (W - margin)
        tri(x, ty - u(36), u(16), CYAN)
        d.text((x + u(26), ty - u(42)), "NIGHT CITY NET  //  NODE ONLINE", font=mono(22), fill=CORAL_DIM)
        bbox = glitch((x - u(8), ty), title, fit(title, 260, right - x))
        d = ImageDraw.Draw(im)
        ry = bbox[3] + u(24)
        d.rectangle([x, ry - u(1), x + u(90), ry + u(2)], fill=CYAN)
        d.line([(x + u(100), ry), (right, ry)], fill=CORAL, width=max(1, u(2)))
        d.text((x, ry + u(20)), "WAKE UP, NETRUNNER.", font=raj(56, "SemiBold"), fill=CYAN)
        if facts:
            node_panel(px0, int(H * 0.22), px1)
        telemetry(x, H - u(220))
    foot = f"NIGHT CITY NET  //  {title}  //  STATUS: ONLINE"
    fw = d.textlength(foot, font=mono(16))
    fy = max(H - u(150), tele_end + u(18)) if tall else H - u(80)
    d.text(((W - fw) / 2 if tall else W - margin - fw, fy), foot, font=mono(16), fill=MUTED)
    im.save(out, optimize=True)
    print(out)


def main():
    mode = sys.argv[1]
    if mode == "chat":
        chat(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
        return
    out, fonts, W, H = sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    title, facts, args = "NETRUNNER", [], sys.argv[6:]
    i = 0
    while i < len(args):
        if args[i] == "--title":
            title = args[i + 1].upper()[:20]; i += 2
        elif args[i] == "--fact":
            k, _, v = args[i + 1].partition("=")
            facts.append((k.upper()[:10], v.upper()[:26])); i += 2
        else:
            sys.exit(f"unknown argument {args[i]}")
    wallpaper(out, fonts, W, H, title, facts)


if __name__ == "__main__":
    main()
