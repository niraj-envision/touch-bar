# Omarchy Touch Bar

A context-aware Touch Bar for Intel T2 MacBooks running Omarchy and Hyprland.
It uses `tiny-dfr` as the renderer and replaces a static function row with a
full-height, animated interface that follows the focused app.

## Highlights

- Reliable raw-touch workspace picker for Omarchy workspaces 1–5
- Browser controls and tab shortcuts with a collapsed workspace drawer
- App-aware layouts for terminals, Claude Code, ChatGPT, editors, Spotify,
  Discord, Obsidian, and general windows
- Always-available dictation while typing, with recording/transcribing states
- Native ChatGPT dictation when its accessible control is available
- Claude-aware session activity, context, output, turn, and tool indicators
- Animated SVG buttons colored from the active Omarchy theme
- Window launcher, media/function layer, app dock, and live battery/clock options
- Touch-safe rendering that prevents `tiny-dfr` reloads while a finger is down

## Requirements

- Omarchy with Hyprland
- A supported Apple T2 Touch Bar exposed through Linux input devices
- `tiny-dfr`
- Python 3.11 or newer
- `wtype` and `librsvg` (`rsvg-convert`)
- [Voxtype](https://github.com/omarchy/omarchy) for system dictation fallback
- Optional: Python GObject/AT-SPI bindings for ChatGPT-native dictation

## Install

```bash
git clone https://github.com/niraj-envision/touch-bar.git
cd touch-bar
./install.sh
```

The installer preserves an existing `~/.config/omarchy/touchbar.toml`. To
replace it with the repository configuration:

```bash
./install.sh --force-config
```

It installs the executable files in `~/.local/bin`, adds the daemon to
`~/.config/hypr/autostart.lua`, adds the Omarchy theme hook, and starts the
user daemon. It may ask for `sudo` only to prepare `/etc/tiny-dfr` and restart
the system `tiny-dfr` service.

## Commands

```bash
omarchy-touchbar status
omarchy-touchbar render
omarchy-touchbar page auto
omarchy-touchbar page workspaces
omarchy-touchbar page fn
omarchy-touchbar preview
```

Edit `~/.config/omarchy/touchbar.toml` to tune profiles, icons, colors, buttons,
workspace count, brightness, clock, battery, and animation settings. Saving it
triggers a live repaint.

## Architecture

`tiny-dfr` watches `/etc/tiny-dfr/config.toml`. The daemon watches Hyprland,
the raw Touch Bar digitizer, focused applications, Omarchy theme state,
Voxtype, Claude session logs, and Codex/ChatGPT activity. It generates colored
SVG controls and writes a stable 13-button layout to `tiny-dfr`.

Workspace, microphone, page, and app-dock controls are dispatched from the raw
touch surface. They do not use synthetic F-keys, which prevents workspace taps
from accidentally toggling dictation.

