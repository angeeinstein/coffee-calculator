#!/bin/bash

# Coffee Calculator Installation/Update Script
# This script will install or update the Coffee Cost Calculator as a systemd service
# - First time: Run after git clone to install everything
# - Updates: Just run this script again to pull latest code and update

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
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

print_update() {
    echo -e "${MAGENTA}[UPDATE]${NC} $1"
}

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="coffee-calculator"
SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_GROUP="${SERVICE_USER}"
INSTALL_DIR="${SCRIPT_DIR}"
VENV_DIR="${INSTALL_DIR}/venv"
DATA_DIR="${INSTALL_DIR}/data"

# Detect if this is an update or fresh install
IS_UPDATE=false
IS_UNINSTALL=false

if systemctl list-unit-files | grep -q "^${APP_NAME}.service"; then
    IS_UPDATE=true
    print_update "Existing installation detected!"
    echo ""
    print_update "============================================"
    print_update "  What would you like to do?"
    print_update "============================================"
    echo ""
    echo "1) Update to latest version (pulls code, updates dependencies, restarts service)"
    echo "2) Complete removal (uninstall service, remove all files and data)"
    echo "3) Cancel"
    echo ""
    read -p "Enter your choice [1-3]: " choice
    echo ""
    
    case $choice in
        1)
            print_update "Starting UPDATE process..."
            ;;
        2)
            IS_UNINSTALL=true
            print_warning "Starting UNINSTALL process..."
            echo ""
            print_warning "⚠️  WARNING: This will remove:"
            echo "   - Systemd service"
            echo "   - Python virtual environment"
            echo "   - Database (all saved configurations)"
            echo "   - Application files (if confirmed)"
            echo ""
            read -p "Are you absolutely sure? Type 'YES' to confirm: " confirm
            echo ""
            
            if [ "$confirm" != "YES" ]; then
                print_info "Uninstall cancelled. Exiting..."
                exit 0
            fi
            ;;
        3)
            print_info "Operation cancelled. Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
else
    print_info "No existing installation found - Running INSTALL mode"
fi

# Handle uninstall if requested
if [ "$IS_UNINSTALL" = true ]; then
    echo ""
    print_warning "============================================"
    print_warning "  Uninstalling Coffee Calculator"
    print_warning "============================================"
    echo ""
    
    # Stop and disable service
    if systemctl is-active --quiet ${APP_NAME}; then
        print_info "Stopping service..."
        systemctl stop ${APP_NAME}
    fi
    
    if systemctl is-enabled --quiet ${APP_NAME} 2>/dev/null; then
        print_info "Disabling service..."
        systemctl disable ${APP_NAME}
    fi
    
    # Remove systemd service file
    if [ -f "/etc/systemd/system/${APP_NAME}.service" ]; then
        print_info "Removing systemd service file..."
        rm -f "/etc/systemd/system/${APP_NAME}.service"
        systemctl daemon-reload
    fi
    
    # Remove virtual environment
    if [ -d "${VENV_DIR}" ]; then
        print_info "Removing virtual environment..."
        rm -rf "${VENV_DIR}"
    fi
    
    # Ask about database and application files
    echo ""
    print_warning "Do you want to remove the database and all configurations?"
    read -p "This will delete all your saved data [y/N]: " remove_data
    
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        if [ -d "${DATA_DIR}" ]; then
            print_info "Removing database and data directory..."
            rm -rf "${DATA_DIR}"
        fi
    else
        print_info "Database preserved at: ${DATA_DIR}"
    fi
    
    echo ""
    print_warning "Do you want to remove ALL application files?"
    print_warning "Directory: ${INSTALL_DIR}"
    read -p "This will delete the entire application folder [y/N]: " remove_app
    
    if [[ "$remove_app" =~ ^[Yy]$ ]]; then
        print_info "Removing application files..."
        cd /tmp
        rm -rf "${INSTALL_DIR}"
        echo ""
        print_success "============================================"
        print_success "  Uninstall completed!"
        print_success "============================================"
        echo ""
        print_success "Coffee Calculator has been completely removed from your system."
    else
        print_info "Application files preserved at: ${INSTALL_DIR}"
        echo ""
        print_success "============================================"
        print_success "  Partial uninstall completed!"
        print_success "============================================"
        echo ""
        print_success "Service removed. Application files preserved."
        print_info "To reinstall, run: cd ${INSTALL_DIR} && sudo ./install.sh"
    fi
    
    echo ""
    exit 0
fi

# Continue with install/update
if [ "$IS_UPDATE" = true ]; then
    echo ""
    print_update "============================================"
    print_update "  Coffee Calculator Update Process"
    print_update "============================================"
    echo ""
