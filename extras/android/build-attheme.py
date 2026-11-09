#!/usr/bin/env python3
"""Build night-city.attheme: Telegram for Android as V's phone.

The Android twin of extras/telegram/build-theme.py, with the same palette and
the same role mapping (it imports that script's remap()):

  - Telegram Android's own night theme is the base, so every one of its ~540
    colour keys exists. A theme file only overrides what it lists; the rest
    falls back to Telegram's light theme, which is why a remapped full night
    theme beats a hand-picked handful of keys.
  - Each colour is remapped onto the Night City palette by role (dark
    surfaces, text greys, blue accents...), keeping its transparency.
  - The keys that define a chat are pinned: their messages coral on dark
    oxblood, yours cyan on dark teal, notices gig-yellow, cyan typing.
  - The Cyberphone grid with scanlines is embedded as the chat wallpaper.

    build-attheme.py <night.attheme> <out.attheme> [wallpaper.jpg]

night.attheme is TMessagesProj/src/main/assets/night.attheme from
https://github.com/DrKLO/Telegram. Telegram can't change fonts, and bubble
corners come from Settings → Chat Settings → Message corners (slide it left
for the square HUD look).
"""
import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tdesktop_theme", HERE.parent / "telegram" / "build-theme.py")
tdesktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tdesktop)
remap = tdesktop.remap
PEERS = tdesktop.PEERS
USERPICS = tdesktop.USERPICS

# Night City palette
INK, VOID, DEEP = "0d0b10", "08070b", "040306"
PANEL, OXBLOOD, RIPPLE = "1c1016", "5a1e24", "2a1418"
CORAL, CORAL_DIM, CORAL_LIGHT = "ff6159", "a3463f", "ff8c82"
MUTED = "7d4446"
CYAN, CYAN_LIGHT, TEAL, TEAL_DEEP, CYAN_DIM = "5ef6ff", "a8fbff", "10353a", "0e2a2e", "2c8c94"
YELLOW, ALARM, BONE = "f3e600", "ff003c", "f2ebe6"

