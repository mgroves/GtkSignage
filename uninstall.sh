#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"

CONFIG_DIR="$HOME/.var/app/$APP_ID"
AUTOSTART_FILE="$HOME/.config/autostart/gtk-signage.desktop"

echo "GtkSignage uninstall"
echo "===================="
echo

# -----------------------------
# Remove autostart
# -----------------------------
if [ -f "$AUTOSTART_FILE" ]; then
  echo "Removing autostart entry..."
  rm -f "$AUTOSTART_FILE"
  echo "Autostart removed."
else
  echo "No autostart entry found."
fi

# -----------------------------
# Uninstall Flatpak
# -----------------------------
if flatpak info "$APP_ID" >/dev/null 2>&1; then
  echo
  echo "Uninstalling GtkSignage Flatpak..."
  flatpak uninstall --user -y "$APP_ID"
else
  echo
  echo "GtkSignage Flatpak is not installed."
fi

# -----------------------------
# Optional: remove config + data
# -----------------------------
echo
read -rp "Remove GtkSignage configuration and data? (y/N): " REMOVE_DATA

if [[ "$REMOVE_DATA" =~ ^[Yy]$ ]]; then
  if [ -d "$CONFIG_DIR" ]; then
    echo "Removing config and data at:"
    echo "  $CONFIG_DIR"
    rm -rf "$CONFIG_DIR"
    echo "Config and data removed."
  else
    echo "No config/data directory found."
  fi
else
  echo "Keeping configuration and data."
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "Uninstall complete."
echo