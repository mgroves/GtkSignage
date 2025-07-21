#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
SERVICE_NAME="gtk-signage"

echo "Updating signage software from GitHub..."

# Ensure git is installed
sudo apt update
sudo apt install -y git

if [ ! -d "$INSTALL_DIR" ]; then
  echo "Install directory not found: $INSTALL_DIR"
  echo "Run install.sh first."
  exit 1
fi

cd "$INSTALL_DIR"

echo "Fetching latest changes..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "Restarting signage service..."
sudo systemctl restart "$SERVICE_NAME"

echo "Update complete."
