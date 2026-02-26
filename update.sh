#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/GtkSignage.flatpak"

# MUST match install.sh exactly
CONFIG_DIR="$HOME/.var/app/$APP_ID/config/$APP_ID"
CONFIG_FILE="$CONFIG_DIR/config.ini"
BACKUP_FILE="$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"

echo "GtkSignage update"
echo "================="
echo

# -----------------------------
# Verify config exists
# -----------------------------
if [ ! -f "$CONFIG_FILE" ]; then
  echo "No config file found."
  echo
  echo "Expected at:"
  echo "  $CONFIG_FILE"
  echo
  echo "Run install.sh first."
  exit 1
fi

# -----------------------------
# Config safety
# -----------------------------
echo "Backing up config:"
echo "  $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

ensure_key() {
  local section="$1"
  local key="$2"
  local value="$3"

  if ! grep -q "^\[$section\]" "$CONFIG_FILE"; then
    echo >> "$CONFIG_FILE"
    echo "[$section]" >> "$CONFIG_FILE"
  fi

  if ! awk "/^\[$section\]/,/^\[/{print}" "$CONFIG_FILE" | grep -q "^$key\s*="; then
    sed -i "/^\[$section\]/a$key = $value" "$CONFIG_FILE"
    echo "  added [$section].$key"
  fi
}

warn_deprecated() {
  local section="$1"
  local key="$2"

  if awk "/^\[$section\]/,/^\[/{print}" "$CONFIG_FILE" | grep -q "^$key\s*="; then
    echo "  WARNING: [$section].$key is deprecated (safe to remove)"
  fi
}

echo "Applying config migrations (if any)…"

echo
echo "No config migrations are required for this version."
echo

# ---------------------------------------------------------------------------
# EXAMPLE (FAKE): introduce a completely fictional setting
#
# PURPOSE:
# Demonstrates how to add a NEW config key during an update in a safe,
# idempotent way, without overwriting an existing user value.
#
# SCENARIO (NOT REAL):
# App v9.9 introduces user shoe size tracking.
#
# BEHAVIOR:
# - If [fun].shoe_size already exists, do nothing.
# - If it does NOT exist, add it with a reasonable default.
# - Existing configs remain valid and unchanged.
#
# WHEN TO USE ensure_key():
# - A new setting is required or expected by the app
# - A safe default value exists
# - You want updates to be repeatable and non-destructive
#
# NOTE:
# This is intentionally silly so no one mistakes it for a real setting.
#
# ensure_key fun shoe_size 11
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# EXAMPLE (FAKE): deprecated spelling variant
#
# PURPOSE:
# Demonstrates how to WARN about an old or discouraged config key
# without deleting it or changing behavior.
#
# SCENARIO (NOT REAL):
# Older versions accepted both US and UK spelling variants:
#
#   [fun].shoe_color   (preferred, US spelling)
#   [fun].shoe_colour  (legacy, UK spelling)
#
# CHANGE:
# App v9.9 standardizes on the US spelling:
#
#   [fun].shoe_color
#
# BEHAVIOR:
# - The legacy key still works for backward compatibility
# - No automatic removal is performed
# - A warning is printed during update to encourage cleanup
#
# WHEN TO USE warn_deprecated():
# - A setting is still supported but discouraged
# - You want visibility without breaking configs
# - Automatic deletion would be risky or surprising
#
# NOTE:
# This warning is informational only and does not modify config files.
#
# warn_deprecated fun shoe_colour
# ---------------------------------------------------------------------------

###############################################################################

# -----------------------------
# Flatpak update from bundle
# -----------------------------
echo
read -rp "Update GtkSignage Flatpak from local bundle? [y/N]: " update_fp

if [[ "$update_fp" =~ ^[Yy]$ ]]; then
  if ! command -v flatpak >/dev/null 2>&1; then
    echo "Flatpak not installed; skipping app update."
  elif [ ! -f "$BUNDLE" ]; then
    echo "ERROR: GtkSignage.flatpak not found."
    echo
    echo "Expected at:"
    echo "  $BUNDLE"
    echo
    echo "Download the new bundle from:"
    echo "  https://github.com/mgroves/GtkSignage/releases"
    exit 1
  else
    echo "Reinstalling GtkSignage from bundle…"
    flatpak install --user --noninteractive --reinstall "$BUNDLE"
  fi
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "Update complete."
echo
echo "If anything goes wrong, restore config with:"
echo "  cp $BACKUP_FILE $CONFIG_FILE"
echo