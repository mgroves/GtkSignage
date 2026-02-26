#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/GtkSignage.flatpak"

CONFIG_DIR="$HOME/.config/$APP_ID"
CONFIG_FILE="$CONFIG_DIR/config.ini"
BACKUP_FILE="$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"

echo "GtkSignage update"
echo "================="
echo

if [ ! -f "$CONFIG_FILE" ]; then
  echo "No config file found."
  echo "Run install.sh first."
  exit 1
fi

# -----------------------------
# Config safety
# -----------------------------
echo "Backing up config:"
echo "  $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

echo
echo "No config migrations are required for this version."
echo

###############################################################################
# FUTURE MIGRATIONS GO BELOW
#
# These helpers are EXAMPLES ONLY.
# They are intentionally silly to avoid confusion with real settings.
###############################################################################

# ensure_key() {
#   local section="$1"
#   local key="$2"
#   local value="$3"
#
#   if ! grep -q "^\[$section\]" "$CONFIG_FILE"; then
#     echo >> "$CONFIG_FILE"
#     echo "[$section]" >> "$CONFIG_FILE"
#   fi
#
#   if ! awk "/^\[$section\]/,/^\[/{print}" "$CONFIG_FILE" | grep -q "^$key\s*="; then
#     sed -i "/^\[$section\]/a$key = $value" "$CONFIG_FILE"
#     echo "  added [$section].$key"
#   fi
# }

# warn_deprecated() {
#   local section="$1"
#   local key="$2"
#
#   if awk "/^\[$section\]/,/^\[/{print}" "$CONFIG_FILE" | grep -q "^$key\s*="; then
#     echo "  WARNING: [$section].$key is deprecated (safe to remove)"
#   fi
# }

# ---------------------------------------------------------------------------
# EXAMPLE (FAKE): introduce a completely fictional setting
#
# App v9.9 introduces user shoe size tracking (this is NOT REAL)
#
# ensure_key fun shoe_size 11
# ---------------------------------------------------------------------------

###############################################################################

# -----------------------------
# Flatpak update from bundle
# -----------------------------
echo
read -rp "Update GtkSignage Flatpak from local bundle? [y/N]: " update_fp

if [[ "$update_fp" =~ ^[Yy]$ ]]; then
  if ! command -v flatpak >/dev/null; then
    echo "Flatpak not installed; skipping app update."
  elif [ ! -f "$BUNDLE" ]; then
    echo "ERROR: GtkSignage.flatpak not found."
    echo "Expected at:"
    echo "  $BUNDLE"
    exit 1
  else
    echo "Reinstalling GtkSignage from bundle…"
    flatpak install --user --noninteractive --reinstall "$BUNDLE"
  fi
fi

echo
echo "Update complete."
echo
echo "If anything goes wrong, restore config with:"
echo "  cp $BACKUP_FILE $CONFIG_FILE"
echo