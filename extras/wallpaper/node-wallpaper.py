#!/usr/bin/env python3
"""Night City node wallpaper: this machine's name as the glitch title.

    node-wallpaper.py <out.png> <fonts-dir> <width> <height> [--tsnet IP] [--palette default|netrunner|samurai]

Ported from the kuroshi cyberdeck theme. Everything is generated: Rajdhani
and Share Tech Mono (SIL OFL) on drawn geometry, no CD Projekt artwork.
The NODE panel on the right is a static readout of this machine, taken when
the wallpaper is made (OS, kernel, CPU, cores, memory, display, TSNET IP).
Layout is designed on a 1600x900 grid and scaled to the target size; wider
or taller screens get more room, not stretched art.
"""
import os
import platform
import random
import re
import socket
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
FONTS = Path(sys.argv[2])
W, H = int(sys.argv[3]), int(sys.argv[4])
tsnet = ""
if "--tsnet" in sys.argv:
    tsnet = sys.argv[sys.argv.index("--tsnet") + 1]

S = min(W / 1600, H / 900)          # scale from the design grid
def u(v): return int(round(v * S))

BG = (13, 11, 16); BG2 = (6, 5, 8); PANEL = (24, 13, 18); OX = (90, 30, 36)
INK = BG; CORAL = (255, 97, 89); CORAL_DIM = (163, 70, 63); CYAN = (94, 246, 255)
YEL = (243, 230, 0); MUTED = (125, 68, 70); TEAL = (16, 53, 58)
SHADOW = CYAN                       # the title's glitch shadow

# --palette netrunner|samurai recolours the card to match that variant.
# CORAL is the main ink and CYAN the highlight whatever their actual colour.
palette = sys.argv[sys.argv.index("--palette") + 1] if "--palette" in sys.argv else "default"
if palette == "netrunner":          # the in-game PC interface: cyan on teal-black
    BG = (10, 14, 14); BG2 = (5, 8, 8); PANEL = (14, 28, 32); OX = (31, 64, 66)
    CORAL = (94, 246, 255); CORAL_DIM = (44, 156, 165); CYAN = (248, 244, 244)
    MUTED = (46, 106, 112); TEAL = (42, 20, 24); SHADOW = (63, 169, 255)
elif palette == "samurai":          # box-art yellow, cyan highlights
    BG = (12, 11, 8); BG2 = (6, 6, 4); PANEL = (26, 24, 8); OX = (74, 69, 16)
    CORAL = (243, 230, 0); CORAL_DIM = (156, 147, 0); MUTED = (107, 102, 30)
    YEL = (255, 0, 60)
elif palette != "default":
    sys.exit(f"unknown palette: {palette}")
INK = BG


def font(rel, size): return ImageFont.truetype(str(FONTS / rel), max(8, u(size)))
def raj(size, w="Bold"): return font(f"rajdhani/Rajdhani-{w}.ttf", size)
def mono(size): return font("sharetechmono/ShareTechMono-Regular.ttf", size)


# ── facts about this machine ────────────────────────────────────────────────
def read(path):
    try: return Path(path).read_text()
    except OSError: return ""

host = socket.gethostname().split(".")[0].upper()[:24] or "NODE"
os_name = re.search(r'^PRETTY_NAME="?([^"\n]+)', read("/etc/os-release"), re.M)
os_name = (os_name.group(1) if os_name else platform.system()).upper()
kernel = platform.release().split("-")[0]
cpu = re.search(r"^model name\s*:\s*(.+)$", read("/proc/cpuinfo"), re.M)
cpu = cpu.group(1) if cpu else ""
if not cpu:
    try:
        lscpu = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"^Model name:\s*(.+)$", lscpu, re.M)
        cpu = m.group(1).strip() if m else ""
        if cpu in ("", "-"):   # ARM boards and VMs often have no model name
            v = re.search(r"^Vendor ID:\s*(.+)$", lscpu, re.M)
            cpu = v.group(1).strip() if v else ""
    except Exception:
        cpu = platform.machine()
