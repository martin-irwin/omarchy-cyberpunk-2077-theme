#!/usr/bin/env python3
"""Build night-city.tdesktop-theme, a Telegram Desktop theme in the style of
V's phone messages in Cyberpunk 2077.

Telegram's own night theme (colors.tdesktop-theme from the tdesktop repo) is
the base, so every one of its ~450 colour keys exists. Each literal colour is
remapped onto the Night City palette by role (dark surfaces, text greys, blue
accents...), then the keys that define the look of a chat are pinned
explicitly: incoming messages coral on dark oxblood, outgoing cyan on dark
teal, service notices gig-yellow.

    build-theme.py <night colors.tdesktop-theme> <out.tdesktop-theme> [tiled.png]

The night theme source is colors.tdesktop-theme inside
https://raw.githubusercontent.com/telegramdesktop/tdesktop/dev/Telegram/Resources/night.tdesktop-theme
(a zip). A background image named tiled.* is repeated across the chat, which
is how tiled.png lays Cyberphone's grid and scanlines behind the messages.
"""
import colorsys
import pathlib
import re
import sys
import zipfile

INK = "0d0b10"

PINNED = {
    # Window chrome
    "windowBg": "#0d0b10",
    "windowFg": "#ff6159",
    "windowBgOver": "#1c1016",
    "windowBgRipple": "#2a1418",
    "windowSubTextFg": "#a3463f",
    "windowActiveTextFg": "#5ef6ff",
    "windowBgActive": "#5ef6ff",
    "windowFgActive": "#0d0b10",
    "windowShadowFg": "#000000",
    "activeButtonBg": "#10353a",
    "activeButtonBgOver": "#14454b",
    "activeButtonFg": "#5ef6ff",
    "activeButtonFgOver": "#a8fbff",
    "lightButtonFg": "#5ef6ff",
    "attentionButtonFg": "#ff003c",
    "titleBg": "#040306",
    "titleFg": "#ff6159",
    "titleFgActive": "#ff6159",
    "titleBgActive": "#040306",
    # Chat list
    "dialogsBg": "#08070b",
    "dialogsBgOver": "#1c1016",
    "dialogsBgActive": "#10353a",
    "dialogsNameFg": "#ff6159",
    "dialogsNameFgActive": "#5ef6ff",
    "dialogsTextFg": "#a3463f",
    "dialogsTextFgActive": "#5ef6ff",
    "dialogsDateFg": "#7d4446",
    "dialogsDateFgActive": "#5ef6ff",
    "dialogsUnreadBg": "#ff6159",
    "dialogsUnreadBgActive": "#5ef6ff",
    "dialogsUnreadFg": "#0d0b10",
    "dialogsUnreadFgActive": "#0d0b10",
    "dialogsUnreadBgMuted": "#5a1e24",
    # Messages: the phone SMS look
    "msgInBg": "#1c1016",
    "msgInBgSelected": "#2a1418",
    "msgInShadow": "#ff6159",
    "msgInShadowSelected": "#ff8c82",
    "historyTextInFg": "#ff6159",
    "msgInDateFg": "#a3463f",
    "msgInServiceFg": "#5ef6ff",
    "msgOutBg": "#0e2a2e",
    "msgOutBgSelected": "#10353a",
    "msgOutShadow": "#5ef6ff",
    "msgOutShadowSelected": "#a8fbff",
    "historyTextOutFg": "#5ef6ff",
    "msgOutDateFg": "#2c8c94",
    "msgOutServiceFg": "#a8fbff",
    "msgServiceBg": "#1c1016d0",
    "msgServiceFg": "#f3e600",
    # Reply and quote bars: coral in their messages, cyan in yours
    "msgInReplyBarColor": "#ff6159",
    "msgInReplyBarSelColor": "#ff8c82",
    "msgOutReplyBarColor": "#5ef6ff",
    "msgOutReplyBarSelColor": "#a8fbff",
    # Unread divider and pinned bar in HUD style
    "historyUnreadBarBg": "#130d12",
    "historyUnreadBarBorder": "#5a1e24",
    "historyPinnedBg": "#040306",
    "emojiPanHeaderBg": "#0d0b10f2",
    # Drafts and "typing…" in the chat list
    "dialogsDraftFg": "#f3e600",
    "dialogsTextFgService": "#5ef6ff",
    "dialogsTextFgServiceOver": "#5ef6ff",
    "dialogsVerifiedIconBg": "#5ef6ff",
    "dialogsVerifiedIconFg": "#0d0b10",
    # Matched to Cyberphone: near-black header and reply area, cyan typing
    "topBarBg": "#040306",
    "historyComposeAreaBg": "#040306",
    "historyComposeAreaFg": "#5ef6ff",
    "historyComposeAreaFgService": "#a3463f",
    "historyOutIconFg": "#5ef6ff",
    "historyOutIconFgSelected": "#a8fbff",
    "historyComposeIconFg": "#a3463f",
    "historyComposeIconFgOver": "#5ef6ff",
    "historySendIconFg": "#5ef6ff",
    "historySendIconFgOver": "#a8fbff",
    "historyLinkInFg": "#f3e600",
    "historyLinkOutFg": "#f3e600",
    "historyFileNameInFg": "#ff6159",
    "historyFileNameOutFg": "#5ef6ff",
    "msgFileInBg": "#ff6159",
    "msgFileOutBg": "#5ef6ff",
    "historyUnreadBarBg": "#1c1016",
    "historyUnreadBarFg": "#f3e600",
    "historyToDownBg": "#1c1016",
    "historyToDownFg": "#ff6159",
    "historyScrollBg": "#ff615940",
    "historyScrollBgOver": "#ff615980",
    "introBg": "#0d0b10",
    "boxBg": "#0d0b10",
    "boxTextFg": "#ff6159",
    "menuBg": "#0d0b10",
    "menuBgOver": "#10353a",
    "menuFgDisabled": "#5a1e24",
    "sideBarBg": "#040306",
    "sideBarBgActive": "#10353a",
    "sideBarTextFg": "#a3463f",
    "sideBarTextFgActive": "#5ef6ff",
    "sideBarIconFg": "#a3463f",
    "sideBarIconFgActive": "#5ef6ff",
    "sideBarBadgeBg": "#ff6159",
}


