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
sudo apt install -y git python3 python3-pip python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0

# Clone the repo
if [ ! -d "$INSTALL_DIR" ]; then
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
else
  echo "$INSTALL_DIR already exists, skipping clone."
fi

cd "$INSTALL_DIR"

# Prompt for admin credentials
read -p "Enter admin username: " ADMIN_USERNAME
read -p "Enter admin password: " ADMIN_PASSWORD

# Generate a random Flask secret key
FLASK_SECRET=$(openssl rand -hex 32)

# Write .env file
echo "Creating .env file..."
cat <<EOF | sudo tee .env > /dev/null
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
FLASK_SECRET_KEY=$FLASK_SECRET
EOF

# Install required Python packages
echo "Installing Python packages..."
pip3 install --no-cache-dir -r requirements.txt

# Create systemd service
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Setting up systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GTK Signage App
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

# Enable and start the service
echo "Enabling and starting the signage service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "Installation complete. Signage service is running."
