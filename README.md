# Omarchy Touch Bar

A context-aware Touch Bar for Intel T2 MacBooks running Omarchy and Hyprland.
It uses `tiny-dfr` as the renderer and replaces a static function row with a
full-height, animated interface that follows the focused app.

## Highlights

- Raw-touch workspace picker showing each workspace's app, badged by number
- Browser controls and tab shortcuts with a collapsed workspace drawer
- App-aware layouts for terminals, Claude Code, ChatGPT, editors, Spotify,
  Discord, Obsidian, and general windows
- Always-available dictation while typing, with recording/transcribing states
- Native ChatGPT dictation plus Claude-style live model, context, output,
  turns, tools, elapsed-time, task, and rate-limit telemetry
- Claude Code read-out: live spinner with the running tool, context gauge,
  output, rolling 7-day and all-time token totals, expandable to full stats
- Animated SVG buttons colored from the active Omarchy theme
- Window launcher, media/function layer, app dock, and live battery/clock options
- Touch-safe rendering that prevents `tiny-dfr` reloads while a finger is down
- Fn-safe rendering that keeps classic brightness, keyboard-light, playback,
  microphone, search, and volume controls usable for the full key hold

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

## Claude Code

When a `claude` process is running under the focused window, the bar switches to
a live read-out of that session. Everything is read from
`~/.claude/projects/<cwd>/<session>.jsonl` and `~/.claude/sessions/<pid>.json`,
which Claude Code writes as it goes — no hooks and no changes to
`~/.claude/settings.json`.

Tapping any read-out tile expands it into a full stats page: session name,
model, permission mode, turns, elapsed, top tools, context, window, cached
tokens, and plan tier.

### Weekly usage

Anthropic does not publish your weekly allowance anywhere on disk — `/usage`
fetches it from the API at runtime. The `week` tile therefore reports the last
seven days of tokens counted from transcript timestamps, and `remaining` shows
`∞ no cap` until you give it a number to measure against:

```toml
[settings]
claude_weekly_budget = 500000000   # tokens; 0 disables the gauge
```

With a budget set, both tiles become percentage gauges that run green → yellow →
red as the week fills up.

## Architecture

`tiny-dfr` watches `/etc/tiny-dfr/config.toml`. The daemon watches Hyprland,
the raw Touch Bar digitizer, focused applications, Omarchy theme state,
Voxtype, Claude session logs, and Codex/ChatGPT activity. It generates colored
SVG controls and writes a stable 13-button layout to `tiny-dfr`.

Workspace, microphone, page, and app-dock controls are dispatched from the raw
touch surface. They do not use synthetic F-keys, which prevents workspace taps
from accidentally toggling dictation.