# Telegram's eight peer colours (names in groups, placeholder portraits)
PEERS = ["#ff003c", "#ff8a3d", "#c34dff", "#1ef2a0", "#5ef6ff", "#3fa9ff", "#ff6159", "#f3e600"]
for i, colour in enumerate(PEERS, 1):
    PINNED[f"historyPeer{i}NameFg"] = colour
    PINNED[f"historyPeer{i}NameFgSelected"] = colour
    PINNED[f"historyPeer{i}UserpicBg"] = colour
    PINNED[f"historyPeer{i}UserpicBg2"] = colour
PINNED["historyPeerUserpicFg"] = "#0d0b10"


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tohex(rgb):
    return "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb)


def mix(a, b, t):
    a, b = hexrgb(a), hexrgb(b)
    return tohex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def remap(rgb_hex):
    r, g, b = hexrgb(rgb_hex)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if l < 0.32:
        # Surfaces: night theme slate -> Night City near-black with a red cast
        return mix(INK, "3a1a20", l / 0.32)
    if s < 0.22:
        # Text greys: dim coral -> HUD coral
        return mix("7d4446", "ff6159", min(1, (l - 0.32) / 0.5))
    if 170 <= hue < 265:
        return mix("1d5f66", "5ef6ff", min(1, (l - 0.32) / 0.4))
    if 75 <= hue < 170:
        return "1ef2a0"
    if 40 <= hue < 75:
        return "f3e600"
    if 15 <= hue < 40:
        return "ff8a3d"
    if 265 <= hue < 330:
        return "c34dff"
    return "ff003c"


def main():
    src, out = sys.argv[1], sys.argv[2]
    background = sys.argv[3] if len(sys.argv) > 3 else None
    line_re = re.compile(r"^(\w+):\s*(#[0-9a-fA-F]{6,8}|\w+);(.*)$")
    lines = []
    seen = set()
    for line in open(src, encoding="utf-8"):
        m = line_re.match(line.rstrip("\n"))
        if not m:
            lines.append(line.rstrip("\n"))
            continue
        key, value, rest = m.groups()
        seen.add(key)
        if key in PINNED:
            value = PINNED[key]
        elif value.startswith("#"):
            alpha = value[7:9]
            value = "#" + remap(value[1:7].lower()) + alpha
        lines.append(f"{key}: {value};{rest}")
    # Only keys Telegram itself defines are written; report any stale ones.
    for key in sorted(set(PINNED) - seen):
        print(f"note: {key} is not a Telegram colour key, skipped", file=sys.stderr)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("colors.tdesktop-theme", "\n".join(lines) + "\n")
        if background:
            name = pathlib.Path(background).name
            z.write(background, name if name.startswith("tiled.") else "background.png")


if __name__ == "__main__":
    main()
