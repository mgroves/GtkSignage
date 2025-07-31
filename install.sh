#!/bin/bash

set -e

REPO_USER="mgroves"
REPO_NAME="GtkSignage"
BRANCH="prod"
INSTALL_DIR="/opt/gtk-signage"
VENV_DIR="$INSTALL_DIR/venv"

echo "Installing GtkSignage..."

# Ensure dependencies
sudo apt update
sudo apt install -y \
  git python3 python3-pip python3-venv openssl \
  python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
  xserver-xorg xinit matchbox-window-manager x11-xserver-utils \
  unclutter

# Determine invoking user for autologin + config
if [ -n "$SUDO_UID" ]; then
  INSTALL_OWNER="$(getent passwd "$SUDO_UID" | cut -d: -f1)"
else
  INSTALL_OWNER="$(whoami)"
fi

echo "Using install user: $INSTALL_OWNER"

# Clone the repo
if [ ! -d "$INSTALL_DIR" ]; then
  sudo git clone --branch "$BRANCH" "https://github.com/$REPO_USER/$REPO_NAME.git" "$INSTALL_DIR"
fi

# Ensure user owns it
sudo chown -R "$INSTALL_OWNER:$INSTALL_OWNER" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR" --system-site-packages
source "$VENV_DIR/bin/activate"

# Install Python packages inside venv
echo "Installing Python packages..."
pip install --no-cache-dir -r requirements.txt

# Prompt for admin credentials
read -p "Enter GtkSignage username: " ADMIN_USERNAME
read -s -p "Enter GtkSignage password: " ADMIN_PASSWORD
echo

# Hash the password using Werkzeug
HASHED_PASSWORD=$("$VENV_DIR/bin/python" -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$ADMIN_PASSWORD'))")

# Prompt for Flask config
read -p "Enter GtkSignage host [0.0.0.0]: " FLASK_HOST
FLASK_HOST=${FLASK_HOST:-0.0.0.0}

read -p "Enter GtkSignage port [80]: " FLASK_PORT
FLASK_PORT=${FLASK_PORT:-80}

read -p "Enable HTTPS (requires cert.pem and key.pem)? [y/N]: " USE_SSL
USE_SSL=$(echo "$USE_SSL" | tr '[:upper:]' '[:lower:]')
USE_SSL=${USE_SSL:-n}
USE_SSL_VALUE="false"

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
  echo "Created cert.pem and key.pem"
fi

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

# Set up .xinitrc to launch the app via X
echo "Configuring .xinitrc startup..."
cat <<'EOF' | sudo tee "/home/$INSTALL_OWNER/.xinitrc" > /dev/null
#!/bin/bash
matchbox-window-manager -use_titlebar no &
unclutter -idle 0 &
/opt/gtk-signage/venv/bin/python /opt/gtk-signage/main.py
EOF
sudo chmod +x "/home/$INSTALL_OWNER/.xinitrc"
sudo chown "$INSTALL_OWNER:$INSTALL_OWNER" "/home/$INSTALL_OWNER/.xinitrc"

# Set up autostarting X via .bash_profile
echo "Ensuring X autostarts on login..."
PROFILE_SCRIPT="/home/$INSTALL_OWNER/.bash_profile"

# Create if missing
if [ ! -f "$PROFILE_SCRIPT" ]; then
  sudo touch "$PROFILE_SCRIPT"
  sudo chown "$INSTALL_OWNER:$INSTALL_OWNER" "$PROFILE_SCRIPT"
fi

# Append exec startx if not present
if ! grep -q "exec startx" "$PROFILE_SCRIPT"; then
  echo "exec startx" | sudo tee -a "$PROFILE_SCRIPT" > /dev/null
  sudo chown "$INSTALL_OWNER:$INSTALL_OWNER" "$PROFILE_SCRIPT"
fi

# Set journald log size limit
echo "Configuring systemd journal size limits..."
sudo sed -i '/^#*SystemMaxUse=/d;/^#*SystemKeepFree=/d;/^#*SystemMaxFileSize=/d;/^#*SystemMaxFiles=/d' /etc/systemd/journald.conf
sudo tee -a /etc/systemd/journald.conf > /dev/null <<EOF
SystemMaxUse=100M
SystemKeepFree=50M
SystemMaxFileSize=10M
SystemMaxFiles=10
EOF
sudo systemctl restart systemd-journald

# Force Raspberry Pi to boot to console with autologin
echo "Forcing boot to console with autologin..."
sudo raspi-config nonint do_boot_behaviour B2
echo "Boot to console with autologin enabled."

echo
read -n 1 -s -r -p "✅ GtkSignage installed. Press any key to reboot and start the signage system..."
echo
sudo reboot
