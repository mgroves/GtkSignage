#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/GtkSignage.flatpak"

# ALWAYS write config where Flatpak can see it
CONFIG_DIR="$HOME/.var/app/$APP_ID/config/$APP_ID"
CONFIG_FILE="$CONFIG_DIR/config.ini"

AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/gtk-signage.desktop"

echo "GtkSignage setup"
echo "================"
echo

# -----------------------------
# Verify Flatpak bundle exists
# -----------------------------
if [ ! -f "$BUNDLE" ]; then
  echo
  echo "ERROR: GtkSignage.flatpak not found."
  echo
  echo "Expected file:"
  echo "  $BUNDLE"
  echo
  echo "Download the Flatpak bundle from:"
  echo "  https://github.com/mgroves/GtkSignage/releases"
  echo
  echo "Then place GtkSignage.flatpak in the same directory as install.sh"
  echo "and re-run this script."
  echo
  exit 1
fi

# -----------------------------
# Ensure Flatpak exists
# -----------------------------
if ! command -v flatpak >/dev/null 2>&1; then
  echo "Flatpak not found."
  echo "Administrator password required to install it."
  sudo apt update
  sudo apt install -y flatpak
fi

# -----------------------------
# Config setup
# -----------------------------
echo
echo "Configuring GtkSignage…"
echo

mkdir -p "$CONFIG_DIR"

prompt() {
  local label="$1"
  local default="$2"
  local var
  read -rp "$label [$default]: " var
  echo "${var:-$default}"
}

FLASK_HOST=$(prompt "Flask bind host" "0.0.0.0")
FLASK_PORT=$(prompt "Flask port" "6969")
USE_SSL=$(prompt "Enable SSL?" "false")
ADMIN_USER=$(prompt "Admin username" "admin")

# -----------------------------
# Password prompt + confirmation
# -----------------------------
while true; do
  read -rsp "Admin password (min 8 chars): " ADMIN_PASS
  echo
  read -rsp "Confirm admin password: " ADMIN_PASS_CONFIRM
  echo

  if [[ -z "$ADMIN_PASS" ]]; then
    echo "Password cannot be empty. Please try again."
  elif [[ ${#ADMIN_PASS} -lt 8 ]]; then
    echo "Password must be at least 8 characters."
  elif [[ "$ADMIN_PASS" != "$ADMIN_PASS_CONFIRM" ]]; then
    echo "Passwords do not match. Please try again."
  else
    break
  fi
done

DATA_DIR=$(prompt "Data directory" "$HOME/.local/share/gtk-signage")
CEC_ENABLE=$(prompt "Enable HDMI-CEC control?" "true")
CEC_START=$(prompt "CEC start time (HH:MM)" "10:30")
CEC_END=$(prompt "CEC end time (HH:MM)" "22:00")

SECRET_KEY=$(python3 - <<EOF
import secrets
print(secrets.token_hex(32))
EOF
)

PASS_HASH=$(python3 - <<EOF
from werkzeug.security import generate_password_hash
print(generate_password_hash("$ADMIN_PASS"))
EOF
)

echo
echo "Writing config…"
echo

cat >"$CONFIG_FILE" <<EOF
[auth]
admin_username = $ADMIN_USER
admin_password_hash = $PASS_HASH

[flask]
host = $FLASK_HOST
port = $FLASK_PORT
use_ssl = $USE_SSL
secret_key = $SECRET_KEY

[paths]
data_dir = $DATA_DIR

[slides]
file = slides.json

[storage]
uploads_dir = uploads

[cec]
enable = $CEC_ENABLE
start = $CEC_START
end = $CEC_END
poll_seconds = 300
EOF

echo "Config written to:"
echo "  $CONFIG_FILE"

# -----------------------------
# Flatpak install (local bundle only)
# -----------------------------
echo
if flatpak info "$APP_ID" >/dev/null 2>&1; then
  echo "GtkSignage Flatpak already installed."
else
  echo "Installing GtkSignage Flatpak bundle…"
  flatpak install --user --noninteractive "$BUNDLE"
fi

# -----------------------------
# Autostart on login
# -----------------------------
echo
echo "Enabling autostart on login…"

mkdir -p "$AUTOSTART_DIR"

cat >"$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=GtkSignage
Exec=flatpak run $APP_ID
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "Autostart configured:"
echo "  $AUTOSTART_FILE"

# -----------------------------
# Optional: enable auto-login (Raspberry Pi OS)
# -----------------------------
echo
read -rp "Enable desktop auto-login for kiosk use? (Y/n): " ENABLE_AUTOLOGIN

if [[ -z "$ENABLE_AUTOLOGIN" || "$ENABLE_AUTOLOGIN" =~ ^[Yy]$ ]]; then
  if grep -qi "raspberry pi" /etc/os-release 2>/dev/null; then
    echo "Configuring auto-login (Raspberry Pi OS)..."
    echo "Administrator password required."

    sudo bash -c "
      mkdir -p /etc/lightdm
      if [ ! -f /etc/lightdm/lightdm.conf ]; then
        echo '[Seat:*]' > /etc/lightdm/lightdm.conf
      fi

      sed -i '/^autologin-user=/d' /etc/lightdm/lightdm.conf
      sed -i '/^autologin-session=/d' /etc/lightdm/lightdm.conf

      sed -i '/^\[Seat:\*\]/a autologin-user=$USER' /etc/lightdm/lightdm.conf
      sed -i '/^\[Seat:\*\]/a autologin-session=lightdm-autologin' /etc/lightdm/lightdm.conf
    "

    echo "Auto-login enabled for user: $USER"
    echo "The system will log in automatically on boot."
  else
    echo "Auto-login setup is only supported automatically on Raspberry Pi OS."
    echo "Please configure auto-login manually for your distribution."
  fi
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "Setup complete."
echo
echo "GtkSignage will start automatically on login."
echo "Manual start:"
echo "  flatpak run $APP_ID"
echo