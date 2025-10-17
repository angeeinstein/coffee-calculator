#!/bin/bash

# Coffee Calculator Installation Script
# This script will install and configure the Coffee Cost Calculator as a systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="coffee-calculator"
SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_GROUP="${SERVICE_USER}"
INSTALL_DIR="${SCRIPT_DIR}"
VENV_DIR="${INSTALL_DIR}/venv"
DATA_DIR="${INSTALL_DIR}/data"

print_info "Starting Coffee Calculator installation..."
print_info "Installation directory: ${INSTALL_DIR}"
print_info "Service user: ${SERVICE_USER}"

# Check if running with sudo (except for user checks)
if [ "$EUID" -ne 0 ] && [ "$(id -u)" -ne 0 ]; then 
    print_warning "This script requires sudo privileges for system configuration."
    print_info "Attempting to re-run with sudo..."
    exec sudo bash "$0" "$@"
    exit $?
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update package list
print_info "Updating package list..."
apt-get update -qq

# Install Python 3 and pip if not present
if ! command_exists python3; then
    print_info "Installing Python 3..."
    apt-get install -y python3
else
    print_success "Python 3 is already installed ($(python3 --version))"
fi

if ! command_exists pip3; then
    print_info "Installing pip..."
    apt-get install -y python3-pip
else
    print_success "pip is already installed"
fi

# Install python3-venv if not present
if ! dpkg -l | grep -q python3-venv; then
    print_info "Installing python3-venv..."
    apt-get install -y python3-venv
else
    print_success "python3-venv is already installed"
fi

# Install system dependencies for reportlab
print_info "Installing system dependencies..."
apt-get install -y build-essential python3-dev libfreetype6-dev libpng-dev libjpeg-dev

# Create data directory if it doesn't exist
print_info "Creating data directory..."
mkdir -p "${DATA_DIR}"

# Remove old virtual environment if it exists
if [ -d "${VENV_DIR}" ]; then
    print_warning "Removing old virtual environment..."
    rm -rf "${VENV_DIR}"
fi

# Create new virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv "${VENV_DIR}"

# Activate virtual environment and install dependencies
print_info "Installing Python dependencies..."
source "${VENV_DIR}/bin/activate"

# Upgrade pip in virtual environment
pip install --upgrade pip

# Install all requirements
pip install -r "${INSTALL_DIR}/requirements.txt"

deactivate

# Set proper ownership
print_info "Setting file permissions..."
chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${INSTALL_DIR}"
chmod -R 755 "${INSTALL_DIR}"
chmod 775 "${DATA_DIR}"

# Create systemd service file
print_info "Creating systemd service..."
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Coffee Cost Calculator Web Application
After=network.target

[Service]
Type=notify
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile - --error-logfile - app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd daemon
print_info "Reloading systemd daemon..."
systemctl daemon-reload

# Stop service if running
if systemctl is-active --quiet ${APP_NAME}; then
    print_info "Stopping existing service..."
    systemctl stop ${APP_NAME}
fi

# Enable and start service
print_info "Enabling and starting service..."
systemctl enable ${APP_NAME}
systemctl start ${APP_NAME}

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet ${APP_NAME}; then
    print_success "Service started successfully!"
    
    # Get the service status
    print_info "Service status:"
    systemctl status ${APP_NAME} --no-pager -l
    
    echo ""
    print_success "============================================"
    print_success "Installation completed successfully!"
    print_success "============================================"
    echo ""
    print_info "Service name: ${APP_NAME}"
    print_info "Installation directory: ${INSTALL_DIR}"
    print_info "Data directory: ${DATA_DIR}"
    print_info "Application URL: http://localhost:5000"
    echo ""
    print_info "Useful commands:"
    echo "  - View status:    sudo systemctl status ${APP_NAME}"
    echo "  - Stop service:   sudo systemctl stop ${APP_NAME}"
    echo "  - Start service:  sudo systemctl start ${APP_NAME}"
    echo "  - Restart service: sudo systemctl restart ${APP_NAME}"
    echo "  - View logs:      sudo journalctl -u ${APP_NAME} -f"
    echo ""
    print_info "The database is stored at: ${DATA_DIR}/coffee_calculator.db"
    echo ""
else
    print_error "Service failed to start!"
    print_error "Check logs with: sudo journalctl -u ${APP_NAME} -n 50"
    exit 1
fi
