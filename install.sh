#!/bin/bash
# Cyberpunk 2077 for Omarchy: the parts a theme cannot do by itself.
#
# `omarchy theme install` only copies colours, shell styling and images. This
# script adds the rest, and every step can be skipped:
#
#   1. installs the bundled OFL fonts (Share Tech Mono, Rajdhani)
#   2. sets Share Tech Mono as the system monospace font     (--keep-font to skip)
#   3. downloads the official CDPR wallpapers from cyberpunk.net
#                                  (--all-wallpapers for posters/gangs/Edgerunners,
#                                   --no-wallpapers to skip)
#   4. installs the Cyberdeck file browser (Yazi + Night City flavor) on
#      Super+Alt+Y                                         (--no-cyberdeck to skip)
#   5. builds the Netrunner (cyan) and Samurai (yellow) colour variants, which
#      then appear in Omarchy's theme picker
#   6. re-applies the theme so the new wallpapers and font show up
#
#   ./install.sh --screensaver also sets the screensaver to the box-art logo
#                              (global, so opt-in; your current one is backed up)
#   ./install.sh --uninstall   undoes 1, 2, 4 and 5 (wallpapers are left in place)

set -euo pipefail

THEME_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
FONT_DIR="$HOME/.local/share/fonts/cyberpunk-2077"
BIN_DIR="$HOME/.local/bin"
HYPR_DIR="$HOME/.config/hypr"
STATE_DIR="$HOME/.local/state/omarchy-cyberpunk-2077"
MONO_FONT="Share Tech Mono"
REQUIRE_LINE='pcall(require, "hypr.cyberpunk-2077") -- Cyberpunk 2077 theme extras'
# omarchy theme set renders terminal, Hyprland and editor colours from
# $OMARCHY_PATH/default/themed; non-login shells (ssh, cron) may not set it.
if [[ -z ${OMARCHY_PATH:-} ]]; then
  for d in /usr/share/omarchy "$HOME/.local/share/omarchy"; do
    [[ -d $d/default/themed ]] && { export OMARCHY_PATH=$d; break; }
  done
fi

keep_font=0 wallpapers=core cyberdeck=1 uninstall=0 screensaver=0

while (( $# )); do
  case $1 in
    --keep-font) keep_font=1 ;;
    --all-wallpapers) wallpapers=all ;;
    --no-wallpapers) wallpapers=none ;;
    --no-cyberdeck) cyberdeck=0 ;;
    --screensaver) screensaver=1 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

say() { printf '\e[38;2;94;246;255m::\e[0m \e[38;2;255;97;89m%s\e[0m\n' "$*"; }

if (( uninstall )); then
  say "Removing Cyberdeck launcher and Hyprland extras"
  rm -f "$BIN_DIR/cyberdeck" "$BIN_DIR/cyberpunk-wallpapers" "$BIN_DIR/cyberpunk-variants" "$BIN_DIR/cyberpunk-ferdium" "$BIN_DIR/cyberpunk-screensaver" "$BIN_DIR/cyberphone" "$BIN_DIR/cyberslack" "$BIN_DIR/cyberpunk-telegram" "$HOME/.local/share/applications/cyberphone.desktop" "$HYPR_DIR/cyberpunk-2077.lua"
  "$THEME_DIR/extras/bin/cyberpunk-variants" --remove
  "$THEME_DIR/extras/bin/cyberpunk-screensaver" --restore 2>/dev/null || true
  "$THEME_DIR/extras/bin/cyberpunk-telegram" --remove >/dev/null 2>&1 || true
  [[ -f $HYPR_DIR/hyprland.lua ]] && sed -i '\#pcall(require, "hypr.cyberpunk-2077")#d' "$HYPR_DIR/hyprland.lua"

  if [[ -f $STATE_DIR/previous-font ]]; then
    previous=$(<"$STATE_DIR/previous-font")
    say "Restoring monospace font: $previous"
    omarchy font set "$previous" || true
  fi

  say "Removing fonts"
  rm -rf "$FONT_DIR"
  fc-cache -f >/dev/null
  rm -rf "$STATE_DIR"
  say "Done. Official wallpapers remain in ~/.config/omarchy/backgrounds/cyberpunk-2077/"
  exit 0
fi

mkdir -p "$STATE_DIR"

