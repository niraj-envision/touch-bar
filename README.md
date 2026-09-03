# Omarchy Touch Bar

A context-aware Touch Bar for Intel T2 MacBooks running Omarchy and Hyprland.
It uses `tiny-dfr` as the renderer and replaces a static function row with a
full-height, themed interface that follows the focused app.

## Highlights

- **Follows the app.** Workspace picker with per-workspace app glyphs, live
  browser tabs with favicons and a swipeable strip, and shortcut rows for
  terminals, Claude Code, ChatGPT, editors, Spotify, Discord, Obsidian, and
  everything else.
- **Ring gauges everywhere a number has a ceiling.** Rate limits, context,
  battery, CPU, RAM, swap, temperature, fans and disk read as watch-style
  complications: a coloured ring, the value, and a caption.
- **Real sliders.** The controls page (tap **fn**) has Mac-style brightness,
  keyboard-light and volume sliders. Tap the track to jump, drag to sweep,
  tap the glyph to switch off or mute. The daemon resolves every touch from
  the raw digitizer, so the whole 60 px height is live.
- **Claude Code read-out.** An arc spinner names the running tool while a
  turn is in flight; idle, the tile names the model and opens a picker.
  Session, weekly and model-scoped rate limits with reset countdowns,
  context ring, lifetime tokens, and a full stats page one tap away.
- **Dictation on the bar.** Touch-Bar-only Voxtype dictation with a live
  two-sided microphone waveform, then Add / Send / Delete after transcription.
- **Media transport** with an animated equaliser and the current track title
  wherever something is playing, read from MPRIS.
- **System vitals page**: battery, CPU and load, RAM, swap, CPU temperature,
  fans, disk and uptime, refreshed while it is open.
- **Themed clock and battery tiles** (optional) that follow the Omarchy theme
  instead of tiny-dfr's plain white text.
