#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/GtkSignage.flatpak"

# ALWAYS write config where Flatpak can see it
CONFIG_DIR="$HOME/.var/app/$APP_ID/config/$APP_ID"
CONFIG_FILE="$CONFIG_DIR/config.ini"

echo "GtkSignage setup"
echo "================"
echo

# -----------------------------
# Config setup
# -----------------------------
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

read -rsp "Admin password (will be hashed): " ADMIN_PASS
echo

DATA_DIR=$(prompt "Data directory" "$HOME/.local/share/gtk-signage")
CEC_ENABLE=$(prompt "Enable HDMI-CEC control?" "false")
CEC_START=$(prompt "CEC start time (HH:MM)" "10:00")
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
echo

# -----------------------------
# Flatpak install
# -----------------------------
if flatpak info "$APP_ID" >/dev/null 2>&1; then
  echo "GtkSignage Flatpak already installed."
else
  echo "Installing GtkSignage Flatpak bundle…"

  if [ ! -f "$BUNDLE" ]; then
    echo "ERROR: GtkSignage.flatpak not found."
    echo "Expected at:"
    echo "  $BUNDLE"
    exit 1
  fi

  flatpak install --user --noninteractive "$BUNDLE"
fi

echo
echo "Setup complete."
echo
echo "Run with:"
echo "  flatpak run $APP_ID"
echo