cpu = re.sub(r"\((R|TM)\)|CPU|Processor|@.*$", "", cpu, flags=re.I)
cpu = re.sub(r"\s+", " ", cpu).strip().upper()[:28] or platform.machine().upper()
cores = os.cpu_count() or 1
mem = re.search(r"^MemTotal:\s*(\d+)", read("/proc/meminfo"), re.M)
mem = f"{round(int(mem.group(1)) / 1048576)} GB" if mem else "?"
arch = platform.machine().upper()


# ── drawing helpers ─────────────────────────────────────────────────────────
def base(seed):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = (y / H) * 0.6
        d.line([(0, y), (W, y)], fill=tuple(int(BG[i] * (1 - t) + BG2[i] * t) for i in range(3)))
    step = max(20, u(40))
    for x in range(0, W, step): d.line([(x, 0), (x, H)], fill=(22, 13, 18))
    for y in range(0, H, step): d.line([(0, y), (W, y)], fill=(22, 13, 18))
    for y in range(0, H, max(2, u(3))): d.line([(0, y), (W, y)], fill=(8, 7, 10))
    rnd = random.Random(seed)
    for _ in range(int(26 * W * H / (1600 * 900))):
        x, y = rnd.randrange(0, W, step), rnd.randrange(0, H, step)
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=rnd.choice([OX, MUTED, TEAL]))
    return im, d


def brackets(d, box, col, length=38, width=2):
    x0, y0, x1, y1 = box; L = u(length); w = max(1, u(width))
    for x, y, dx, dy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y), (x + dx * L, y)], fill=col, width=w)
        d.line([(x, y), (x, y + dy * L)], fill=col, width=w)


def tri(d, x, y, s, col):
    d.polygon([(x, y), (x + s, y), (x, y + s)], fill=col)


