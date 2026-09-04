#!/usr/bin/bash
set -euo pipefail

script_path=${BASH_SOURCE[0]}
[[ $script_path == /* ]] || script_path=$PWD/$script_path
project_dir=$(cd -- "${script_path%/*}" && pwd -P)
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

required_commands=(
  /usr/bin/python3 /usr/bin/hyprctl /usr/bin/systemctl /usr/bin/wtype
  /usr/bin/rsvg-convert /usr/bin/brightnessctl /usr/bin/wpctl
)
for command_path in "${required_commands[@]}"; do
  if [[ ! -x $command_path ]]; then
    echo "Missing required command: $command_path" >&2
    exit 1
  fi
done

if [[ ! -x /usr/bin/tiny-dfr ]]; then
  echo "Missing tiny-dfr. Install it before running this installer." >&2
  exit 1
fi

/usr/bin/install -d "$user_bin" "$omarchy_config" "$omarchy_config/hooks/theme-set.d" "$hypr_config" "$user_systemd"
/usr/bin/install -m 0755 "$project_dir/src/omarchy-touchbar" "$user_bin/omarchy-touchbar"
/usr/bin/install -m 0755 "$project_dir/src/omarchy-chatgpt-dictate" "$user_bin/omarchy-chatgpt-dictate"
/usr/bin/install -m 0755 "$project_dir/src/omarchy-touchbar-settings" "$user_bin/omarchy-touchbar-settings"
/usr/bin/install -d "${HOME}/.local/share/applications"
/usr/bin/install -m 0644 "$project_dir/integration/omarchy-touchbar-settings.desktop" \
  "${HOME}/.local/share/applications/omarchy-touchbar-settings.desktop"
/usr/bin/install -m 0755 "$project_dir/integration/theme-set-touchbar" \
  "$omarchy_config/hooks/theme-set.d/touchbar"
/usr/bin/install -m 0644 "$project_dir/integration/omarchy-touchbar.service" \
  "$user_systemd/omarchy-touchbar.service"

if $force_config || [[ ! -e "$omarchy_config/touchbar.toml" ]]; then
  /usr/bin/install -m 0644 "$project_dir/config/touchbar.toml" "$omarchy_config/touchbar.toml"
else
  /usr/bin/install -m 0644 "$project_dir/config/touchbar.toml" "$omarchy_config/touchbar.toml.dist"
  echo "Kept existing touchbar.toml; repository version installed as touchbar.toml.dist."
fi

autostart="$hypr_config/autostart.lua"
/usr/bin/touch "$autostart"
if /usr/bin/grep -Fq 'o.launch_on_start("systemctl --user start omarchy-touchbar.service")' "$autostart"; then
  /usr/bin/sed -i 's|o.launch_on_start("systemctl --user start omarchy-touchbar.service")|o.launch_on_start("/usr/bin/systemctl --user start omarchy-touchbar.service")|' "$autostart"
elif /usr/bin/grep -Fq 'o.launch_on_start("/usr/bin/systemctl --user start omarchy-touchbar.service")' "$autostart"; then
  :
elif /usr/bin/grep -Fq 'systemd-run --user --unit=omarchy-touchbar' "$autostart"; then
  /usr/bin/sed -i 's|o.launch_on_start("systemd-run --user --unit=omarchy-touchbar --collect " .. os.getenv("HOME") .. "/.local/bin/omarchy-touchbar daemon")|o.launch_on_start("/usr/bin/systemctl --user start omarchy-touchbar.service")|' "$autostart"
elif /usr/bin/grep -Fq 'omarchy-touchbar daemon' "$autostart"; then
  /usr/bin/sed -i 's|o.launch_on_start(os.getenv("HOME") .. "/.local/bin/omarchy-touchbar daemon")|o.launch_on_start("/usr/bin/systemctl --user start omarchy-touchbar.service")|' "$autostart"
else
  printf '\n-- Context-aware T2 MacBook Touch Bar.\n' >> "$autostart"
  printf 'o.launch_on_start("/usr/bin/systemctl --user start omarchy-touchbar.service")\n' >> "$autostart"
fi

bindings="$hypr_config/bindings.lua"
/usr/bin/touch "$bindings"
if ! /usr/bin/grep -Fq 'Touch Bar daemon-owned controls' "$bindings"; then
  while IFS= read -r line; do printf '%s\n' "$line"; done >> "$bindings" <<'LUA'

-- Touch Bar daemon-owned controls use the raw touch surface, not F-keys.
for key = 13, 24 do
  hl.unbind("F" .. tostring(key))
end
LUA
fi

if [[ ! -d /etc/tiny-dfr || ! -w /etc/tiny-dfr ]]; then
  echo "Preparing /etc/tiny-dfr for live user-level rendering (sudo required)."
  /usr/bin/sudo /usr/bin/install -d -m 0755 -o "$(/usr/bin/id -un)" -g "$(/usr/bin/id -gn)" /etc/tiny-dfr /etc/tiny-dfr/gen
  /usr/bin/sudo /usr/bin/touch /etc/tiny-dfr/config.toml
  /usr/bin/sudo /usr/bin/chown "$(/usr/bin/id -un):$(/usr/bin/id -gn)" /etc/tiny-dfr/config.toml
fi

backlight_rule=/etc/udev/rules.d/99-touchbar-backlight.rules
if [[ ! -e $backlight_rule ]]; then
  echo "Allowing the session to hold the Touch Bar backlight on (sudo required)."
  /usr/bin/sudo /usr/bin/install -m 0644 "$project_dir/integration/99-touchbar-backlight.rules" "$backlight_rule"
  /usr/bin/sudo /usr/bin/udevadm control --reload-rules
  /usr/bin/sudo /usr/bin/chgrp input /sys/class/backlight/appletb_backlight/brightness
  /usr/bin/sudo /usr/bin/chmod g+w /sys/class/backlight/appletb_backlight/brightness
fi

panel_reset=/usr/local/lib/touchbar-panel-reset
if [[ ! -e $panel_reset ]] \
    || ! /usr/bin/cmp -s "$project_dir/integration/touchbar-panel-reset" "$panel_reset"; then
  echo "Installing the post-resume Touch Bar display reset (sudo required)."
  /usr/bin/sudo /usr/bin/install -m 0755 "$project_dir/integration/touchbar-panel-reset" "$panel_reset"
  /usr/bin/sudo /usr/bin/install -m 0644 "$project_dir/integration/touchbar-panel-reset.service" \
    /etc/systemd/system/touchbar-panel-reset.service
  /usr/bin/sudo /usr/bin/systemctl daemon-reload
  /usr/bin/sudo /usr/bin/systemctl enable touchbar-panel-reset.service
fi

/usr/bin/python3 -m py_compile "$user_bin/omarchy-touchbar" "$user_bin/omarchy-chatgpt-dictate" \
  "$user_bin/omarchy-touchbar-settings"
/usr/bin/python3 -c 'import tomllib, pathlib; tomllib.loads(pathlib.Path.home().joinpath(".config/omarchy/touchbar.toml").read_text())'

/usr/bin/systemctl --user stop omarchy-touchbar.service 2>/dev/null || true
# Also reap any daemon launched outside the unit (pre-unit autostart entries).
/usr/bin/pkill -f "$user_bin/omarchy-touchbar daemon" 2>/dev/null || true
/usr/bin/systemctl --user daemon-reload
/usr/bin/systemctl --user enable omarchy-touchbar.service >/dev/null
/usr/bin/systemctl --user restart omarchy-touchbar.service
/usr/bin/sudo /usr/bin/systemctl restart tiny-dfr
/usr/bin/hyprctl reload >/dev/null

echo "Omarchy Touch Bar installed and running."
echo "Run: omarchy-touchbar status"
