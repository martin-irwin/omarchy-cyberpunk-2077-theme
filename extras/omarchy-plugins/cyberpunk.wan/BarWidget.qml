import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// WAN reachability from one ping every intervalSec (default 30 s) to a fixed
// target (default 1.1.1.1). That ping is the only network traffic this widget
// makes. Click to check now.
//   WAN 21MS    the internet answered      (accent colour)
//   WAN SLOW    over 250 ms                (yellow)
//   WAN DOWN    no answer within 2 s       (urgent colour)
BarWidget {
  id: root
  moduleName: "cyberpunk.wan"

  // Only hostname/IP-shaped targets reach ping; anything else falls back.
  readonly property string target: {
    var t = String(setting("target", "1.1.1.1")).trim()
    return /^[A-Za-z0-9.:-]{1,253}$/.test(t) ? t : "1.1.1.1"
  }
  readonly property int intervalMs: Math.max(10, Math.min(3600, Number(setting("intervalSec", 30)) || 30)) * 1000

  property string state: "wait"   // wait | up | slow | down
  property real latency: -1

  readonly property string label: {
    if (state === "up" || state === "slow") return "WAN " + Math.round(latency) + "MS"
    if (state === "down") return "WAN DOWN"
    return "WAN …"
  }
  readonly property color tint: state === "down" ? Color.urgent
                              : state === "slow" ? "#F3E600"
                              : state === "up" ? Color.accent
                              : Color.muted

  implicitWidth: vertical ? barSize : readout.implicitWidth + Style.space(14)
  implicitHeight: vertical ? readout.implicitHeight + Style.space(8) : barSize

  function check() {
    pingProc.running = false
    pingProc.running = true
  }

  Process {
    id: pingProc
    command: ["/usr/bin/ping", "-n", "-c", "1", "-W", "2", root.target]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var m = /time[=<]([0-9.]+)\s*ms/.exec(String(text))
        if (m) {
          root.latency = Number(m[1])
          root.state = root.latency > 250 ? "slow" : "up"
        } else {
          root.state = "down"
        }
      }
    }
  }

  Timer {
    interval: root.intervalMs
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.check()
  }

  Text {
    id: readout
    anchors.centerIn: parent
    textFormat: Text.PlainText
    text: root.vertical ? (root.state === "down" ? "WAN\n✕" : "WAN\n" + (root.latency >= 0 ? Math.round(root.latency) : "…")) : root.label
    horizontalAlignment: Text.AlignHCenter
    color: root.tint
    font.family: root.bar ? root.bar.fontFamily : Style.font.family
    font.pixelSize: Style.font.bodySmall
    font.letterSpacing: 1
  }

  MouseArea {
    anchors.fill: parent
    cursorShape: Qt.PointingHandCursor
    onClicked: root.check()
  }
}
