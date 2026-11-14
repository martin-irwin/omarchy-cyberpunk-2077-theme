#!/usr/bin/env python3
"""Build night-city.css for Cybergram: Telegram Web A as V's phone.

Telegram Web A (web.telegram.org/a) styles everything through ~120
--color-* variables and a set of --border-radius-* ones. Like the WhatsApp
skin (extras/whatsapp/build-skin.py), this doesn't chase generated class
names: it overrides the variables, so the skin survives most updates.

  - The variables that define the look are pinned to the Night City palette
    (coral text on near-black, cyan for you, dark teal for your bubbles,
    gig-yellow links). Every other colour is remapped by role from its light
    theme value: near-white surfaces become dark panels, greys become coral,
    blues cyan, and so on.
  - Every corner radius becomes 0: the game's UI has no rounded corners.
  - phone.css (shapes, portraits, message edges, the grid) is appended.

    build-skin.py telegram-web-vars.txt phone.css night-city.css

telegram-web-vars.txt is a dump of Web A's :root variables (name<TAB>value),
taken from its main stylesheet (web.telegram.org/a/assets/index-*.css). After
a big Telegram redesign, re-dump it and rebuild.
"""
import colorsys
import re
import sys

INK, VOID, DEEP = "#0d0b10", "#08070b", "#040306"
PANEL, RIPPLE, OXBLOOD, SURFACE = "#1c1016", "#2a1418", "#5a1e24", "#3a1a20"
CORAL, CORAL_DIM, CORAL_LIGHT, MUTED = "#ff6159", "#a3463f", "#ff8c82", "#7d4446"
CYAN, CYAN_LIGHT, TEAL, TEAL_DEEP, TEAL_MID, CYAN_DIM = "#5ef6ff", "#a8fbff", "#10353a", "#0e2a2e", "#14454b", "#2c8c94"
YELLOW, ALARM, GREEN, BONE = "#f3e600", "#ff003c", "#1ef2a0", "#f2ebe6"

PINNED = {
    # surfaces
    "--color-background": INK,
    "--color-background-secondary": VOID,
    "--color-background-secondary-accent": PANEL,
    "--color-background-selected": TEAL,
    "--color-background-own": TEAL_DEEP,
    "--color-background-own-selected": TEAL,
    "--color-background-own-apple": TEAL_DEEP,
    "--color-background-menu-separator": RIPPLE,
    "--color-background-compact-menu": "#0d0b10e6",
    "--color-background-compact-menu-hover": PANEL,
    "--color-background-compact-menu-reactions": "#0d0b10e6",
    "--color-chat-hover": PANEL,
    "--color-chat-active": TEAL,
    "--color-item-hover": PANEL,
    "--color-item-active": RIPPLE,
    "--color-reply-hover": RIPPLE,
    "--color-reply-active": SURFACE,
    "--color-reply-own-hover": TEAL_MID,
    "--color-reply-own-active": "#1d5f66",
    "--color-reply-own-hover-apple": TEAL_MID,
    "--color-reply-own-active-apple": "#1d5f66",
    "--color-toast-background": PANEL,
    "--color-webpage-initial-background": PANEL,
    # text
    "--color-text": CORAL,
    "--color-text-secondary": CORAL_DIM,
    "--color-text-secondary-apple": CORAL_DIM,
    "--color-text-meta": MUTED,
    "--color-text-meta-colored": CYAN_DIM,
    "--color-text-green": CYAN,
    "--color-placeholders": MUTED,
    "--color-white": BONE,
    "--color-gray": MUTED,
    "--color-deleted-account": MUTED,
    "--color-user": CORAL,
    "--color-chat-username": CYAN,
    "--color-message-non-contact": YELLOW,
    # accents: cyan is "you", coral is "them", yellow is links and notices
    "--color-primary": CYAN,
    "--color-primary-shade": CYAN_LIGHT,
    "--color-primary-tint": TEAL,
    "--color-telegram-blue": CYAN,
    "--color-active": CYAN,
    "--color-accent-own": CYAN,
    "--color-message-meta-own": CYAN_DIM,
    "--color-links": YELLOW,
    "--color-own-links": YELLOW,
    "--color-toast-action": CYAN,
    "--color-composer-button": CYAN,
    "--color-voice-transcribe-button": PANEL,
    "--color-voice-transcribe-button-own": TEAL,
    "--color-yellow": YELLOW,
    "--color-warning": YELLOW,
    "--color-error": ALARM,
    "--color-success": GREEN,
    # lines
    "--color-borders": OXBLOOD,
    "--color-borders-input": OXBLOOD,
    "--color-dividers": RIPPLE,
    "--color-dividers-android": RIPPLE,
    "--color-scrollbar": OXBLOOD,
    "--color-icon-secondary": CORAL_DIM,
    "--color-list-icon": CORAL_DIM,
    "--color-default-shadow": "#000000aa",
    "--color-light-shadow": "#00000066",
    # code
    "--color-code": YELLOW,
    "--color-code-bg": PANEL,
    "--color-code-own": YELLOW,
    "--color-code-own-bg": TEAL,
    # reactions
    "--color-message-reaction": PANEL,
    "--color-message-reaction-hover": RIPPLE,
    "--color-message-reaction-own": TEAL,
    "--color-message-reaction-hover-own": TEAL_MID,
    "--color-message-reaction-chosen-hover": CORAL_LIGHT,
    "--color-message-reaction-chosen-hover-own": CYAN_LIGHT,
}


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)), (h[6:8] if len(h) == 8 else "")