PINNED = {
    # Windows, lists and settings
    "windowBackgroundWhite": INK,
    "windowBackgroundGray": VOID,
    "windowBackgroundGrayShadow": "000000",
    "windowBackgroundWhiteBlackText": CORAL,
    "windowBackgroundWhiteGrayText": CORAL_DIM,
    "windowBackgroundWhiteGrayText2": CORAL_DIM,
    "windowBackgroundWhiteGrayText3": MUTED,
    "windowBackgroundWhiteGrayText4": CORAL_DIM,
    "windowBackgroundWhiteBlueText": CYAN,
    "windowBackgroundWhiteBlueText4": CYAN,
    "windowBackgroundWhiteBlueHeader": CYAN,
    "windowBackgroundWhiteValueText": CYAN,
    "windowBackgroundWhiteLinkText": YELLOW,
    "windowBackgroundWhiteGrayIcon": CORAL_DIM,
    "windowBackgroundWhiteInputField": OXBLOOD,
    "windowBackgroundWhiteInputFieldActivated": CYAN,
    "windowBackgroundChecked": TEAL,
    "windowBackgroundCheckText": CYAN,
    "divider": "2a1418",
    "listSelectorSDK21": "1a5ef6ff",
    "switchTrack": OXBLOOD,
    "switchTrackChecked": CYAN,
    "checkbox": CYAN,
    "checkboxCheck": INK,
    "checkboxSquareBackground": CYAN,
    "checkboxSquareCheck": INK,
    "radioBackgroundChecked": CYAN,
    "featuredStickers_addButton": CYAN,
    "featuredStickers_buttonText": INK,
    "dialogBackground": INK,
    "dialogBackgroundGray": VOID,
    "dialogTextBlack": CORAL,
    "dialogTextGray": CORAL_DIM,
    "dialogTextBlue": CYAN,
    "dialogTextLink": YELLOW,
    "dialogButton": CYAN,
    "dialogIcon": CORAL_DIM,
    "progressCircle": CYAN,
    # Header bars
    "actionBarDefault": DEEP,
    "actionBarDefaultTitle": CORAL,
    "actionBarDefaultSubtitle": CORAL_DIM,
    "actionBarDefaultIcon": CORAL,
    "actionBarDefaultSelector": "335ef6ff",
    "actionBarDefaultSearch": CYAN,
    "actionBarDefaultSearchPlaceholder": "88a3463f",
    "actionBarActionModeDefault": PANEL,
    "actionBarActionModeDefaultIcon": CYAN,
    "actionBarActionModeDefaultTop": OXBLOOD,
    "actionBarDefaultSubmenuBackground": INK,
    "actionBarDefaultSubmenuItem": CORAL,
    "actionBarDefaultSubmenuItemIcon": CORAL_DIM,
    "actionBarTabActiveText": CYAN,
    "actionBarTabUnactiveText": CORAL_DIM,
    "actionBarTabLine": CYAN,
    "actionBarTabSelector": "335ef6ff",
    # Chat list
    "chats_name": CORAL,
    "chats_secretName": CYAN,
    "chats_message": CORAL_DIM,
    "chats_message_threeLines": CORAL_DIM,
    "chats_nameMessage": CYAN,
    "chats_nameMessage_threeLines": CYAN,
    "chats_attachMessage": CYAN,
    "chats_actionMessage": CYAN,
    "chats_draft": YELLOW,
    "chats_date": MUTED,
    "chats_pinnedIcon": MUTED,
    "chats_pinnedOverlay": "0affffff",
    "chats_tabletSelectedOverlay": "1a5ef6ff",
    "chats_sentCheck": CYAN,
    "chats_sentReadCheck": CYAN,
    "chats_sentClock": MUTED,
    "chats_unreadCounter": CORAL,
    "chats_unreadCounterMuted": OXBLOOD,
    "chats_unreadCounterText": INK,
    "chats_onlineCircle": CYAN,
    "chats_verifiedBackground": CYAN,
    "chats_verifiedCheck": INK,
    "chats_muteIcon": MUTED,
    "chats_actionBackground": CORAL,
    "chats_actionPressedBackground": CORAL_LIGHT,
    "chats_actionIcon": INK,
    "chats_menuBackground": VOID,
    "chats_menuName": CORAL,
    "chats_menuPhone": CYAN,
    "chats_menuPhoneCats": CYAN,
    "chats_menuItemText": CORAL,
    "chats_menuItemIcon": CORAL_DIM,
    "chats_menuTopShadow": "000000",
    "chats_menuTopShadowCats": "000000",
    "chats_menuTopBackgroundCats": DEEP,
    # Messages: the phone SMS look
    "chat_inBubble": PANEL,
    "chat_inBubbleSelected": RIPPLE,
    "chat_inBubbleShadow": "66ff6159",
    "chat_outBubble": TEAL_DEEP,
    "chat_outBubbleGradient": TEAL_DEEP,
    "chat_outBubbleSelected": TEAL,
    "chat_outBubbleShadow": "665ef6ff",
    "chat_messageTextIn": CORAL,
    "chat_messageTextOut": CYAN,
    "chat_messageLinkIn": YELLOW,
    "chat_messageLinkOut": YELLOW,
    "chat_inTimeText": CORAL_DIM,
    "chat_outTimeText": CYAN_DIM,
    "chat_inTimeSelectedText": CORAL_LIGHT,
    "chat_outTimeSelectedText": CYAN_LIGHT,
    "chat_outSentCheck": CYAN_DIM,
    "chat_outSentCheckRead": CYAN,
    "chat_outSentClock": CYAN_DIM,
    "chat_inViews": CORAL_DIM,
    "chat_outViews": CYAN_DIM,
    "chat_inReplyLine": CORAL,
    "chat_outReplyLine": CYAN,
    "chat_inReplyNameText": CORAL,
    "chat_outReplyNameText": CYAN,
    "chat_inReplyMessageText": CORAL_DIM,
    "chat_outReplyMessageText": CYAN_DIM,
    "chat_inForwardedNameText": CORAL,
    "chat_outForwardedNameText": CYAN,
    "chat_inFileBackground": CORAL,
    "chat_outFileBackground": CYAN,
    "chat_inLoader": CORAL,
    "chat_outLoader": CYAN,
    "chat_inPreviewLine": CORAL,
    "chat_outPreviewLine": CYAN,
    "chat_inSiteNameText": CORAL,
    "chat_outSiteNameText": CYAN,
    "chat_inContactNameText": CORAL,
    "chat_outContactNameText": CYAN,
    "chat_inAudioSeekbarFill": CORAL,
    "chat_outAudioSeekbarFill": CYAN,
    "chat_inVoiceSeekbarFill": CORAL,
    "chat_outVoiceSeekbarFill": CYAN,
    "chat_serviceBackground": "d01c1016",
    "chat_serviceBackgroundSelected": "d02a1418",
    "chat_serviceText": YELLOW,
    "chat_serviceLink": CYAN,
    "chat_serviceIcon": YELLOW,
    "chat_unreadMessagesStartBackground": PANEL,
    "chat_unreadMessagesStartText": YELLOW,
    "chat_unreadMessagesStartArrowIcon": YELLOW,
    "chat_goDownButton": PANEL,
    "chat_goDownButtonIcon": CORAL,
    "chat_goDownButtonCounterBackground": CORAL,
    "chat_goDownButtonCounter": INK,
    "chat_wallpaper": INK,
    "chat_status": CYAN,
    "chat_topPanelBackground": DEEP,
    "chat_topPanelLine": CYAN,
    "chat_topPanelTitle": CYAN,
    "chat_topPanelMessage": CORAL_DIM,
    "chat_topPanelClose": CORAL_DIM,
    # Reply area: near-black with cyan typing, as on Cyberphone
    "chat_messagePanelBackground": DEEP,
    "chat_messagePanelShadow": "000000",
    "chat_messagePanelText": CYAN,
    "chat_messagePanelHint": "88a3463f",
    "chat_messagePanelIcons": CORAL_DIM,
    "chat_messagePanelSend": CYAN,
    "chat_messagePanelCursor": CYAN,
    "chat_messagePanelVoiceBackground": CYAN,
    "chat_messagePanelVoicePressed": CYAN_LIGHT,
    "chat_emojiPanelBackground": INK,
    "chat_emojiPanelIcon": CORAL_DIM,
    "chat_emojiPanelIconSelected": CYAN,
    "chat_emojiPanelNewTrending": CYAN,
    "chat_recordedVoiceBackground": CYAN,
    "chat_recordTime": CORAL,
    "chat_recordVoiceCancel": CORAL_DIM,
    # Profiles and avatars
    "avatar_text": INK,
    "avatar_backgroundActionBarBlue": DEEP,
    "avatar_actionBarIconBlue": CORAL,
    "avatar_actionBarSelectorBlue": "335ef6ff",
    "avatar_subtitleInProfileBlue": CYAN,
    "profile_title": CORAL,
    "profile_actionBackground": CORAL,
    "profile_actionIcon": INK,
    "profile_actionPressedBackground": CORAL_LIGHT,
    "profile_tabText": CORAL_DIM,
    "profile_tabSelectedText": CYAN,
    "profile_tabSelectedLine": CYAN,
    "profile_status": CYAN,
    "profile_verifiedBackground": CYAN,
    "profile_verifiedCheck": INK,
}

