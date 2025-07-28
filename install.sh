#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
SERVICE_NAME="gtk-signage"
VENV_DIR="$INSTALL_DIR/venv"

echo "Installing GtkSignage..."

# Ensure dependencies
sudo apt update
sudo apt install -y \
  git python3 python3-pip python3-venv openssl \
  python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
  xserver-xorg xinit openbox lightdm raspberrypi-ui-mods


# Clone the repo
if [ ! -d "$INSTALL_DIR" ]; then
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
fi

# Always ensure ownership, even if clone was skipped
# Determine the invoking user even when run via sudo or subshell
if [ -n "$SUDO_UID" ]; then
  INSTALL_OWNER=$(getent passwd "$SUDO_UID" | cut -d: -f1)
else
  INSTALL_OWNER=$(whoami)
fi

sudo chown -R "$INSTALL_OWNER:$INSTALL_OWNER" "$INSTALL_DIR"

cd "$INSTALL_DIR"

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv --system-site-packages
source "$VENV_DIR/bin/activate"

# Install Python packages inside venv
echo "Installing Python packages..."
pip install --no-cache-dir -r requirements.txt

# Prompt for admin credentials
read -p "Enter admin username: " ADMIN_USERNAME
read -p "Enter admin password: " ADMIN_PASSWORD

# Hash the password using Werkzeug's generate_password_hash
HASHED_PASSWORD=$("$VENV_DIR/bin/python" -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$ADMIN_PASSWORD'))")

# Prompt for Flask host/port and SSL
read -p "Enter Flask host [0.0.0.0]: " FLASK_HOST
FLASK_HOST=${FLASK_HOST:-0.0.0.0}

read -p "Enter Flask port [6969]: " FLASK_PORT
FLASK_PORT=${FLASK_PORT:-6969}

read -p "Enable HTTPS (requires cert.pem and key.pem)? [y/N]: " USE_SSL
USE_SSL=$(echo "$USE_SSL" | tr '[:upper:]' '[:lower:]')
USE_SSL=${USE_SSL:-n}
USE_SSL_VALUE="false"

# Prompt for cache settings
read -p "Enter cache directory [cache]: " CACHE_DIR
CACHE_DIR=${CACHE_DIR:-cache}

read -p "Enter cache expiry time in hours [48]: " CACHE_EXPIRY_HOURS
CACHE_EXPIRY_HOURS=${CACHE_EXPIRY_HOURS:-48}

if [[ "$USE_SSL" == "y" || "$USE_SSL" == "yes" ]]; then
  USE_SSL_VALUE="true"

  echo "Generating self-signed SSL certificate..."
  openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
    -keyout key.pem -out cert.pem -days 365 \
    -subj "/CN=localhost"

  echo "Self-signed certificate created at:"
  echo "  $INSTALL_DIR/cert.pem"
  echo "  $INSTALL_DIR/key.pem"
fi

# Generate a random Flask secret key
FLASK_SECRET=$(openssl rand -hex 32)

# Write .env file
echo "Creating .env file..."
cat <<EOF | sudo tee .env > /dev/null
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$HASHED_PASSWORD
FLASK_SECRET_KEY=$FLASK_SECRET
FLASK_HOST=$FLASK_HOST
FLASK_PORT=$FLASK_PORT
USE_SSL=$USE_SSL_VALUE
CACHE_DIR=$CACHE_DIR
CACHE_EXPIRY_HOURS=$CACHE_EXPIRY_HOURS
EOF

# Create systemd service
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Setting up systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GTK Signage App
After=graphical.target
Requires=graphical.target

[Service]
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=$INSTALL_OWNER
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$INSTALL_OWNER/.Xauthority

[Install]
WantedBy=default.target
EOF


# Enable and start the service
echo "Enabling and starting the signage service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# Set journald log size limit
echo "Configuring systemd journal log size limit..."
sudo sed -i '/^#*SystemMaxUse=/d;/^#*SystemKeepFree=/d;/^#*SystemMaxFileSize=/d;/^#*SystemMaxFiles=/d' /etc/systemd/journald.conf
sudo tee -a /etc/systemd/journald.conf > /dev/null <<EOF
SystemMaxUse=100M
SystemKeepFree=50M
SystemMaxFileSize=10M
SystemMaxFiles=10
EOF
sudo systemctl restart systemd-journald

echo "✅ Log output is handled by systemd-journald."
echo "  To view logs:"
echo "    sudo journalctl -u $SERVICE_NAME.service"
echo "    sudo journalctl -u $SERVICE_NAME.service -f  # (live view)"
echo "  Logs are stored in: /var/log/journal (persistent) or /run/log/journal (volatile)"

echo "Installation complete. Signage service is running."
if [[ "$USE_SSL_VALUE" == "true" ]]; then
  echo "🔒 HTTPS is enabled using self-signed certificates."
fi

echo "💡 Tip: Make sure your Pi is set to boot to Desktop (GUI with autologin)."
echo "Run 'sudo raspi-config' → System Options → Boot / Auto Login → Desktop Autologin."
