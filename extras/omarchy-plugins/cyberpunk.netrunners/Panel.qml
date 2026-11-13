import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "Model.js" as Model

// NETRUNNERS: every machine on your tailnet, the way the DIAGNOSTICS panel
// on kuroshi lists them. Data comes from `jack --json` (tailscale status plus
// a 5-minute uptime cache for watched hosts). Enter or a click jacks in over
// SSH in a new terminal; right-click copies the IP.
//
// Keys: Up/Down pick, Enter jack in, Esc close, Tab to the next panel.
// Super+G (theme keybinding) runs `omarchy-shell cyberpunk.netrunners toggle`.
Panel {
  id: root
  moduleName: "cyberpunk.netrunners"
  ipcTarget: "cyberpunk.netrunners"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root

  readonly property string home: Quickshell.env("HOME") || ""
  readonly property string jackPath: home + "/.local/bin/jack"
  readonly property var watch: Model.cleanWatch(setting("watch", []))
  readonly property int refreshMs: Math.max(15, Math.min(3600, Number(setting("refreshIntervalSec", 60)) || 60)) * 1000
  // Development only: a saved `tailscale status --json` to show instead.
  readonly property string statusFile: String(setting("statusFile", "")).replace(/[^A-Za-z0-9._\/-]/g, "")
  // Development only: a saved Tailscale API device list (via-host mode).
  readonly property string apiFile: String(setting("apiFile", "")).replace(/[^A-Za-z0-9._\/-]/g, "")
  // auto (detect a VM) | vm | metal — passed to jack as JACK_MACHINE
  readonly property string machine: {
    var m = String(setting("machine", "auto"))
    return (m === "vm" || m === "metal") ? m : "auto"
  }

  property var net: ({ self: { name: "", ip: "", state: "" }, peers: [] })
  property bool loaded: false
  property real nowMs: Date.now()
  property int selected: 0
  property bool switching: false   // a connect/disconnect is in flight

  readonly property var rows: Model.rows(net && net.peers ? net.peers : [], nowMs)
  readonly property int online: Model.onlineCount(net && net.peers ? net.peers : [])
  readonly property string selfIp: net && net.self ? net.self.ip : ""
  readonly property string tsState: net && net.self ? net.self.state : ""
  // A VM (this machine runs inside one, unless the "machine" setting says
  // otherwise) normally reaches the tailnet through its host's Tailscale.
  // Then jack reads the machine list from the Tailscale API (ViaHost) when a
  // read-only credential is set up, or has nothing to list (ViaHostNoApi).
  // Real installs get the full local Tailscale experience.
  readonly property bool isVm: net && net.self ? net.self.vm === true : false
  readonly property bool viaHost: tsState === "ViaHost"
  readonly property bool viaHostNoApi: tsState === "ViaHostNoApi"
  readonly property bool viaHostError: tsState === "ViaHostError"
  readonly property bool onLocalTailnet: tsState === "Running" && selfIp !== ""
  readonly property bool connected: onLocalTailnet || viaHost
  readonly property bool needsLogin: tsState === "NeedsLogin" || tsState === "NeedsMachineAuth"
  readonly property bool missing: tsState === "Missing"

  // Bar text, read by BarWidget.qml. Empty hides the widget: on a VM that
  // isn't on the tailnet itself there's no TSNET address to show, and the
  // host badge (or Super+G) opens the panel instead.
  readonly property string label: !loaded ? ""
    : onLocalTailnet ? "TSNET " + selfIp
    : isVm ? ""
    : missing ? "TSNET N/A"
    : needsLogin ? "TSNET LOGIN"
    : "TSNET OFF"

  function refresh() {
    nowMs = Date.now()
    statusProc.running = false
    statusProc.running = true
  }

  // CONNECT / LOG IN / JACK OUT. jack does the work: `tailscale up` (opening
  // the login page when this machine is logged out, and asking once via
  // pkexec to let this user control Tailscale) or `tailscale down`. Status is
  // re-read a few times while that settles.
  function setConnected(on) {
    if (!root.bar || root.missing) return
    root.switching = true
    root.bar.run("'" + root.jackPath + "' " + (on ? "--connect" : "--disconnect"))
    settleTimer.ticks = 0
    settleTimer.restart()
  }

  Timer {
    id: settleTimer
    property int ticks: 0
    interval: 3000
    repeat: true
    onTriggered: {
      ticks++
      root.refresh()
      if (ticks >= 10 || (ticks >= 2 && root.connected !== root._wasConnected)) {
        stop()
        root.switching = false
      }
    }
  }
  property bool _wasConnected: false
  onSwitchingChanged: if (switching) _wasConnected = connected

  function jackIn(row) {
    if (!row || !root.bar) return
    var name = Model.cleanName(row.name)
    if (!name) return
    root.close()
    root.bar.run("'" + root.jackPath + "' --term " + name)
  }

  function copyIp(row) {
    if (!row || !root.bar) return
    var ip = Model.cleanIp(row.ip)
    if (!ip) return
    root.bar.run("printf %s " + ip + " | wl-copy")
  }

  function move(delta) {
    if (rows.length === 0) return
    selected = Math.max(0, Math.min(rows.length - 1, selected + delta))
  }

  // ---- Panel lifecycle, as in omarchy.weather / kuroshi.zonebar
  property bool openedFromHotkey: false

  function setCenterHoverRevealSuppressed(value) {
    if (root.bar && typeof root.bar.setCenterHoverRevealSuppressed === "function")
      root.bar.setCenterHoverRevealSuppressed(value)
    else if (root.bar && "centerHoverRevealSuppressed" in root.bar)
      root.bar.centerHoverRevealSuppressed = value
  }

  function open() {
    openedFromHotkey = false
    setCenterHoverRevealSuppressed(false)
    root.selected = 0
    root.controller.show()
    root.refresh()
  }

  function openFromHotkey() {
    openedFromHotkey = true
    root.selected = 0
    root.controller.show()
    root.refresh()
    Qt.callLater(function() {
      if (root.opened) setCenterHoverRevealSuppressed(true)
    })
  }

  function close() {
    setCenterHoverRevealSuppressed(false)
    root.controller.hide()
  }

  function toggle() {
    if (root.opened) root.close()
    else root.openFromHotkey()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  onWatchChanged: Qt.callLater(root.refresh)

  Process {
    id: statusProc
    command: [root.jackPath, "--json"].concat(root.watch)
    environment: {
      var env = { "JACK_MACHINE": root.machine }
      if (root.statusFile !== "") env["JACK_STATUS_FILE"] = root.statusFile
      else if (root.apiFile !== "") env["JACK_API_FILE"] = root.apiFile
      return env
    }
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.net = Model.parse(text)
        root.loaded = true
        if (root.selected >= root.rows.length) root.selected = Math.max(0, root.rows.length - 1)
      }
    }
  }

  Timer {
    interval: root.refreshMs
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  IpcHandler {
    target: "cyberpunk.netrunners"

    function open(): void { root.openFromHotkey() }
    function close(): void { root.close() }
    function show(): void { root.openFromHotkey() }
    function hide(): void { root.close() }
    function toggle(): void { root.toggle() }
    function refresh(): void { root.refresh() }
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.barIdentity
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(380))
    contentHeight: panel.fittedContentHeight(column.implicitHeight)

    readonly property color fg: root.bar ? root.bar.foreground : Commons.Color.foreground
    readonly property string family: root.bar ? root.bar.fontFamily : Style.font.family

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onMoveRequested: function(dx, dy) { if (dy !== 0) root.move(dy) }
      onReturnRequested: {
        if (root.connected) root.jackIn(root.rows[root.selected])
        else if (!root.isVm && !root.missing && !root.switching) root.setConnected(true)
      }

      Column {
        id: column
        width: parent.width
        spacing: Style.space(4)

        Item {
          width: parent.width
          height: header.implicitHeight

          PanelSectionHeader {
            id: header
            anchors.left: parent.left
            foreground: panel.fg
            text: "NETRUNNERS"
          }

          Text {
            anchors.right: parent.right
            anchors.baseline: header.baseline
            textFormat: Text.PlainText
            text: root.onLocalTailnet
              ? root.online + " ONLINE  //  " + (root.net.self.name || "").toUpperCase() + " " + root.selfIp
              : root.viaHost ? root.online + " ONLINE  //  VIA HOST"
              : ""
            color: Commons.Color.accent
            font.family: panel.family
            font.pixelSize: Style.font.caption
          }
        }

        Text {
          visible: root.rows.length === 0
          width: parent.width
          wrapMode: Text.WordWrap
          textFormat: Text.PlainText
          text: !root.loaded ? "Scanning the net…"
              : root.viaHostError ? "Couldn't read your tailnet from the Tailscale API. Check ~/.config/jack/tailscale-oauth (run: jack --api-check)."
              : root.viaHostNoApi ? "This VM reaches the tailnet through its host, so there's no machine list here. Jack in by address (jack 100.x.y.z), or add a read-only Tailscale API credential to list machines (see the theme README)."
              : root.missing ? "Tailscale isn't installed on this deck."
              : root.needsLogin ? "This deck isn't logged in to your tailnet."
              : !root.connected ? "This deck is off the tailnet."
              : "No other machines on the tailnet."
          color: Qt.darker(panel.fg, 1.4)
          font.family: panel.family
          font.pixelSize: Style.font.bodySmall
        }

        // Big CONNECT / LOG IN button when this machine is off the tailnet
        Rectangle {
          id: connectButton
          // Real installs only: a VM uses its host's tunnel, so there's
          // nothing on this machine to connect.
          visible: root.loaded && !root.isVm && !root.connected && !root.missing
          width: parent.width
          height: Style.spacing.popupRowHeight
          radius: 0
          color: connectMouse.containsMouse || keyCatcher.activeFocus ? Commons.Color.accent : "transparent"
          border.width: 1
          border.color: Commons.Color.accent

          Text {
            anchors.centerIn: parent
            textFormat: Text.PlainText
            text: root.switching ? "JACKING IN…"
                : root.needsLogin ? "▶  LOG IN TO TAILNET"
                : "▶  CONNECT TO TAILNET"
            color: connectMouse.containsMouse || keyCatcher.activeFocus ? Commons.Color.background : Commons.Color.accent
            font.family: panel.family
            font.pixelSize: Style.font.body
            font.bold: true
            font.letterSpacing: 2
          }

          MouseArea {
            id: connectMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            enabled: !root.switching
            onClicked: root.setConnected(true)
          }
        }

        Repeater {
          model: root.rows

          Rectangle {
            id: row
            required property var modelData
            required property int index
            readonly property bool current: index === root.selected
            width: column.width
            height: Style.spacing.popupRowHeight
            radius: 0
            color: current ? Qt.rgba(Commons.Color.accent.r, Commons.Color.accent.g, Commons.Color.accent.b, 0.14)
                 : rowMouse.containsMouse ? Style.hoverFill : "transparent"

            // cyan bar on the left of the selected row, like the game's menus
            Rectangle {
              visible: row.current
              anchors.left: parent.left
              anchors.top: parent.top
              anchors.bottom: parent.bottom
              width: Style.space(3)
              color: Commons.Color.accent
            }

            Row {
              anchors.left: parent.left
              anchors.leftMargin: Style.space(10)
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(8)

              Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: Style.space(7)
                height: width
                color: row.modelData.online ? Commons.Color.accent : "transparent"
                border.width: row.modelData.online ? 0 : 1
                border.color: Qt.darker(panel.fg, 1.8)
              }

              Text {
                anchors.verticalCenter: parent.verticalCenter
                textFormat: Text.PlainText
                text: row.modelData.label + (row.modelData.watched ? "  ◆" : "")
                color: row.current ? Commons.Color.accent : panel.fg
                opacity: row.modelData.online ? 1.0 : 0.55
                font.family: panel.family
                font.pixelSize: Style.font.body
                font.letterSpacing: 1
              }
            }

            Row {
              anchors.right: parent.right
              anchors.rightMargin: Style.space(8)
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(8)

              Text {
                anchors.verticalCenter: parent.verticalCenter
                textFormat: Text.PlainText
                text: row.modelData.detail
                color: Qt.darker(panel.fg, 1.6)
                font.family: panel.family
                font.pixelSize: Style.font.caption
              }

              Text {
                anchors.verticalCenter: parent.verticalCenter
                textFormat: Text.PlainText
                text: row.modelData.status
                color: row.modelData.online ? Commons.Color.accent : Commons.Color.urgent
                font.family: panel.family
                font.pixelSize: Style.font.bodySmall
                font.bold: true
              }
            }

            MouseArea {
              id: rowMouse
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              acceptedButtons: Qt.LeftButton | Qt.RightButton
              onEntered: root.selected = row.index
              onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton) root.copyIp(row.modelData)
                else root.jackIn(row.modelData)
              }
            }
          }
        }

        Item {
          visible: root.connected
          width: parent.width
          // Two lines when JACK OUT shows: the hint spans the panel's width,
          // so sharing one line made the two overlap.
          height: footerHint.implicitHeight + Style.space(4)
                  + (jackOut.visible ? jackOut.implicitHeight + Style.space(6) : 0)

          // JACK OUT: take this machine off the tailnet (tailscale down).
          // Not shown via host: there's no local connection to drop.
          Text {
            id: jackOut
            visible: root.onLocalTailnet
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.topMargin: Style.space(4)
            textFormat: Text.PlainText
            text: root.switching ? "JACKING OUT…" : "◥ JACK OUT"
            color: jackOutMouse.containsMouse ? Commons.Color.urgent : Qt.darker(panel.fg, 1.5)
            font.family: panel.family
            font.pixelSize: Style.font.caption
            font.letterSpacing: 1

            MouseArea {
              id: jackOutMouse
              anchors.fill: parent
              anchors.margins: -Style.space(4)
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              enabled: !root.switching
              onClicked: root.setConnected(false)
            }
          }

          Text {
            id: footerHint
            visible: root.rows.length > 0
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            textFormat: Text.PlainText
            text: "ENTER JACK IN  ·  RIGHT-CLICK COPY IP  ·  ◆ WATCHED"
            color: Qt.darker(panel.fg, 1.8)
            font.family: panel.family
            font.pixelSize: Style.font.caption
            font.letterSpacing: 1
          }
        }
      }
    }
  }
}
