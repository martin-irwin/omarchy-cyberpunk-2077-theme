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
#   5. re-applies the theme so the new wallpapers and font show up
#
#   ./install.sh --uninstall   undoes 1, 2 and 4 (wallpapers are left in place)

set -euo pipefail

THEME_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
FONT_DIR="$HOME/.local/share/fonts/cyberpunk-2077"
BIN_DIR="$HOME/.local/bin"
HYPR_DIR="$HOME/.config/hypr"
STATE_DIR="$HOME/.local/state/omarchy-cyberpunk-2077"
MONO_FONT="Share Tech Mono"
REQUIRE_LINE='pcall(require, "hypr.cyberpunk-2077") -- Cyberpunk 2077 theme extras'

keep_font=0 wallpapers=core cyberdeck=1 uninstall=0

while (( $# )); do
  case $1 in
    --keep-font) keep_font=1 ;;
    --all-wallpapers) wallpapers=all ;;
    --no-wallpapers) wallpapers=none ;;
    --no-cyberdeck) cyberdeck=0 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

say() { printf '\e[38;2;94;246;255m::\e[0m \e[38;2;255;97;89m%s\e[0m\n' "$*"; }

if (( uninstall )); then
  say "Removing Cyberdeck launcher and Hyprland extras"
  rm -f "$BIN_DIR/cyberdeck" "$BIN_DIR/cyberpunk-wallpapers" "$HYPR_DIR/cyberpunk-2077.lua"
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

# 5. Apply
say "Applying theme"
omarchy theme set cyberpunk-2077

say "Wake up, samurai. We have a city to burn."