def glitch_text(im, xy, text, fnt, seed, slices=3):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x, y = xy
    ld.text((x - u(6), y + u(3)), text, font=fnt, fill=SHADOW + (140,))
    ld.text((x, y), text, font=fnt, fill=CORAL + (255,))
    bbox = ld.textbbox((x, y), text, font=fnt)
    rnd = random.Random(seed)
    top, bot = bbox[1], bbox[3]; span = bot - top; used = []
    for _ in range(slices):
        for _try in range(20):
            sh = rnd.randint(max(12, span // 6), max(18, span // 4))
            sy = rnd.randint(top + int(span * 0.22), max(top + int(span * 0.22), bot - int(span * 0.18) - sh))
            if all(sy + sh < a or sy > b for a, b in used): break
        used.append((sy - 6, sy + sh + 6))
        dx = rnd.choice([-1, 1]) * rnd.randint(u(5), u(11))
        x0, x1 = max(0, bbox[0] - 30), min(W, bbox[2] + 30)
        band = layer.crop((x0, sy, x1, sy + sh))
        layer.paste((0, 0, 0, 0), (x0, sy, x1, sy + sh))
        layer.paste(band, (x0 + dx, sy))
    im.paste(layer, (0, 0), layer)
    return bbox


def spans(d, x, y, parts, fnt):
    for text, col in parts:
        d.text((x, y), text, font=fnt, fill=col)
        x += d.textlength(text, font=fnt)
    return x


def telemetry(d, x, y, seed, rows=4):
    rnd = random.Random(seed); f = mono(14)
    for r in range(rows):
        line = "  ".join(f"{rnd.getrandbits(16):04X}" for _ in range(8))
        d.text((x, y + r * u(18)), line, font=f, fill=OX if r % 2 else MUTED)
    bx = x
    while bx < x + u(300):
        w = rnd.choice([1, 1, 2, 3])
        d.rectangle([bx, y + rows * u(18) + u(10), bx + max(1, u(w)) - 1, y + rows * u(18) + u(34)], fill=MUTED)
        bx += max(1, u(w)) + rnd.choice([2, 3, 4])


# ── composition ─────────────────────────────────────────────────────────────
seed = sum(map(ord, host))
im, d = base(seed)
# Omarchy's bar sits on top; keep the frame below it
top = u(46)
brackets(d, (u(16), top, W - u(16), H - u(16)), CORAL)

# NODE panel, right side
pw = u(330); px1 = W - u(56); px0 = px1 - pw; py0 = top + u(40)
lines = [
    ("OS", os_name[:22]), ("KERNEL", kernel), ("ARCH", arch), ("CPU", cpu),
    ("CORES", str(cores)), ("MEMORY", mem), ("DISPLAY", f"{W}x{H}"),
]
if tsnet: lines.append(("TSNET", tsnet))
row_h = u(34)
py1 = py0 + u(40) + row_h * len(lines) + u(26)
over = Image.new("RGBA", im.size, (0, 0, 0, 0))
od = ImageDraw.Draw(over)
cut = u(16)
shape = [(px0, py0), (px1, py0), (px1, py1), (px0 + cut, py1), (px0, py1 - cut)]
od.polygon(shape, fill=PANEL + (235,))
im.paste(over, (0, 0), over)
d = ImageDraw.Draw(im)
d.line(shape + [shape[0]], fill=OX, width=1)
d.rectangle([px0, py0, px1, py0 + u(28)], fill=CORAL)
tri(d, px0 + u(9), py0 + u(8), u(12), INK)
d.text((px0 + u(30), py0 + u(4)), "NODE", font=mono(18), fill=INK)
d.text((px1 - u(70), py0 + u(6)), "SYS.07", font=mono(14), fill=INK)
fy = py0 + u(44)
for i, (k, v) in enumerate(lines):
    d.text((px0 + u(16), fy + i * row_h), k, font=mono(15), fill=MUTED)
    vw = d.textlength(v, font=mono(16))
    d.text((px1 - u(16) - vw, fy + i * row_h - u(1)), v, font=mono(16), fill=CYAN if k == "TSNET" else CORAL)
    if i < len(lines) - 1:
        d.line([(px0 + u(16), fy + i * row_h + u(26)), (px1 - u(16), fy + i * row_h + u(26))], fill=(40, 20, 26))
tri(d, px1 - u(14), py1 - u(14), u(14), CORAL)

# HUD ruler between the title and the panel
rx = px0 - u(40)
for y in range(top + u(30), H - u(40), max(4, u(8))): d.point((rx, y), fill=OX)
for i, y in enumerate(range(top + u(30), H - u(40), u(80))):
    d.line([(rx - u(6), y), (rx, y)], fill=MUTED)
    d.text((rx - u(34), y - u(6)), f"{i * 80:03d}", font=mono(11), fill=OX)

# Title block, left
x = u(96)
title_size = 230
f = raj(title_size)
max_w = rx - u(80) - x
while d.textlength(host, font=f) > max_w and title_size > 90:
    title_size -= 10; f = raj(title_size)
ty = int(H * 0.30)
tri(d, x, ty - u(6), u(14), CYAN)
spans(d, x + u(24), ty - u(10), [
    ("NIGHT CITY NET", CORAL), ("  //  ", OX), ("NODE ONLINE", CORAL_DIM),
], mono(20))
bbox = glitch_text(im, (x - u(8), ty), host, f, seed=seed, slices=2)
d = ImageDraw.Draw(im)
ry = bbox[3] + u(22)
d.rectangle([x, ry - u(1), x + u(90), ry + u(2)], fill=CYAN)
end = min(x + u(760), rx - u(120))
d.line([(x + u(100), ry), (end, ry)], fill=CORAL, width=max(1, u(2)))
d.polygon([(end, ry - u(1)), (end + u(30), ry - u(1)), (end + u(16), ry + u(12)), (end, ry + u(12))], fill=CORAL)
d.text((x, ry + u(18)), "WAKE UP, NETRUNNER.", font=raj(46, "SemiBold"), fill=CYAN)
keys = mono(19); yk = ry + u(86)
spans(d, x, yk, [
    ("SUPER+G ", YEL), ("JACK IN", CORAL), ("    SUPER+ALT+Y ", YEL), ("CYBERDECK", CORAL),
    ("    SUPER+SPACE ", YEL), ("LAUNCH", CORAL),
], keys)

telemetry(d, x, H - u(136), seed=seed + 1)
foot = f"NIGHT CITY NET  //  NODE {host}  //  STATUS: ONLINE"
d.text((rx - u(40) - d.textlength(foot, font=mono(15)), H - u(44)), foot, font=mono(15), fill=MUTED)

out.parent.mkdir(parents=True, exist_ok=True)
im.save(out, optimize=True)
print(out)
