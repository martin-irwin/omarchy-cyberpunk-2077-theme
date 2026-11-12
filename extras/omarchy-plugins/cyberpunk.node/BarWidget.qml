import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// USER@HOST as a Night City HUD badge: background-coloured text on the
// accent colour, closed by the angled edge the game's menus use. Follows the
// theme's palette, so the Netrunner and Samurai variants recolour it too.
//
// Click: optics reboot. The name scrambles into glitch characters and decodes
// back letter by letter while the theme flips between the coral original
// and Netrunner (Samurai goes to coral). Right-click opens NETRUNNERS, the
// same panel as Super+G. Middle-click re-reads the host name.
BarWidget {
  id: root
  moduleName: "cyberpunk.node"

  readonly property bool showUser: !!setting("showUser", false)
  readonly property string user: String(Quickshell.env("USER") || "").toUpperCase()
  property string host: ""

  readonly property string realLabel: (showUser && user !== "" ? user + "@" : "") + host
  // While glitching, the scrambled text; otherwise the real name.
  property string glitchText: ""
  readonly property string label: glitchText !== "" ? glitchText : realLabel
  readonly property string shortLabel: host.slice(0, 2)

  visible: host !== ""
  implicitWidth: vertical ? barSize : badge.width + edge.width
  implicitHeight: vertical ? badge.height : barSize

  // The host name changes rarely; read it once, and again on a click.
  Process {
    id: hostProc
    command: ["cat", "/proc/sys/kernel/hostname"]
    running: true
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        // Only hostname-shaped text: letters, digits, dots and dashes.
        var h = String(text).trim().replace(/[^A-Za-z0-9.-]/g, "").slice(0, 40)
        root.host = h.toUpperCase()
      }
    }
  }

  Rectangle {
    id: badge
    anchors.verticalCenter: parent.verticalCenter
    x: 0
    height: Math.round(root.barSize * 0.72)
    width: label.implicitWidth + Style.space(12)
    color: Commons.Color.accent

    Text {
      id: label
      anchors.centerIn: parent
      textFormat: Text.PlainText
      text: root.vertical ? root.shortLabel : root.label
      color: Commons.Color.background
      font.family: root.bar ? root.bar.fontFamily : Style.font.family
      font.pixelSize: Style.font.bodySmall
      font.bold: true
      font.letterSpacing: 1
    }
  }

  // The angled edge: a right triangle in the accent colour, like ◤
  Canvas {
    id: edge
    visible: !root.vertical
    anchors.left: badge.right
    anchors.top: badge.top
    width: Math.round(badge.height * 0.55)
    height: badge.height
    onPaint: {
      var ctx = getContext("2d")
      ctx.reset()
      ctx.fillStyle = Commons.Color.accent
      ctx.beginPath()
      ctx.moveTo(0, 0)
      ctx.lineTo(width, 0)
      ctx.lineTo(0, height)
      ctx.closePath()
      ctx.fill()
    }
    Connections {
      target: Commons.Color
      function onAccentChanged() { edge.requestPaint() }
    }
  }

  // ── optics reboot ─────────────────────────────────────────────────────
  readonly property string glyphs: "#%&@$<>/\\|=+*01░▒▓"
  property int tick: 0
  readonly property int ticks: 18                 // × 45 ms ≈ 0.8 s
  readonly property bool glitching: glitchTimer.running

  function scramble() {
    // Letters left of the decode point are back; the rest are noise.
    var real = root.realLabel, out = ""
    var revealed = Math.floor(real.length * Math.max(0, tick - 6) / (ticks - 6))
    for (var i = 0; i < real.length; i++) {
      if (i < revealed || real[i] === "-" && Math.random() < 0.5) out += real[i]
      else out += glyphs[Math.floor(Math.random() * glyphs.length)]
    }
    return out
  }

  Timer {
    id: glitchTimer
    interval: 45
    repeat: true
    onTriggered: {
      root.tick += 1
      if (root.tick >= root.ticks) {
        stop()
        root.glitchText = ""
        badge.opacity = 1
        badge.x = 0
        return
      }
      root.glitchText = root.scramble()
      // flicker and jitter like a bad signal, settling as it decodes
      var calm = root.tick / root.ticks
      badge.opacity = Math.random() < 0.25 * (1 - calm) ? 0.35 : 1
      badge.x = Math.random() < 0.4 * (1 - calm) ? (Math.random() < 0.5 ? -2 : 2) : 0
    }
  }

  // Which theme to flip to: read Omarchy's current theme name, then set.
  Process {
    id: flipProc
    command: ["sh", "-c",
      "t=$(cat \"$HOME/.local/state/omarchy/current/theme.name\" 2>/dev/null); " +
      "case $t in cyberpunk-2077-netrunner) n=cyberpunk-2077 ;; cyberpunk-2077) n=cyberpunk-2077-netrunner ;; *) n=cyberpunk-2077 ;; esac; " +
      "omarchy theme set \"$n\" >/dev/null 2>&1"]
  }

  function opticsReboot() {
    if (glitching) return
    tick = 0
    glitchText = scramble()
    glitchTimer.start()
    if (!flipProc.running) flipProc.running = true
  }

  MouseArea {
    anchors.fill: parent
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
    onClicked: function(mouse) {
      if (mouse.button === Qt.MiddleButton) {
        hostProc.running = false
        hostProc.running = true
      } else if (mouse.button === Qt.RightButton) {
        if (root.bar) root.bar.run("omarchy-shell cyberpunk.netrunners toggle")
      } else {
        root.opticsReboot()
      }
    }
  }
}
