import QtQuick
import qs.Commons
import qs.Ui

// Bar slot for NETRUNNERS: shows `TSNET <ip>` read off Panel.qml, which owns
// all state, and hosts the panel (same split as omarchy.weather).
BarWidget {
  id: root
  moduleName: "cyberpunk.netrunners"

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
  }

  readonly property string displayText: panelLoader.item ? panelLoader.item.label : ""
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false
  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function open() { if (panelLoader.item) panelLoader.item.openFromHotkey() }
  function close() { if (panelLoader.item) panelLoader.item.close() }
  function closeForPopoutSwitch() { if (panelLoader.item) panelLoader.item.closeForPopoutSwitch() }

  // With no label (a VM using its host's Tailscale) the widget collapses to
  // zero width but stays on the bar: it's still where the panel opens from
  // when the host badge or Super+G asks for it.
  readonly property bool shown: displayText !== ""
  implicitWidth: shown ? button.implicitWidth : 0
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    visible: root.shown
    bar: root.bar
    text: root.vertical ? "TS" : root.displayText
    // cyan like kuroshi's TSNET readout (follows the theme's accent)
    foreground: Color.accent
    horizontalMargin: 8.75
    verticalPadding: 8.75
    tooltipText: ""

    onPressed: function(b) {
      if (!panelLoader.item) return
      if (b === Qt.MiddleButton) panelLoader.item.refresh()
      else panelLoader.item.toggle()
    }
  }
}
