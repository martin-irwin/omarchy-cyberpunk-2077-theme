#!/usr/bin/env python3
r"""Build night-city.css, a WhatsApp Web skin in the style of V's phone
messages in Cyberpunk 2077, for Ferdium (or any user-CSS extension).

WhatsApp Web's class names are generated and change every few weeks, but its
colours all come from CSS custom properties (the WDS design-system tokens plus
older names like --panel-background). Overriding those survives redesigns far
better than class selectors. whatsapp-dark-vars.txt is a dump of every colour
variable in WhatsApp's dark mode, taken from the live app; each one is remapped
onto the Night City palette by role (dark surfaces, grey text, brand green...),
then the tokens that define the look of a chat are pinned: incoming messages
coral on dark oxblood, outgoing cyan on dark teal, links gig-yellow.

    build-skin.py whatsapp-dark-vars.txt night-city.css

To refresh the dump after a WhatsApp redesign, run this in the WhatsApp
service's DevTools console (dark mode) and save the output:

    (() => {
      const cs = getComputedStyle(document.body), names = new Set(), aliases = {};
      for (const s of document.styleSheets) for (const r of s.cssRules) if (r.style)
        for (const p of r.style) if (p.startsWith("--")) {
          names.add(p);
          const v = r.style.getPropertyValue(p).trim();
          if (/^(:root|\.dark)/.test(r.selectorText || "") && v.startsWith("var(")) aliases[p] = v;
        }
      copy([...names].sort().map(n => n + ": " + (aliases[n] || cs.getPropertyValue(n).trim())).join("\n"));
    })()

Variables that WhatsApp defines as var(...) aliases are kept as aliases, so
they follow the pinned tokens below instead of being remapped on their own.
"""
import colorsys
import re
import sys

INK = "0d0b10"

PINNED = {
    # Surfaces: near-black with a red cast, like the screens in Night City
    "--WDS-surface-default": "#0d0b10",
    "--WDS-surface-emphasized": "#1c1016",
    "--WDS-surface-elevated-default": "#130d12",
    "--WDS-surface-elevated-emphasized": "#1c1016",
    "--WDS-surface-highlight": "rgba(94, 246, 255, .08)",
    "--WDS-surface-pressed": "rgba(94, 246, 255, .16)",
    "--WDS-surface-inverse": "#ff6159",
    "--WDS-app-wash": "#040306",
    "--WDS-background-wash-plain": "#08070b",
    "--WDS-background-wash-inset": "#08070b",
    "--WDS-background-elevated-wash-plain": "#130d12",
    "--WDS-background-elevated-wash-inset": "#130d12",
    "--WDS-components-surface-nav-bar": "#040306",
    "--WDS-components-active-list-row": "#10353a",
    "--WDS-components-filter-surface-selected": "#10353a",
    "--WDS-lines-divider": "#2a1418",
    "--WDS-lines-outline-default": "#5a1e24",
    "--WDS-lines-outline-deemphasized": "#2a1418",
    # Text: HUD coral, dimmed coral for secondary text
    "--WDS-content-default": "#ff6159",
    "--WDS-content-deemphasized": "#a3463f",
    "--WDS-content-disabled": "#5a1e24",
    "--WDS-content-inverse": "#0d0b10",
    "--WDS-content-on-accent": "#0d0b10",
    "--WDS-content-action-default": "#ff6159",
    "--WDS-content-action-emphasized": "#5ef6ff",
    "--WDS-content-external-link": "#f3e600",
    "--WDS-content-read": "#5ef6ff",
    # Accent: netrunner cyan replaces WhatsApp green
    "--WDS-accent": "#5ef6ff",
    "--WDS-accent-deemphasized": "#10353a",
    "--WDS-accent-emphasized": "#a8fbff",
    "--WDS-persistent-always-branded": "#5ef6ff",
    "--WDS-persistent-activity-indicator": "#5ef6ff",
    "--WDS-systems-status-seen": "#5a1e24",
    "--WDS-secondary-negative": "#ff003c",
    "--WDS-secondary-warning": "#f3e600",
    "--WDS-secondary-positive": "#1ef2a0",
    # Chat: the phone SMS look
    "--WDS-systems-chat-background-wallpaper": "#08070b",
    "--WDS-systems-chat-foreground-wallpaper": "#2a1418",
    "--WDS-systems-chat-surface-composer": "#130d12",
    "--WDS-systems-chat-surface-tray": "#0d0b10",
    "--WDS-systems-bubble-surface-incoming": "#1c1016",
    "--WDS-systems-bubble-surface-outgoing": "#0e2a2e",
    "--WDS-systems-bubble-surface-system": "#1c1016",
    "--WDS-systems-bubble-surface-overlay": "rgba(13, 11, 16, .8)",
    "--WDS-systems-bubble-content-deemphasized": "#a3463f",
    "--WDS-components-badge-muted": "#5a1e24",
    "--panel-background": "#0d0b10",
    "--panel-background-deep": "#08070b",
    "--panel-input-background": "#1c1016",
    "--app-background": "#040306",
    "--app-background-deeper": "#040306",
    "--bubble-meta": "#a3463f",
    "--bubble-meta-icon": "#a3463f",
    "--message-selection-highlight": "rgba(94, 246, 255, .08)",
}

