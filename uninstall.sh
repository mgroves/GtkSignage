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
# Optional: disable auto-login (Raspberry Pi OS)
# -----------------------------
echo
read -rp "Disable desktop auto-login (if enabled)? (Y/n): " DISABLE_AUTOLOGIN

if [[ -z "$DISABLE_AUTOLOGIN" || "$DISABLE_AUTOLOGIN" =~ ^[Yy]$ ]]; then
  if grep -qi "raspberry pi" /etc/os-release 2>/dev/null; then
    if [ -f /etc/lightdm/lightdm.conf ]; then
      echo "Disabling auto-login (Raspberry Pi OS)..."
      echo "Administrator password required."

      sudo sed -i \
        -e '/^autologin-user=/d' \
        -e '/^autologin-session=/d' \
        /etc/lightdm/lightdm.conf

      echo "Auto-login disabled."
    else
      echo "No LightDM config found; auto-login was not configured."
    fi
  else
    echo "Auto-login removal is only supported automatically on Raspberry Pi OS."
  fi
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "Uninstall complete."
echo