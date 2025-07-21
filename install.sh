#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
SERVICE_NAME="gtk-signage"

echo "Installing signage software..."

# Install required system packages
sudo apt update
sudo apt install -y git python3 python3-pip python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0

# Clone or update repo
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Cloning repo into $INSTALL_DIR..."
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
else
  echo "$INSTALL_DIR already exists, skipping clone."
fi

# Install Python dependencies
echo "Installing Python packages..."
sudo pip3 install --no-cache-dir -r "$INSTALL_DIR/requirements.txt"

# Create systemd service
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
echo "Creating systemd service at $SERVICE_FILE"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GTK Signage App
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=5
User=pi
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# Create self-signed certs if not present
CERT="$INSTALL_DIR/cert.pem"
KEY="$INSTALL_DIR/key.pem"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
  echo "Generating self-signed SSL certificate..."
  sudo openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$KEY" \
    -out "$CERT" \
    -subj "/CN=localhost"
fi

echo "✅ Installation complete. Signage will start on boot and after power loss."
