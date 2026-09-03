#!/usr/bin/env bash
# Remove the Omarchy Touch Bar daemon and leave tiny-dfr with a plain F-row.
set -euo pipefail

user_bin="${HOME}/.local/bin"
omarchy_config="${HOME}/.config/omarchy"
hypr_config="${HOME}/.config/hypr"
user_systemd="${HOME}/.config/systemd/user"

systemctl --user disable --now omarchy-touchbar.service 2>/dev/null || true
rm -f "$user_systemd/omarchy-touchbar.service"
systemctl --user daemon-reload

rm -f "$user_bin/omarchy-touchbar" "$user_bin/omarchy-chatgpt-dictate" \
  "$user_bin/omarchy-touchbar-settings" \
  "${HOME}/.local/share/applications/omarchy-touchbar-settings.desktop" \
  "$omarchy_config/hooks/theme-set.d/touchbar" \
  "$omarchy_config/touchbar.toml.dist"

autostart="$hypr_config/autostart.lua"
if [[ -f $autostart ]]; then
  sed -i '/Context-aware T2 MacBook Touch Bar/d;/omarchy-touchbar/d' "$autostart"
fi

echo "Touch Bar daemon removed. Kept: ~/.config/omarchy/touchbar.toml and the"
echo "sudo-installed pieces (/etc/tiny-dfr, udev rule, touchbar-panel-reset)."
echo "Remove those with:"
echo "  sudo systemctl disable --now touchbar-panel-reset.service"
echo "  sudo rm -f /etc/systemd/system/touchbar-panel-reset.service /usr/local/lib/touchbar-panel-reset /etc/udev/rules.d/99-touchbar-backlight.rules"