# Telegram's peer colours, as on desktop: group names keep the full set,
# placeholder portraits are coral/cyan HUD badges with dark initials
AVATARS = ["Red", "Orange", "Violet", "Green", "Cyan", "Blue", "Pink"]
for name, colour, pic in zip(AVATARS, PEERS, USERPICS):
    c, p = colour.lstrip("#"), pic.lstrip("#")
    PINNED[f"avatar_background{name}"] = p
    PINNED[f"avatar_background2{name}"] = p
    PINNED[f"avatar_name{name}"] = c
    PINNED[f"chat_inReplyNameText{name}"] = c
PINNED["avatar_backgroundSaved"] = CYAN
PINNED["avatar_background2Saved"] = CYAN
PINNED["avatar_backgroundArchived"] = OXBLOOD
PINNED["avatar_backgroundArchivedHidden"] = OXBLOOD

LINE = re.compile(r"^([A-Za-z0-9_]+)=(-?\d+|#[0-9a-fA-F]{6,8})$")


def to_argb(value):
    """attheme value (signed 32-bit int or #RRGGBB / #AARRGGBB) → (alpha, 'rrggbb')."""
    if value.startswith("#"):
        h = value[1:]
        if len(h) == 6:
            h = "ff" + h
        return int(h[:2], 16), h[2:].lower()
    n = int(value) & 0xFFFFFFFF
    return n >> 24, f"{n & 0xFFFFFF:06x}"


def fmt(alpha, rgb):
    return f"#{alpha:02x}{rgb}"


def pinned(spec):
    """'rrggbb' or 'aarrggbb' → '#aarrggbb'."""
    return "#" + (spec if len(spec) == 8 else "ff" + spec)


def main():
    src, out = sys.argv[1], sys.argv[2]
    wallpaper = sys.argv[3] if len(sys.argv) > 3 else None
    lines, seen = [], set()
    for raw in open(src, encoding="utf-8"):
        m = LINE.match(raw.strip())
        if not m:
            continue
        key, value = m.groups()
        seen.add(key)
        if key in PINNED:
            lines.append(f"{key}={pinned(PINNED[key])}")
            continue
        alpha, rgb = to_argb(value)
        lines.append(f"{key}={fmt(alpha, remap(rgb))}")
    # Pinned keys the night theme doesn't set (Telegram ignores unknown keys)
    for key, spec in PINNED.items():
        if key not in seen:
            lines.append(f"{key}={pinned(spec)}")

    with open(out, "wb") as f:
        f.write(("\n".join(lines) + "\n").encode())
        if wallpaper:
            # Telegram reads an embedded wallpaper between WPS and WPE
            f.write(b"WPS\n" + pathlib.Path(wallpaper).read_bytes() + b"\nWPE\n")
    print(f"{out}: {len(lines)} colours ({len(PINNED)} pinned)" + (" + wallpaper" if wallpaper else ""))


if __name__ == "__main__":
    main()