FONTS = {
    "--font-family-default": '"Rajdhani", "Share Tech Mono", Helvetica, Arial, sans-serif',
    "--font-family-system-fds": '"Rajdhani", "Share Tech Mono", system-ui, sans-serif',
    "--font-family-segoe": '"Rajdhani", "Share Tech Mono", Helvetica, Arial, sans-serif',
    "--font-family-apple": '"Rajdhani", "Share Tech Mono", system-ui, sans-serif',
    "--font-family-code": '"Share Tech Mono", ui-monospace, monospace',
    "--font-family-monospace": '"Share Tech Mono", ui-monospace, monospace',
}

# Structural rules on WhatsApp's long-lived semantic hooks rather than its
# generated class names. If a redesign drops one, only that detail is lost.
EXTRA = """
/* Angular bubbles, like the in-game phone */
* { --chat-bubble-border-radius: 0 !important; }

/* Your own messages read cyan, everyone else's coral */
.message-out { --WDS-content-default: #5ef6ff !important; --message-primary: #5ef6ff !important;
  --bubble-meta: #2c8c94 !important; --bubble-meta-icon: #2c8c94 !important; }
.message-in { --message-primary: #ff6159 !important; }
.message-in [data-pre-plain-text] { box-shadow: inset 2px 0 0 #ff6159; padding-left: 6px; }
.message-out [data-pre-plain-text] { box-shadow: inset -2px 0 0 #5ef6ff; padding-right: 6px; }

/* Rajdhani is narrow: a touch more weight and size keeps it readable */
body { font-family: "Rajdhani", "Share Tech Mono", Helvetica, Arial, sans-serif !important; font-weight: 500; }
.selectable-text { font-size: 1.04em; letter-spacing: .01em; }

/* Thin coral scrollbars */
::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
::-webkit-scrollbar-thumb { background: #5a1e24 !important; border-radius: 0 !important; }
::-webkit-scrollbar-thumb:hover { background: #ff6159 !important; }
::selection { background: #10353a; color: #5ef6ff; }
"""

COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|\d{1,3}, ?\d{1,3}, ?\d{1,3}")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tohex(rgb):
    return "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb)


def mix(a, b, t):
    a, b = hexrgb(a), hexrgb(b)
    return tohex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def remap(rgb_hex):
    """Same role-based remap as the Telegram theme, so both apps match."""
    r, g, b = hexrgb(rgb_hex)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if l < 0.32:
        return mix(INK, "3a1a20", l / 0.32)
    if s < 0.22:
        return mix("7d4446", "ff6159", min(1, (l - 0.32) / 0.5))
    if 170 <= hue < 265:
        return mix("1d5f66", "5ef6ff", min(1, (l - 0.32) / 0.4))
    if 75 <= hue < 170:
        # WhatsApp's brand green is its accent: it becomes cyan
        return mix("1d5f66", "5ef6ff", min(1, (l - 0.25) / 0.4))
    if 40 <= hue < 75:
        return "f3e600"
    if 15 <= hue < 40:
        return "ff8a3d"
    if 265 <= hue < 330:
        return "c34dff"
    return "ff003c"


def parse(value):
    """Return (hex, alpha, kind) for a colour value, or None."""
    value = value.strip()
    if value.startswith("#"):
        h = value[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        alpha = int(h[6:8], 16) / 255 if len(h) == 8 else None
        return h[:6].lower(), alpha, "hex"
    nums = re.findall(r"[\d.]+%?", value)
    if value.startswith("rgb") and len(nums) >= 3:
        rgb = [int(float(n)) for n in nums[:3]]
        alpha = float(nums[3]) if len(nums) > 3 else None
        return "".join(f"{c:02x}" for c in rgb), alpha, "rgb"
    if len(nums) == 3:
        return "".join(f"{int(n):02x}" for n in nums), None, "triplet"
    return None


def render(h, alpha, kind):
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if kind == "triplet":
        return f"{r}, {g}, {b}"
    if alpha is not None:
        return f"rgba({r}, {g}, {b}, {alpha:g})"
    return f"#{h}"


def main():
    src, out = sys.argv[1], sys.argv[2]
    decls = {}
    for line in open(src, encoding="utf-8"):
        key, _, value = line.strip().partition(": ")
        if not key.startswith("--") or not COLOUR.fullmatch(value.strip()):
            continue
        parsed = parse(value)
        if not parsed:
            continue
        h, alpha, kind = parsed
        decls[key] = render(remap(h), alpha, kind)

    # Pinned tokens win, and their -RGB twins follow them.
    for key, value in PINNED.items():
        decls[key] = value
        if key + "-RGB" in decls or key.startswith("--WDS"):
            p = parse(value)
            if p:
                decls[key + "-RGB"] = render(p[0], None, "triplet")
    decls.update(FONTS)

    body = "\n".join(f"  {k}: {v} !important;" for k, v in sorted(decls.items()))
    with open(out, "w", encoding="utf-8") as f:
        f.write("/* Night City: WhatsApp Web as V's phone. Generated by build-skin.py; edit that, not this. */\n")
        # WhatsApp scopes its tokens to generated classes (and per-chat themes)
        # on nested elements, so the overrides are set on every element.
        f.write(f"*, *::before, *::after {{\n{body}\n}}\n")
        f.write(EXTRA)
    print(f"wrote {out}: {len(decls)} variables", file=sys.stderr)


if __name__ == "__main__":
    main()
