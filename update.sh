#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
VENV_DIR="$INSTALL_DIR/venv"

echo "Updating GtkSignage..."

# Ensure required tools are available
sudo apt update
sudo apt install -y \
  git python3 python3-pip python3-venv openssl \
  python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
  xserver-xorg xinit matchbox-window-manager x11-xserver-utils \
  unclutter \
  cmake libcec-dev cec-utils libudev-dev libxrandr-dev

# Check for install dir
if [ ! -d "$INSTALL_DIR" ]; then
  echo "❌ Install directory not found: $INSTALL_DIR"
  echo "Run install.sh first."
  exit 1
fi

cd "$INSTALL_DIR"

echo "Fetching latest code from $BRANCH branch..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

# Check and activate venv
if [ -d "$VENV_DIR" ]; then
  echo "Activating virtual environment and installing updated dependencies..."
  source "$VENV_DIR/bin/activate"
  pip install --no-cache-dir -r requirements.txt
else
  echo "❌ Virtual environment not found: $VENV_DIR"
  echo "Run install.sh again to set it up."
  exit 1
fi

# Optional reboot confirmation
echo
read -p "✅ Update complete. Reboot now to apply changes? [y/N]: " REBOOT_ANSWER
REBOOT_ANSWER=$(echo "$REBOOT_ANSWER" | tr '[:upper:]' '[:lower:]')

if [[ "$REBOOT_ANSWER" == "y" || "$REBOOT_ANSWER" == "yes" ]]; then
  echo "Rebooting..."
  sudo reboot
else
  echo "Reboot skipped. You can reboot manually with 'sudo reboot' later."
fi
