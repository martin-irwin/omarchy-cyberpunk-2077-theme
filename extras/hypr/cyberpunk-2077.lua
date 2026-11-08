-- Cyberpunk 2077 theme extras, loaded from ~/.config/hypr/hyprland.lua by
-- the theme's install.sh. Safe to delete together with that require line.

-- Super+Alt+Y: the Cyberdeck file browser (Yazi, Night City flavor).
o.bind("SUPER + ALT + Y", "Cyberdeck file browser", "cyberdeck")

-- Float it centred like a terminal window on a desk in Night City, opaque.
-- Sized relative to the monitor so it fits on scaled displays too.
o.window("^cyberdeck\\.files$", { tag = "-default-opacity" })
o.window("^cyberdeck\\.files$", {
  float = true,
  center = true,
  size = { "monitor_w*0.85", "monitor_h*0.85" },
  opacity = "1 1",
})
