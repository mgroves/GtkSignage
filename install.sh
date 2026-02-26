#!/bin/bash
set -euo pipefail

# -----------------------------
# Configuration
# -----------------------------
REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
VENV_DIR="$INSTALL_DIR/venv"

echo "▶ Installing GtkSignage"

# -----------------------------
# Ensure running on Linux
# -----------------------------
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "❌ This installer must be run on Linux."
  exit 1
fi

# -----------------------------
# Determine invoking user
# -----------------------------
if [[ -n "${SUDO_UID:-}" ]]; then
  INSTALL_OWNER="$(getent passwd "$SUDO_UID" | cut -d: -f1)"
else
  INSTALL_OWNER="$(whoami)"
fi

INSTALL_HOME="/home/$INSTALL_OWNER"
echo "▶ Install user: $INSTALL_OWNER"

# -----------------------------
# System dependencies
# -----------------------------
echo "▶ Installing system dependencies"

BASE_PACKAGES=(
  git python3 python3-pip python3-venv openssl
  python3-gi python3-gi-cairo gir1.2-gtk-3.0
  xserver-xorg xinit matchbox-window-manager x11-xserver-utils
  unclutter
  libcec-dev cec-utils libudev-dev libxrandr-dev
)

WEBKIT_PACKAGES=()

if apt-cache show gir1.2-webkit2gtk-4.1 >/dev/null 2>&1; then
  WEBKIT_PACKAGES+=(gir1.2-webkit2gtk-4.1 libwebkit2gtk-4.1-0)
elif apt-cache show gir1.2-webkit2-4.0 >/dev/null 2>&1; then
  WEBKIT_PACKAGES+=(gir1.2-webkit2-4.0 libwebkit2gtk-4.0-37)
else
  echo "❌ No compatible WebKitGTK GIR package found"
  exit 1
fi

sudo apt update
sudo apt install -y "${BASE_PACKAGES[@]}" "${WEBKIT_PACKAGES[@]}"

# -----------------------------
# Clone or update repo
# -----------------------------
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  echo "▶ Cloning repository"
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
else
  echo "▶ Updating existing repository"
  sudo git -C "$INSTALL_DIR" fetch origin
  sudo git -C "$INSTALL_DIR" checkout "$BRANCH"
  sudo git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
fi

sudo chown -R "$INSTALL_OWNER:$INSTALL_OWNER" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# -----------------------------
# Virtual environment
# -----------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  echo "▶ Creating virtual environment"
  python3 -m venv "$VENV_DIR" --system-site-packages
fi

source "$VENV_DIR/bin/activate"

echo "▶ Installing Python dependencies"
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Admin credentials
# -----------------------------
read -rp "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"

read -rsp "Admin password: " ADMIN_PASSWORD
echo
read -rsp "Confirm password: " CONFIRM_PASSWORD
echo

if [[ "$ADMIN_PASSWORD" != "$CONFIRM_PASSWORD" ]]; then
  echo "❌ Passwords do not match."
  exit 1
fi

HASHED_PASSWORD="$("$VENV_DIR/bin/python" <<EOF
from werkzeug.security import generate_password_hash
import sys
print(generate_password_hash(sys.stdin.read().rstrip()))
EOF
<<<"$ADMIN_PASSWORD"
)"

# -----------------------------
# Flask config
# -----------------------------
read -rp "Flask host [0.0.0.0]: " FLASK_HOST
FLASK_HOST="${FLASK_HOST:-0.0.0.0}"

read -rp "Flask port [6969]: " FLASK_PORT
FLASK_PORT="${FLASK_PORT:-6969}"

USE_SSL="false"

# -----------------------------
# CEC config
# -----------------------------
read -rp "Enable HDMI-CEC display control? [y/N]: " CEC_ENABLE_INPUT
CEC_ENABLE_INPUT="${CEC_ENABLE_INPUT,,}"

CEC_ENABLE="false"
CEC_START=""
CEC_END=""

if [[ "$CEC_ENABLE_INPUT" == "y" || "$CEC_ENABLE_INPUT" == "yes" ]]; then
  CEC_ENABLE="true"

  validate_time() {
    [[ "$1" =~ ^([01]?[0-9]|2[0-3]):[0-5][0-9]$ ]]
  }

  while true; do
    read -rp "CEC start time [08:00]: " CEC_START
    CEC_START="${CEC_START:-08:00}"
    validate_time "$CEC_START" && break
    echo "❌ Invalid time format"
  done

  while true; do
    read -rp "CEC end time [22:00]: " CEC_END
    CEC_END="${CEC_END:-22:00}"
    validate_time "$CEC_END" && break
    echo "❌ Invalid time format"
  done
fi

FLASK_SECRET="$(openssl rand -hex 32)"

# -----------------------------
# Write .env
# -----------------------------
echo "▶ Writing .env"
cat > "$INSTALL_DIR/.env" <<EOF
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD_HASH=$HASHED_PASSWORD

FLASK_SECRET_KEY=$FLASK_SECRET
FLASK_HOST=$FLASK_HOST
FLASK_PORT=$FLASK_PORT
USE_SSL=false

CEC_ENABLE=$CEC_ENABLE
CEC_START=$CEC_START
CEC_END=$CEC_END
EOF

chmod 600 "$INSTALL_DIR/.env"
chown "$INSTALL_OWNER:$INSTALL_OWNER" "$INSTALL_DIR/.env"

# -----------------------------
# X autostart
# -----------------------------
XINITRC="$INSTALL_HOME/.xinitrc"

cat > "$XINITRC" <<EOF
#!/bin/bash
matchbox-window-manager -use_titlebar no &
unclutter -idle 0 &
xset s off
xset -dpms
xset s noblank
exec $VENV_DIR/bin/python $INSTALL_DIR/main.py
EOF

chmod +x "$XINITRC"
chown "$INSTALL_OWNER:$INSTALL_OWNER" "$XINITRC"

# -----------------------------
# Start X on console login
# -----------------------------
PROFILE="$INSTALL_HOME/.bash_profile"

touch "$PROFILE"
chown "$INSTALL_OWNER:$INSTALL_OWNER" "$PROFILE"

if ! grep -q "startx" "$PROFILE"; then
  cat >> "$PROFILE" <<'EOF'

if [[ -z "$DISPLAY" && "$(tty)" == "/dev/tty1" ]]; then
  exec startx
fi
EOF
fi

# -----------------------------
# Pi boot mode
# -----------------------------
if command -v raspi-config >/dev/null; then
  echo "▶ Enabling console autologin"
  sudo raspi-config nonint do_boot_behaviour B2
fi

# -----------------------------
# Sanity check
# -----------------------------
echo "▶ Verifying installation"
"$VENV_DIR/bin/python" -c "import gi; from gi.repository import Gtk; print('GTK OK')"

# -----------------------------
# Finish
# -----------------------------
read -rp "✅ Installation complete. Reboot now? [y/N]: " REBOOT
REBOOT="${REBOOT,,}"

if [[ "$REBOOT" == "y" || "$REBOOT" == "yes" ]]; then
  sudo reboot
else
  echo "ℹ Reboot later with: sudo reboot"
fi