#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
SERVICE_NAME="gtk-signage"

echo "Installing signage software..."

# Ensure dependencies
sudo apt update
sudo apt install -y git python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0

# Clone the repo
if [ ! -d "$INSTALL_DIR" ]; then
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
else
  echo "$INSTALL_DIR already exists, skipping clone."
fi

# Create systemd service
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GTK Signage App
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

# Enable and start service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "Installation complete. Service is running."
