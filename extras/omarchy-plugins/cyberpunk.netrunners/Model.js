.pragma library

// Pure helpers for NETRUNNERS: parse `jack --json`, build panel rows.
// Everything from the subprocess is treated as untrusted and re-validated
// here, even though jack already strips it to safe characters.

var NAME_RE = /^[a-z0-9-]{1,63}$/
var IP_RE = /^[0-9a-f.:]{2,45}$/

function cleanName(s) { s = String(s || ""); return NAME_RE.test(s) ? s : "" }
function cleanIp(s) { s = String(s || ""); return IP_RE.test(s) ? s : "" }
function cleanToken(s, max) { return String(s || "").replace(/[^A-Za-z0-9 ]/g, "").slice(0, max || 16) }

function parse(text) {
  var out = { self: { name: "", ip: "" }, peers: [] }
  var data
  try { data = JSON.parse(String(text || "")) } catch (e) { return out }
  if (!data || typeof data !== "object") return out
  if (data.self) out.self = { name: cleanName(data.self.name), ip: cleanIp(data.self.ip) }
  var peers = Array.isArray(data.peers) ? data.peers.slice(0, 200) : []
  for (var i = 0; i < peers.length; i++) {
    var p = peers[i] || {}
    var name = cleanName(p.name), ip = cleanIp(p.ip)
    if (!name || !ip) continue
    out.peers.push({
      name: name,
      ip: ip,
      os: cleanToken(p.os, 12),
      online: p.online === true,
      seen: String(p.seen || "").replace(/[^0-9TZ:.+-]/g, "").slice(0, 40),
      uptime: cleanToken(p.uptime, 12),
      watched: p.watched === true
    })
  }
  return out
}

// "2026-11-08T19:28:10Z" → "4H AGO" (Tailscale uses year 1 for "never")
function ago(iso, nowMs) {
  var t = Date.parse(iso)
  if (!isFinite(t) || t < 86400000) return ""
  var s = Math.max(0, Math.floor((nowMs - t) / 1000))
  if (s < 90) return "JUST NOW"
  if (s < 5400) return Math.round(s / 60) + "M AGO"
  if (s < 172800) return Math.round(s / 3600) + "H AGO"
  return Math.round(s / 86400) + "D AGO"
}

// Watched first, then online, then by name.
function rows(peers, nowMs) {
  var list = peers.slice()
  list.sort(function(a, b) {
    if (a.watched !== b.watched) return a.watched ? -1 : 1
    if (a.online !== b.online) return a.online ? -1 : 1
    return a.name < b.name ? -1 : a.name > b.name ? 1 : 0
  })
  return list.map(function(p) {
    var status, detail
    if (p.online) {
      status = p.uptime ? "UP " + p.uptime.toUpperCase() : "ONLINE"
      detail = p.os.toUpperCase()
    } else {
      status = "OFFLINE"
      detail = ago(p.seen, nowMs)
    }
    return {
      name: p.name,
      label: p.name.toUpperCase(),
      ip: p.ip,
      online: p.online,
      watched: p.watched,
      status: status,
      detail: detail
    }
  })
}

function onlineCount(peers) {
  var n = 0
  for (var i = 0; i < peers.length; i++) if (peers[i].online) n++
  return n
}

function cleanWatch(list) {
  if (!Array.isArray(list)) return []
  var out = []
  for (var i = 0; i < list.length && out.length < 32; i++) {
    var n = cleanName(String(list[i] || "").toLowerCase())
    if (n && out.indexOf(n) < 0) out.push(n)
  }
  return out
}
