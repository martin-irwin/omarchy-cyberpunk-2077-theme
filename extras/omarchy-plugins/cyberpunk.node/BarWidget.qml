import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// USER@HOST as a Night City HUD badge: background-coloured text on the
// accent colour, closed by the angled edge the game's menus use. Follows the
// theme's palette, so the Netrunner and Samurai variants recolour it too.
// Clicking it opens the NETRUNNERS panel (cyberpunk.netrunners).
BarWidget {
  id: root
  moduleName: "cyberpunk.node"

  readonly property bool showUser: !!setting("showUser", false)
  readonly property string user: String(Quickshell.env("USER") || "").toUpperCase()
  property string host: ""

  readonly property string label: (showUser && user !== "" ? user + "@" : "") + host
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
    color: Color.accent

    Text {
      id: label
      anchors.centerIn: parent
      textFormat: Text.PlainText
      text: root.vertical ? root.shortLabel : root.label
      color: Color.background
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
      ctx.fillStyle = Color.accent
      ctx.beginPath()
      ctx.moveTo(0, 0)
      ctx.lineTo(width, 0)
      ctx.lineTo(0, height)
      ctx.closePath()
      ctx.fill()
    }
    Connections {
      target: Color
      function onAccentChanged() { edge.requestPaint() }
    }
  }

  MouseArea {
    anchors.fill: parent
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton | Qt.MiddleButton
    onClicked: function(mouse) {
      if (mouse.button === Qt.MiddleButton) {
        hostProc.running = false
        hostProc.running = true
      } else if (root.bar) {
        root.bar.run("omarchy-shell cyberpunk.netrunners toggle")
      }
    }
  }
}
