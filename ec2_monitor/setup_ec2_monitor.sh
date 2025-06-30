#!/bin/bash

# EC2 Monitor Setup Script
# This script installs and configures EC2 Monitor as a systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="ec2-enhanced-monitor"
INSTALL_DIR="/opt/ec2-enhanced-monitor"
LOG_DIR="/var/log/ec2-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON_SCRIPT="ec2_monitor.py"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    apt-get update -q
    
    # Install Python3 and pip if not present
    apt-get install -y python3 python3-pip python3-venv
    
#     print_status "Installing Python dependencies..."
#     pip3 install psutil pytz
# }

# Create installation directory
create_directories() {
    print_status "Creating directories..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Create log directory with proper permissions
    mkdir -p "$LOG_DIR"
    chown nobody:nogroup "$LOG_DIR"
    chmod 755 "$LOG_DIR"
}

# Copy Python script
install_script() {
    print_status "Installing EC2 Monitor script..."
    
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script '$PYTHON_SCRIPT' not found in current directory"
        print_error "Please ensure ec2_monitor.py is in the same directory as this setup script"
        exit 1
    fi
    
    # Copy script to installation directory
    cp "$PYTHON_SCRIPT" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/$PYTHON_SCRIPT"
    
    # Set ownership
    chown -R nobody:nogroup "$INSTALL_DIR"
}

# Create systemd service file
create_service_file() {
    print_status "Creating systemd service file..."
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Enhanced EC2 Instance Monitor for Complete Observability
Documentation=Comprehensive EC2 monitoring with system metrics, logs, and security events
After=network.target
Wants=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/$PYTHON_SCRIPT
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ec2-enhanced-monitor

# Resource limits (increased for comprehensive monitoring)
MemoryMax=512M
CPUQuota=30%

# Security settings (enhanced permissions for log access)
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR
ReadOnlyPaths=/var/log
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
SupplementaryGroups=adm

[Install]
WantedBy=multi-user.target
EOF

    print_status "Service file created at $SERVICE_FILE"
}

# Enable and start service
setup_service() {
    print_status "Setting up systemd service..."
    
    # Reload systemd to recognize new service
    systemctl daemon-reload
    
    # Enable service to start on boot
    systemctl enable "$SERVICE_NAME"
    
    # Start the service
    systemctl start "$SERVICE_NAME"
    
    # Wait a moment for service to start
    sleep 2
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "✅ EC2 Monitor service started successfully!"
    else
        print_error "❌ Failed to start EC2 Monitor service"
        print_error "Check logs with: journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

# Show service status and helpful commands
show_status() {
    print_status "=== Enhanced EC2 Monitor Installation Complete ==="
    echo
    print_status "Service Status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo
    print_status "Useful Commands:"
    echo "  Start service:    sudo systemctl start $SERVICE_NAME"
    echo "  Stop service:     sudo systemctl stop $SERVICE_NAME"
    echo "  Restart service:  sudo systemctl restart $SERVICE_NAME"
    echo "  Service status:   sudo systemctl status $SERVICE_NAME"
    echo "  View logs:        sudo journalctl -u $SERVICE_NAME -f"
    echo "  View metrics:     sudo tail -f $LOG_DIR/ec2_comprehensive.log"
    echo
    print_status "Log Directory: $LOG_DIR"
    print_status "Install Directory: $INSTALL_DIR"
}

# Uninstall function
uninstall_service() {
    print_warning "Uninstalling Enhanced EC2 Monitor service..."
    
    # Stop and disable service
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$SERVICE_FILE"
    
    # Remove installation directory
    rm -rf "$INSTALL_DIR"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Enhanced EC2 Monitor service uninstalled"
    print_warning "Log directory $LOG_DIR was preserved"
}

# Main installation function
main() {
    print_status "Starting Enhanced EC2 Monitor installation..."
    
    check_root
    install_dependencies
    create_directories
    install_script
    create_service_file
    setup_service
    show_status
}

# Handle command line arguments
case "${1:-}" in
    "uninstall")
        check_root
        uninstall_service
        ;;
    "status")
        systemctl status "$SERVICE_NAME" --no-pager -l
        ;;
    "logs")
        journalctl -u "$SERVICE_NAME" -f
        ;;
    *)
        main
        ;;
esac