def to_hex(rgb):
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb)


def mix(a, b, t):
    (ra, _), (rb, _) = hex_rgb(a), hex_rgb(b)
    return to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def remap(rgb):
    """A light-theme colour → its Night City role."""
    h, l, s = colorsys.rgb_to_hls(*rgb)
    hue = h * 360
    if s < 0.25:
        if l > 0.8:                      # near-white surfaces → dark panels
            return mix(INK, SURFACE, (1 - l) / 0.2)
        if l < 0.3:                      # near-black text → HUD coral
            return CORAL
        return mix(MUTED, CORAL_DIM, (0.8 - l) / 0.5)   # greys → dim coral
    if 170 <= hue < 265:
        return CYAN if l < 0.75 else TEAL
    if 75 <= hue < 170:
        return CYAN_DIM if l > 0.6 else CYAN
    if 40 <= hue < 75:
        return YELLOW
    if 15 <= hue < 40:
        return "#ff8a3d"
    if 265 <= hue < 330:
        return "#c34dff"
    return ALARM


HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")
TRIPLET = re.compile(r"^\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\s*$")


def main():
    vars_file, phone_css, out = sys.argv[1:4]
    lines, count = [], 0
    for raw in open(vars_file, encoding="utf-8"):
        name, _, value = raw.rstrip("\n").partition("\t")
        if name.startswith("--border-radius"):
            lines.append(f"  {name}: 0 !important;")
            continue
        if not name.startswith("--color"):
            continue
        if name.endswith("-rgb"):
            base = name[:-4]
            src = PINNED.get(base)
            if src:
                (r, g, b), _ = hex_rgb(src)
            else:
                m = TRIPLET.match(value)
                if not m:
                    continue
                r, g, b = hex_rgb(remap(tuple(float(x) / 255 for x in m.groups())))[0]
            lines.append(f"  {name}: {round(r * 255)}, {round(g * 255)}, {round(b * 255)} !important;")
            count += 1
            continue
        if name in PINNED:
            lines.append(f"  {name}: {PINNED[name]} !important;")
            count += 1
        elif HEX.match(value):
            rgb, alpha = hex_rgb(value)
            lines.append(f"  {name}: {remap(rgb)}{alpha} !important;")
            count += 1
        # values that reference other variables follow them; leave as they are
    css = (
        "/* Night City skin for Telegram Web A (Cybergram). Generated by\n"
        "   build-skin.py from telegram-web-vars.txt + phone.css; edit those. */\n"
        ":root, html.theme-dark, html.theme-light, body {\n" + "\n".join(lines) + "\n}\n\n"
        + open(phone_css, encoding="utf-8").read()
    )
    open(out, "w", encoding="utf-8").write(css)
    print(f"{out}: {count} colours, {sum(1 for l in lines if 'radius' in l)} radii")


if __name__ == "__main__":
    main()
