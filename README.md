# Omarchy Touch Bar

A context-aware Touch Bar for Intel T2 MacBooks running Omarchy and Hyprland.
It uses `tiny-dfr` as the renderer and replaces a static function row with a
full-height, animated interface that follows the focused app.

## Highlights

- Raw-touch workspace picker showing each workspace's app, badged by number
- Browser controls and tab shortcuts with a collapsed workspace drawer
- App-aware layouts for terminals, Claude Code, ChatGPT, editors, Spotify,
  Discord, Obsidian, and general windows
- Media transport with an animated equaliser wherever something is playing,
  read from MPRIS, with mute
- Always-available dictation while typing, with recording/transcribing states
- Native ChatGPT dictation plus Claude-style live model, context, output,
  turns, tools, elapsed-time, task, and rate-limit telemetry
- Claude Code read-out: live spinner with the running tool, real session/weekly/
  model rate-limit gauges with reset countdowns, context gauge, expandable to
  full session stats, with model and effort switchable from the panel
- Animated SVG buttons colored from the active Omarchy theme
- Full-panel Premier League goal celebrations with a ball-to-net flight,
  scorer, match clock, and current score
- Window launcher, media/function layer, app dock, and live battery/clock options
- Touch-safe rendering that prevents `tiny-dfr` reloads while a finger is down
- Full-height touch targets: every tap is resolved by the daemon from the raw
  digitizer, so buttons work edge to edge (tiny-dfr's own hit test ignores the
  top and bottom 10% of the panel)
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
omarchy-touchbar page system      # battery, CPU, load, RAM, swap, temp, fans
omarchy-touchbar page settings    # screen brightness, volume, keyboard backlight
omarchy-touchbar page fn
omarchy-touchbar preview
```

The **system** page shows live machine vitals (battery, CPU usage, load, RAM,
swap, CPU temperature, fan RPM) refreshed every couple of seconds while open.
The **settings** page adjusts screen brightness, output volume (with mute), and
keyboard backlight with −/+ buttons; levels come from sysfs and `wpctl`, so
changes made elsewhere (volume keys) show up live. Both are part of the page
cycle on the mode button.

Edit `~/.config/omarchy/touchbar.toml` to tune profiles, icons, colors, buttons,
workspace count, brightness, clock, battery, and animation settings. Saving it
triggers a live repaint.

## Football goal celebrations

When the [Football](https://github.com/niraj-envision/football) plugin observes
a new Premier League goal, the controller temporarily uses all 13 stable Touch
Bar cells as one continuous stadium scene. The ball flies into the net, then
the scorer and exact score remain visible for a total of five seconds.

Delivery is durable and serial: the football app records goals on disk, this
daemon acknowledges each one only after it has finished displaying, and goals
that arrive together are shown FIFO without overlap. Restarting the daemon may
replay an interrupted alert, but it cannot silently lose it.

## Claude Code

When a `claude` process is running under the focused window, the bar switches to
a live read-out of that session. Everything is read from
`~/.claude/projects/<cwd>/<session>.jsonl` and `~/.claude/sessions/<pid>.json`,
which Claude Code writes as it goes — no hooks and no changes to
`~/.claude/settings.json`.

Tapping any read-out tile expands it into a full stats page: model, effort,
permission mode, turns, elapsed, top tools, output, cached tokens, all-time
tokens, and plan tier.

On that page the **model** and **effort** tiles are doors — tap one to pick from
`opus / sonnet / haiku / fable` or `auto / low / medium / high / xhigh`. The
choice is applied by typing the matching `/model` or `/effort` command into the
prompt, so it is only offered while the session is idle; during a turn the
options render greyed out and do nothing.

### Rate limits

Claude Code refreshes its own `/usage` figures into `~/.claude.json` under
`cachedUsageUtilization`, so the bar reads the real numbers straight off disk —
no API call and no contact with the OAuth token. The three gauges show headroom
**remaining** with the reset countdown: the 5-hour session window, the weekly
limit, and the model-scoped weekly limit (currently Fable). They run green →
yellow → red as they fill, and grey out if the cache goes stale.

If no model-scoped bucket is reported, the third gauge falls back to a local
7-day token count, which you can turn into a percentage by setting a budget:

```toml
[settings]
claude_weekly_budget = 500000000   # tokens; 0 disables the gauge
```

## Architecture

`tiny-dfr` watches `/etc/tiny-dfr/config.toml`. The daemon watches Hyprland,
the raw Touch Bar digitizer, focused applications, Omarchy theme state,
the football goal inbox, Voxtype, Claude session logs, and Codex/ChatGPT
activity. It generates colored SVG controls and writes a stable 13-button
layout to `tiny-dfr`.

Workspace, microphone, page, and app-dock controls are dispatched from the raw
touch surface. They do not use synthetic F-keys, which prevents workspace taps
from accidentally toggling dictation.
