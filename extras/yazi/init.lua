-- Cyberdeck chrome: an in-universe badge in the header and a clock in the
-- status bar, styled like the computers in Cyberpunk 2077.
local CORAL, CYAN, INK = "#FF6159", "#5EF6FF", "#0D0B10"

Header:children_add(function()
	return ui.Line {
		ui.Span(" CYBERDECK "):fg(INK):bg(CORAL):bold(),
		ui.Span("◤ "):fg(CORAL),
	}
end, 100, Header.LEFT)

Header:children_add(function()
	local user = os.getenv("USER") or "v"
	return ui.Line {
		ui.Span(" ◥"):fg(CYAN),
		ui.Span(" NET//" .. string.upper(user) .. " "):fg(INK):bg(CYAN):bold(),
	}
end, 100, Header.RIGHT)

Status:children_add(function()
	return ui.Line {
		ui.Span(" ◥"):fg(CORAL),
		ui.Span(os.date(" %H:%M ")):fg(INK):bg(CORAL):bold(),
	}
end, 9000, Status.RIGHT)