- **Built-in Premier League centre.** A football page with live scores, the
  table, upcoming fixtures and your club's form, and a full-bar goal
  celebration (ball-to-net flight, scorer, clock and score) whenever a goal
  goes in. No companion app needed; if the
  [Football](https://github.com/niraj-envision/football) plugin is installed
  the two share one cache and one goal queue, and its terminal scorecard
  turns the bar into the live centre while it is focused.
- **Desktop settings.** `omarchy-touchbar-settings` (in the app launcher as
  "Touch Bar") edits the look, feature switches, per-app profiles and their
  buttons, and the football options, with a live preview of every page.
  Edits keep your config file's comments and apply on save.
- **Omarchy bar widget.** A pill in the shell bar shows what the Touch Bar is
  doing (page, dictation, Claude's tool, playing track), cycles pages on
  click, opens the controls on right click and toggles dictation on middle
  click. It offers to run the installer when the daemon is not set up.
- Every button is a generated SVG coloured from the active Omarchy theme,
  labels are set in a UI face with Nerd Font glyph fallback, and repaints are
  held while a finger is down so `tiny-dfr` never reloads mid-press.

## Requirements

- Omarchy with Hyprland
- A supported Apple T2 Touch Bar exposed through Linux input devices
- `tiny-dfr`
- Python 3.11 or newer
- `wtype`, `librsvg` (`rsvg-convert`), `brightnessctl`, `wpctl`
- GTK 4 and libadwaita with Python bindings (`python-gobject`) for the settings app
- [Voxtype](https://github.com/omarchy/omarchy) for Touch-Bar-only dictation

## Install

As an Omarchy plugin (adds the bar widget; click it to run the installer):

```bash
omarchy plugin add https://github.com/niraj-envision/touch-bar.git --enable
```

Or directly:

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

It installs the executables in `~/.local/bin`, enables a persistent
`omarchy-touchbar.service` user unit, adds a Hyprland startup safety check and
the Omarchy theme hook, and starts the daemon. It asks for `sudo` only to
prepare `/etc/tiny-dfr`, allow the session to hold the Touch Bar backlight,
and install the post-resume panel reset. `./uninstall.sh` reverses the
user-level parts.

## Commands

```bash
omarchy-touchbar status                 # JSON: page, dictation, media, Claude, last touch
omarchy-touchbar render                 # repaint once
omarchy-touchbar page next              # auto -> apps -> system -> football -> settings -> fn
omarchy-touchbar page auto|apps|system|football|settings|fn|workspaces
omarchy-touchbar voice toggle           # start/stop Touch-Bar dictation
omarchy-touchbar football table         # jump to a football view, or `refresh`
omarchy-touchbar settings               # open the settings window
omarchy-touchbar preview                # PNG mock-up of the smart bar
omarchy-touchbar preview system         # ...or any page, plus:
omarchy-touchbar preview football:table [out.png]   # any football view
omarchy-touchbar preview recording|review|goal [out.png]
```

The page cycle is on the mode button at the right end of the bar (its dots
show where you are). **fn** toggles the controls page from any page.

Edit `~/.config/omarchy/touchbar.toml` to tune profiles, icons, colours,
buttons, fonts, workspace count, brightness, clock, battery and animation.
Saving it triggers a live repaint.

## Controls and vitals

The **settings** page is the Mac-style control strip: brightness, keyboard
light and volume sliders, previous / play-pause / next, and mute. Sliders are
driven from the raw touch surface: a tap on the track sets the level, a drag
follows the finger live, and a tap on the glyph toggles the screen or
keyboard light off (and back to the previous level) or mutes the output.

The **system** page shows live machine vitals as ring gauges refreshed every
couple of seconds while open. Setting `battery = "percentage"` or
`clock = "%H:%M"` adds themed tiles next to the mode button; tapping either
opens the system page.

## Football

The **football** page is on the mode-button cycle (and opens by itself while
the Football plugin's scorecard is focused). Its first tile cycles four
views; swipe left or right to page through longer lists:

| View | Shows |
|---|---|
| live | every match in progress with clock and score; otherwise the latest results and next kick-offs |
| table | the 20 clubs with points and goal difference, Champions League and relegation places coloured, your club highlighted |
| fixtures | upcoming matches with local kick-off time and a countdown |
| club | league position ring, points, W-D-L, goals, last five results as form dots, next match and last result |

Every match tile carries both clubs' colours on its flanks. Data comes from
the public ESPN scoreboard and standings feeds (no key), polled every 25 s
while a match is on, once a minute around kick-off or while the page is
showing, and every five minutes otherwise. Pick your club under
`[football]` in the config or in the settings app; with nothing set, the
Football plugin's choice is used.

### Goal celebrations

When a new Premier League goal is observed, the bar temporarily uses all 13
stable cells as one continuous stadium scene. The ball flies into the net,
then the scorer and exact score remain visible for a total of five seconds.

Detection is built in and baselines silently on first run, so a restart never
replays an afternoon of goals. Goals are also accepted from the Football
plugin's inbox; both sources use the same goal ids and one acknowledgement
file, so a goal is shown exactly once whichever noticed it first. Delivery is
serial and durable: goals that arrive together are shown FIFO without
overlap, and an interrupted alert is replayed rather than lost.

## Settings app

```bash
omarchy-touchbar settings          # or launch "Touch Bar" from the app menu
omarchy-touchbar-settings apps     # open straight to a tab
```

Tabs: **Bar** (fonts, radius, animation, brightness, clock, battery, layout),
**Features** (dictation, media, Claude, ChatGPT, browser tabs, football,
celebrations), **Apps** (enable or disable each profile, edit its match
pattern, icon and shortcut buttons), **Football** (club, refresh rates) and
**Preview** (render any page as the panel draws it). Changes are written back
into `~/.config/omarchy/touchbar.toml` in place, comments included, and the
daemon repaints on save.

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
no API call and no contact with the OAuth token. The three rings show headroom
**remaining** with the reset countdown: the 5-hour session window, the weekly
limit, and the model-scoped weekly limit. They run green → yellow → red as
they fill; when the cache is more than an hour old the caption says `old`
(open `/usage` in Claude Code to refresh it).

If no model-scoped bucket is reported, the third ring falls back to a local
7-day token count, which you can turn into a percentage by setting a budget:

```toml
[settings]
claude_weekly_budget = 500000000   # tokens; 0 disables the gauge
```

## Architecture

`tiny-dfr` watches `/etc/tiny-dfr/config.toml`. The daemon watches Hyprland's
event socket, the raw Touch Bar digitizer, the Fn key, Omarchy theme state,
the football goal inbox, Voxtype, Claude session logs, MPRIS, and Codex/ChatGPT
activity. It generates coloured SVG controls and writes a stable 13-cell layout
to `tiny-dfr`.

Compositor state is cached and invalidated by Hyprland events, so the
pollers cost nothing between changes; generated SVGs are content-addressed and
pruned as an LRU so animated states never fill the disk. Workspace,
microphone, page, slider, and app-dock controls are dispatched from the raw
touch surface rather than synthetic F-keys, which prevents workspace taps from
accidentally toggling dictation.

## Development

```bash
python3 -m unittest discover -s tests
omarchy plugin validate .
omarchy-touchbar preview settings /tmp/settings.png
```

Deploy a change without sudo:

```bash
install -m 0755 src/omarchy-touchbar ~/.local/bin/omarchy-touchbar
systemctl --user restart omarchy-touchbar
```