# 1. Fonts
say "Installing fonts (Share Tech Mono, Rajdhani; SIL Open Font License)"
mkdir -p "$FONT_DIR"
cp "$THEME_DIR"/fonts/*/*.ttf "$FONT_DIR/"
fc-cache -f "$FONT_DIR" >/dev/null

# 2. Monospace font (terminal, bar, menus)
if (( ! keep_font )); then
  current=$(omarchy font current 2>/dev/null || true)
  if [[ -n $current && $current != "$MONO_FONT" && ! -f $STATE_DIR/previous-font ]]; then
    echo "$current" >"$STATE_DIR/previous-font"
  fi
  say "Setting system monospace font to $MONO_FONT"
  omarchy font set "$MONO_FONT" >/dev/null 2>&1 || echo "   (could not set font; run: omarchy font set \"$MONO_FONT\")"
fi

# 3. Wallpapers
mkdir -p "$BIN_DIR"
ln -sfn "$THEME_DIR/extras/bin/cyberpunk-wallpapers" "$BIN_DIR/cyberpunk-wallpapers"
case $wallpapers in
  core) "$THEME_DIR/extras/bin/cyberpunk-wallpapers" || echo "   (wallpaper download failed; re-run: cyberpunk-wallpapers)" ;;
  all) "$THEME_DIR/extras/bin/cyberpunk-wallpapers" --all || echo "   (wallpaper download failed; re-run: cyberpunk-wallpapers --all)" ;;
esac

# 4. Cyberdeck file browser
if (( cyberdeck )); then
  say "Installing the Cyberdeck file browser (Super+Alt+Y)"
  if ! command -v yazi >/dev/null; then
    if [[ -t 0 ]]; then
      say "Yazi is not installed; installing it (needs your sudo password)"
      omarchy pkg add yazi || echo "   (install it later with: omarchy pkg add yazi)"
    else
      echo "   Yazi is not installed and there is no terminal to ask for sudo."
      echo "   Install it with: omarchy pkg add yazi"
    fi
  fi
  ln -sfn "$THEME_DIR/extras/bin/cyberdeck" "$BIN_DIR/cyberdeck"
  ln -sfn "$THEME_DIR/extras/hypr/cyberpunk-2077.lua" "$HYPR_DIR/cyberpunk-2077.lua"
  if [[ -f $HYPR_DIR/hyprland.lua ]] && ! grep -qF 'hypr.cyberpunk-2077' "$HYPR_DIR/hyprland.lua"; then
    printf '\n%s\n' "$REQUIRE_LINE" >>"$HYPR_DIR/hyprland.lua"
  fi
  hyprctl reload >/dev/null 2>&1 || true
fi

# 5. Colour variants
say "Building the Netrunner and Samurai colour variants"
ln -sfn "$THEME_DIR/extras/bin/cyberpunk-variants" "$BIN_DIR/cyberpunk-variants"
"$THEME_DIR/extras/bin/cyberpunk-variants" >/dev/null

# Cyberphone: WhatsApp as V's phone in its own window (opened on demand)
ln -sfn "$THEME_DIR/extras/bin/cyberphone" "$BIN_DIR/cyberphone"
"$THEME_DIR/extras/bin/cyberphone" --install >/dev/null

# Cyberslack: Slack web app with the Night City userstyle. Only the command is
# linked; run `cyberslack --install` yourself if you want the launcher entry.
ln -sfn "$THEME_DIR/extras/bin/cyberslack" "$BIN_DIR/cyberslack"

# Telegram Desktop in Rajdhani, if it is installed
ln -sfn "$THEME_DIR/extras/bin/cyberpunk-telegram" "$BIN_DIR/cyberpunk-telegram"
[[ -f /usr/share/applications/org.telegram.desktop.desktop ]] && "$THEME_DIR/extras/bin/cyberpunk-telegram" --install >/dev/null

# Ferdium WhatsApp skin, if Ferdium is set up on this machine
ln -sfn "$THEME_DIR/extras/bin/cyberpunk-ferdium" "$BIN_DIR/cyberpunk-ferdium"
if [[ -d $HOME/.config/Ferdium/recipes/whatsapp ]]; then
  say "Skinning WhatsApp in Ferdium"
  "$THEME_DIR/extras/bin/cyberpunk-ferdium" | sed 's/^/   /' || true
fi

# Screensaver (opt-in: it is global, not per theme)
ln -sfn "$THEME_DIR/extras/bin/cyberpunk-screensaver" "$BIN_DIR/cyberpunk-screensaver"
if (( screensaver )); then
  say "Setting the screensaver to the Cyberpunk 2077 logo"
  "$THEME_DIR/extras/bin/cyberpunk-screensaver" | sed 's/^/   /' || echo "   (failed; re-run: cyberpunk-screensaver)"
fi

# 6. Apply (keeps a variant if one is already in use)
current_theme=$(basename "$(readlink -f "$HOME/.local/state/omarchy/current/theme" 2>/dev/null)" 2>/dev/null || true)
[[ $current_theme == cyberpunk-2077-* ]] || current_theme=cyberpunk-2077
say "Applying theme"
omarchy theme set "$current_theme"

say "Wake up, samurai. We have a city to burn."
