import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// The Touch Bar's seat in the Omarchy bar.
//
// Everything it shows comes from `omarchy-touchbar status`, a cheap local
// socket round-trip that the daemon answers from memory. Left click cycles
// the Touch Bar's pages, right click opens the hardware controls, middle
// click starts or stops Touch-Bar dictation. When the daemon is not
// installed yet, the pill offers to run the installer in a terminal.
BarWidget {
  id: root
  moduleName: "io.github.niraj-envision.touch-bar"

  property string page: ""
  property string voice: "idle"
  property bool claudeBusy: false
  property string claudeTool: ""
  property string mediaTitle: ""
  property bool mediaPlaying: false
  property bool running: false
  property bool installed: false

  readonly property string binPath: Quickshell.env("HOME") + "/.local/bin/omarchy-touchbar"
  readonly property string installPath: Qt.resolvedUrl("install.sh").toString().replace(/^file:\/\//, "")
  readonly property bool showLabel: setting("showLabel", true) !== false
  readonly property int pollInterval: Math.min(60, Math.max(1, Number(setting("pollInterval", 3)))) * 1000

  readonly property bool recording: voice === "recording"
  readonly property bool transcribing: voice === "transcribing"
  readonly property bool live: recording || transcribing || claudeBusy

  readonly property string icon: recording ? ""           // microphone
    : transcribing ? ""                                    // spinner
    : claudeBusy ? "󰊩"                                // robot
    : mediaPlaying ? ""                                    // music
    : ""                                                   // keyboard

  readonly property string pageName: ({
    "auto": "smart", "apps": "apps", "system": "vitals", "settings": "controls",
    "fn": "F-keys", "workspaces": "workspaces", "claude": "claude",
    "models": "model", "efforts": "effort", "chatgpt": "chatgpt"
  })[page] || page

  readonly property string label: !installed ? "Touch Bar · setup"
    : !running ? "Touch Bar · off"
    : recording ? "listening"
    : transcribing ? "transcribing"
    : claudeBusy ? (claudeTool !== "" ? claudeTool.toLowerCase() : "thinking")
    : mediaPlaying && mediaTitle !== "" ? mediaTitle.slice(0, 28)
    : pageName

  readonly property string displayText: showLabel && !vertical ? icon + "  " + label : icon
  readonly property string tooltip: !installed
    ? "Install the Omarchy Touch Bar daemon"
    : !running ? "Touch Bar daemon is not running (click to start)"
    : "Touch Bar · " + pageName + "\nLeft: next page · Right: controls · Middle: dictate"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function refresh() {
    if (!statusProbe.running) statusProbe.running = true
  }

  function send(args) {
    if (!installed) { install(); return }
    if (!running) { starter.running = true; return }
    commandProc.command = [root.binPath].concat(args)
    commandProc.running = true
  }

  function install() {
    if (!installerProc.running) installerProc.running = true
  }

  Process {
    id: statusProbe
    command: ["/bin/bash", "-c", "test -x \"$1\" || exit 3; \"$1\" status", "--", root.binPath]
    running: true
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var raw = String(text || "").trim()
        if (raw === "" || raw.length > 65536) return
        try {
          var data = JSON.parse(raw)
          root.page = String(data.page || "auto").slice(0, 16)
          root.voice = String(data.voice || "idle").slice(0, 16)
          var claude = data.claude || null
          root.claudeBusy = !!(claude && claude.busy)
          root.claudeTool = claude ? String(claude.tool || "").slice(0, 24) : ""
          var media = data.media || null
          root.mediaPlaying = !!(media && media.status === "Playing")
          root.mediaTitle = media ? String(media.title || "").slice(0, 80) : ""
          root.running = true
        } catch (e) {
          // Keep the previous reading on a partial line.
        }
      }
    }
    onExited: function(exitCode) {
      if (exitCode === 3) { root.installed = false; root.running = false }
      else if (exitCode !== 0) { root.installed = true; root.running = false }
      else root.installed = true
    }
  }

  Timer {
    interval: 4000
    repeat: false
    running: statusProbe.running
    onTriggered: statusProbe.running = false
  }

  Process { id: commandProc; onExited: function() { root.refresh() } }

  Process {
    id: settingsProc
    command: ["/usr/bin/setsid", "uwsm-app", "--", "omarchy-touchbar-settings"]
  }

  Process {
    id: starter
    command: ["systemctl", "--user", "start", "omarchy-touchbar.service"]
    onExited: function() { root.refresh() }
  }

  Process {
    id: installerProc
    command: [
      "/usr/bin/setsid", "uwsm-app", "--", "xdg-terminal-exec",
      "--app-id=org.omarchy.terminal", "--title=Touch Bar Setup",
      "-e", "/bin/bash", root.installPath
    ]
    onExited: function() { root.refresh() }
  }

  Timer {
    interval: root.live ? 1000 : root.pollInterval
    running: true
    repeat: true
    onTriggered: root.refresh()
  }

  IpcHandler {
    target: "io.github.niraj-envision.touch-bar"

    function refresh(): void { root.refresh() }
    function next(): void { root.send(["page", "next"]) }
    function page(name: string): void { root.send(["page", name]) }
    function dictate(): void { root.send(["voice", "toggle"]) }
    function settings(): void { settingsProc.running = true }
    function status(): string { return root.label }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.displayText
    labelVisible: !root.vertical
    hasVisualContent: true
    horizontalMargin: 8.75
    verticalPadding: 8.75
    tooltipText: root.tooltip
    active: root.live || !root.installed
    activeColor: root.recording ? (root.bar ? root.bar.urgent : Color.urgent) : Color.accent
    foreground: root.bar ? root.bar.barForeground : Color.foreground

    onPressed: function(b) {
      if (b === Qt.RightButton) root.send(["page", "settings"])
      else if (b === Qt.MiddleButton) root.send(["voice", "toggle"])
      else root.send(["page", "next"])
    }

    Column {
      visible: root.vertical
      anchors.fill: parent

      OpticalGlyph {
        width: button.width
        height: Style.bar.iconSlot
        text: root.icon
        fontFamily: button.fontFamily
        fontSize: button.fontSize
        color: button.foreground
      }
    }
  }
}
