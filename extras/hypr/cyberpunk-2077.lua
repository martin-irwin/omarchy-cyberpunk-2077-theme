-- Cyberpunk 2077 theme extras, loaded from ~/.config/hypr/hyprland.lua by
-- the theme's install.sh. Safe to delete together with that require line.

-- o.rebind (replace an existing binding) arrived after Omarchy 4.0.6; where
-- it's missing, do what it does: drop the old binding, then bind the new one.
local function rebind(keys, description, dispatcher, options)
  if o.rebind then return o.rebind(keys, description, dispatcher, options) end
  if hl.unbind then pcall(hl.unbind, keys) end
  return o.bind(keys, description, dispatcher, options)
end

-- Super+Alt+Y: the Cyberdeck file browser (Yazi, Night City flavor).
o.bind("SUPER + ALT + Y", "Cyberdeck file browser", "cyberdeck")

-- Super+G: jack in. Opens the NETRUNNERS bar panel (cyberpunk.netrunners):
-- arrows pick a machine on your tailnet, Enter opens an SSH session to it.
-- Omarchy's window grouping moves from Super+G to Super+Ctrl+G.
rebind("SUPER + G", "Jack in (NETRUNNERS)", "omarchy-shell cyberpunk.netrunners toggle")
rebind("SUPER + CTRL + G", "Toggle window grouping", hl.dsp.group.toggle())

-- Super+Shift+Alt+G: WhatsApp as V's phone (Cyberphone) instead of
-- Omarchy's plain WhatsApp web app on the same key.
rebind("SUPER + SHIFT + ALT + G", "Cyberphone (WhatsApp)", "cyberphone")

-- jack sessions open in their own terminal window, floated like a deck
o.window("^cyberpunk\\.jack$", {
  float = true,
  center = true,
  size = { "monitor_w*0.6", "monitor_h*0.65" },
})

-- Float it centred like a terminal window on a desk in Night City, opaque.
-- Sized relative to the monitor so it fits on scaled displays too.
o.window("^cyberdeck\\.files$", { tag = "-default-opacity" })
o.window("^cyberdeck\\.files$", {
  float = true,
  center = true,
  size = { "monitor_w*0.85", "monitor_h*0.85" },
  opacity = "1 1",
})
