#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
user_bin="${HOME}/.local/bin"
omarchy_config="${HOME}/.config/omarchy"
hypr_config="${HOME}/.config/hypr"
user_systemd="${HOME}/.config/systemd/user"
force_config=false

if [[ "${1:-}" == "--force-config" ]]; then
  force_config=true
elif [[ $# -gt 0 ]]; then
  echo "Usage: ./install.sh [--force-config]" >&2
  exit 2
fi

for command in python3 hyprctl systemctl systemd-run wtype rsvg-convert brightnessctl wpctl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing required command: $command" >&2
    exit 1
  fi
done

if ! command -v tiny-dfr >/dev/null 2>&1; then
  echo "Missing tiny-dfr. Install it before running this installer." >&2
  exit 1
fi

install -d "$user_bin" "$omarchy_config" "$omarchy_config/hooks/theme-set.d" "$hypr_config" "$user_systemd"
install -m 0755 "$project_dir/src/omarchy-touchbar" "$user_bin/omarchy-touchbar"
install -m 0755 "$project_dir/src/omarchy-chatgpt-dictate" "$user_bin/omarchy-chatgpt-dictate"
install -m 0755 "$project_dir/integration/theme-set-touchbar" \
  "$omarchy_config/hooks/theme-set.d/touchbar"
install -m 0644 "$project_dir/integration/omarchy-touchbar.service" \
  "$user_systemd/omarchy-touchbar.service"

if $force_config || [[ ! -e "$omarchy_config/touchbar.toml" ]]; then
  install -m 0644 "$project_dir/config/touchbar.toml" "$omarchy_config/touchbar.toml"
else
  install -m 0644 "$project_dir/config/touchbar.toml" "$omarchy_config/touchbar.toml.dist"
  echo "Kept existing touchbar.toml; repository version installed as touchbar.toml.dist."
fi

autostart="$hypr_config/autostart.lua"
touch "$autostart"
if ! grep -Fq 'omarchy-touchbar daemon' "$autostart"; then
  printf '\n-- Context-aware T2 MacBook Touch Bar.\n' >> "$autostart"
  printf 'o.launch_on_start("systemctl --user start omarchy-touchbar.service")\n' >> "$autostart"
elif grep -Fq 'systemd-run --user --unit=omarchy-touchbar' "$autostart"; then
  # Replace the transient launcher with the enabled persistent user unit.
  sed -i 's|o.launch_on_start("systemd-run --user --unit=omarchy-touchbar --collect " .. os.getenv("HOME") .. "/.local/bin/omarchy-touchbar daemon")|o.launch_on_start("systemctl --user start omarchy-touchbar.service")|' "$autostart"
elif ! grep -Fq 'systemctl --user start omarchy-touchbar.service' "$autostart"; then
  # Migrate a pre-unit bare launch so startup remains single-instance.
  sed -i 's|o.launch_on_start(os.getenv("HOME") .. "/.local/bin/omarchy-touchbar daemon")|o.launch_on_start("systemctl --user start omarchy-touchbar.service")|' "$autostart"
fi

bindings="$hypr_config/bindings.lua"
touch "$bindings"
if ! grep -Fq 'Touch Bar daemon-owned controls' "$bindings"; then
  cat >> "$bindings" <<'LUA'

-- Touch Bar daemon-owned controls use the raw touch surface, not F-keys.
for key = 13, 24 do
  hl.unbind("F" .. tostring(key))
end
LUA
fi

if [[ ! -d /etc/tiny-dfr || ! -w /etc/tiny-dfr ]]; then
  echo "Preparing /etc/tiny-dfr for live user-level rendering (sudo required)."
  sudo install -d -m 0755 -o "$(id -un)" -g "$(id -gn)" /etc/tiny-dfr /etc/tiny-dfr/gen
  sudo touch /etc/tiny-dfr/config.toml
  sudo chown "$(id -un):$(id -gn)" /etc/tiny-dfr/config.toml
fi

backlight_rule=/etc/udev/rules.d/99-touchbar-backlight.rules
if [[ ! -e $backlight_rule ]]; then
  echo "Allowing the session to hold the Touch Bar backlight on (sudo required)."
  sudo install -m 0644 "$project_dir/integration/99-touchbar-backlight.rules" "$backlight_rule"
  sudo udevadm control --reload-rules
  sudo chgrp input /sys/class/backlight/appletb_backlight/brightness
  sudo chmod g+w /sys/class/backlight/appletb_backlight/brightness
fi

panel_reset=/usr/local/lib/touchbar-panel-reset
if [[ ! -e $panel_reset ]] \
    || ! cmp -s "$project_dir/integration/touchbar-panel-reset" "$panel_reset"; then
  echo "Installing the post-resume Touch Bar display reset (sudo required)."
  sudo install -m 0755 "$project_dir/integration/touchbar-panel-reset" "$panel_reset"
  sudo install -m 0644 "$project_dir/integration/touchbar-panel-reset.service" \
    /etc/systemd/system/touchbar-panel-reset.service
  sudo systemctl daemon-reload
  sudo systemctl enable touchbar-panel-reset.service
fi

python3 -m py_compile "$user_bin/omarchy-touchbar" "$user_bin/omarchy-chatgpt-dictate"
python3 -c 'import tomllib, pathlib; tomllib.loads(pathlib.Path.home().joinpath(".config/omarchy/touchbar.toml").read_text())'

systemctl --user stop omarchy-touchbar.service 2>/dev/null || true
# Also reap any daemon launched outside the unit (pre-unit autostart entries).
pkill -f "$user_bin/omarchy-touchbar daemon" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable omarchy-touchbar.service >/dev/null
systemctl --user restart omarchy-touchbar.service
sudo systemctl restart tiny-dfr
hyprctl reload >/dev/null

echo "Omarchy Touch Bar installed and running."
echo "Run: omarchy-touchbar status"