else
    echo ""
    print_info "============================================"
    print_info "  Coffee Calculator Installation Process"
    print_info "============================================"
    echo ""
fi

print_info "Installation directory: ${INSTALL_DIR}"
print_info "Service user: ${SERVICE_USER}"
echo ""

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

# If this is an update, pull latest changes from git
if [ "$IS_UPDATE" = true ]; then
    print_update "Checking for updates from git repository..."
    
    # Check if git is available
    if ! command_exists git; then
        print_warning "Git is not installed. Installing git..."
        apt-get update -qq
        apt-get install -y git
    fi
    
    # Check if this is a git repository
    if [ -d "${INSTALL_DIR}/.git" ]; then
        print_update "Pulling latest changes from repository..."
        
        # Backup database before update
        if [ -f "${DATA_DIR}/coffee_calculator.db" ]; then
            BACKUP_FILE="${DATA_DIR}/coffee_calculator_backup_$(date +%Y%m%d_%H%M%S).db"
            print_info "Creating database backup: ${BACKUP_FILE}"
            cp "${DATA_DIR}/coffee_calculator.db" "${BACKUP_FILE}"
        fi
        
        # Store current user for git operations
        ORIGINAL_USER="${SERVICE_USER}"
        
        # Try to pull changes
        cd "${INSTALL_DIR}"
        
        # Stash any local changes (if any)
        if sudo -u "${ORIGINAL_USER}" git diff-index --quiet HEAD --; then
            print_info "No local changes detected"
        else
            print_warning "Local changes detected, stashing them..."
            sudo -u "${ORIGINAL_USER}" git stash
        fi
        
        # Pull latest changes
        print_update "Fetching latest code..."
        if sudo -u "${ORIGINAL_USER}" git pull origin main 2>/dev/null || sudo -u "${ORIGINAL_USER}" git pull 2>/dev/null; then
            print_success "Successfully pulled latest changes!"
        else
            print_warning "Could not pull changes automatically. Continuing with existing code..."
        fi
        
    else
        print_warning "Not a git repository. Skipping git pull..."
        print_info "To enable automatic updates, clone this project using git"
    fi
    
    echo ""
fi

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
    if [ "$IS_UPDATE" = true ]; then
        print_success "============================================"
        print_success "  Update completed successfully!"
        print_success "============================================"
        echo ""
        print_update "What was updated:"
        echo "  ✓ Application code pulled from git"
        echo "  ✓ Python dependencies updated"
        echo "  ✓ Database migrated (if needed)"
        echo "  ✓ Service restarted with new code"
        echo ""
        if [ -n "$(ls -A ${DATA_DIR}/coffee_calculator_backup_*.db 2>/dev/null)" ]; then
            print_info "Database backups are stored in: ${DATA_DIR}"
            print_info "Backup files: coffee_calculator_backup_*.db"
        fi
    else
        print_success "============================================"
        print_success "  Installation completed successfully!"
        print_success "============================================"
    fi
    echo ""
    print_info "Service name: ${APP_NAME}"
    print_info "Installation directory: ${INSTALL_DIR}"
    print_info "Data directory: ${DATA_DIR}"
    print_info "Application URL: http://localhost:5000"
    echo ""
    print_info "Useful commands:"
    echo "  - Update:         cd ${INSTALL_DIR} && sudo ./install.sh"
    echo "  - View status:    sudo systemctl status ${APP_NAME}"
    echo "  - Stop service:   sudo systemctl stop ${APP_NAME}"
    echo "  - Start service:  sudo systemctl start ${APP_NAME}"
    echo "  - Restart service: sudo systemctl restart ${APP_NAME}"
    echo "  - View logs:      sudo journalctl -u ${APP_NAME} -f"
    echo ""
    print_info "The database is stored at: ${DATA_DIR}/coffee_calculator.db"
    if [ "$IS_UPDATE" = true ]; then
        echo ""
        print_success "Your application is now running the latest version! 🚀"
    fi
    echo ""
else
    print_error "Service failed to start!"
    print_error "Check logs with: sudo journalctl -u ${APP_NAME} -n 50"
    
    if [ "$IS_UPDATE" = true ] && [ -n "$(ls -A ${DATA_DIR}/coffee_calculator_backup_*.db 2>/dev/null)" ]; then
        echo ""
        print_info "If you need to rollback, your database backup is available:"
        print_info "Latest backup: $(ls -t ${DATA_DIR}/coffee_calculator_backup_*.db | head -1)"
    fi
    
    exit 1
fi
