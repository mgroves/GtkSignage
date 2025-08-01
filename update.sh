#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
VENV_DIR="$INSTALL_DIR/venv"

echo "Updating GtkSignage..."

# Ensure git is available
sudo apt update
sudo apt install -y git

if [ ! -d "$INSTALL_DIR" ]; then
  echo "❌ Install directory not found: $INSTALL_DIR"
  echo "Run install.sh first."
  exit 1
fi

cd "$INSTALL_DIR"

echo "Fetching latest code from $BRANCH branch..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

if [ -d "$VENV_DIR" ]; then
  echo "Activating virtual environment and installing updated dependencies..."
  source "$VENV_DIR/bin/activate"
  pip install --no-cache-dir -r requirements.txt
else
  echo "❌ Virtual environment not found: $VENV_DIR"
  echo "Run install.sh again to set it up."
  exit 1
fi

echo
read -n 1 -s -r -p "✅ Update complete. Press any key to reboot and apply changes..."
echo
sudo reboot
