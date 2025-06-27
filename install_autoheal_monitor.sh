#!/bin/bash
# install_autoheal_monitor.sh
# Installation script for AWS Autoheal System Monitoring Agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    # Update package list
    apt-get update
    
    # Install Python3 and pip if not already installed
    apt-get install -y python3 python3-pip python3-venv
    
    # Install required Python packages
    pip3 install psutil
    
    log "Dependencies installed successfully"
}

# Create directories
create_directories() {
    log "Creating directories..."
    
    # Create main application directory
    mkdir -p /opt/autoheal
    
    # Create configuration directory
    mkdir -p /etc/autoheal
    
    # Create log directory with proper permissions
    mkdir -p /var/log/autoheal
    chown root:root /var/log/autoheal
    chmod 755 /var/log/autoheal
    
    log "Directories created successfully"
}

# Install the monitoring agent
install_monitor() {
    log "Installing monitoring agent..."
    
    # Copy the Python script (assuming it's in the current directory)
    if [[ -f "monitor_agent.py" ]]; then
        cp monitor_agent.py /opt/autoheal/
        chmod +x /opt/autoheal/monitor_agent.py
        chown root:root /opt/autoheal/monitor_agent.py
    else
        error "monitor_agent.py not found in current directory"
        exit 1
    fi
    
    log "Monitoring agent installed successfully"
}

# Create configuration file
create_config() {
    log "Creating configuration file..."
    
    cat > /etc/autoheal/monitor.conf << 'EOF'
{
    "log_level": "INFO",
    "log_path": "/var/log/autoheal",
    "monitoring_interval": 1,
    "anomaly_check_interval": 60,
    "max_log_size": "100MB",
    "log_retention_days": 7,
    "enable_process_monitoring": true,
    "enable_network_monitoring": true,
    "enable_disk_monitoring": true,
    "thresholds": {
        "cpu_percent": 80.0,
        "memory_percent": 85.0,
        "disk_usage_percent": 90.0,
        "process_cpu_high": 50.0,
        "process_memory_high": 30.0
    }
}
EOF

    chown root:root /etc/autoheal/monitor.conf
    chmod 644 /etc/autoheal/monitor.conf
    
    log "Configuration file created successfully"
}

# Install systemd service
install_systemd_service() {
    log "Installing systemd service..."
    
    cat > /etc/systemd/system/autoheal-monitor.service << 'EOF'
[Unit]
Description=AWS Autoheal System Monitoring Agent
Documentation=https://github.com/your-org/autoheal-monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/bin/python3 /opt/autoheal/monitor_agent.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5
TimeoutStopSec=20

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/log/autoheal /etc/autoheal
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autoheal-monitor

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable autoheal-monitor.service
    
    log "Systemd service installed and enabled"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/autoheal-monitor << 'EOF'
/var/log/autoheal/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload autoheal-monitor.service > /dev/null 2>&1 || true
    endscript
}
EOF

    log "Log rotation configured"
}

# Create helper scripts
create_helper_scripts() {
    log "Creating helper scripts..."
    
    # Create status check script
    cat > /usr/local/bin/autoheal-status << 'EOF'
#!/bin/bash
# Quick status check for autoheal monitor

echo "=== Autoheal Monitor Status ==="
echo "Service Status:"
systemctl status autoheal-monitor.service --no-pager -l

echo -e "\n=== Recent Logs ==="
journalctl -u autoheal-monitor.service --no-pager -n 10

echo -e "\n=== Log Files ==="
ls -la /var/log/autoheal/

echo -e "\n=== Current System Load ==="
uptime
free -h
df -h /
EOF

    chmod +x /usr/local/bin/autoheal-status
    
    # Create anomaly check script
    cat > /usr/local/bin/autoheal-anomalies << 'EOF'
#!/bin/bash
# Check recent anomalies

echo "=== Recent Anomalies (Last 24 hours) ==="
if [[ -f /var/log/autoheal/anomaly_alerts.log ]]; then
    tail -n 100 /var/log/autoheal/anomaly_alerts.log | grep "$(date +%Y-%m-%d)" || echo "No anomalies found today"
else
    echo "Anomaly log file not found"
fi
EOF

    chmod +x /usr/local/bin/autoheal-anomalies
    
    # Create log viewer script
    cat > /usr/local/bin/autoheal-logs << 'EOF'
#!/bin/bash
# View autoheal logs

LOG_TYPE=${1:-"all"}

case $LOG_TYPE in
    "metrics")
        echo "=== System Metrics Log ==="
        tail -f /var/log/autoheal/system_metrics.log
        ;;
    "processes")
        echo "=== Process Metrics Log ==="
        tail -f /var/log/autoheal/process_metrics.log
        ;;
    "anomalies")
        echo "=== Anomaly Alerts Log ==="
        tail -f /var/log/autoheal/anomaly_alerts.log
        ;;
    "monitor")
        echo "=== Monitor Agent Log ==="
        tail -f /var/log/autoheal/monitor_agent.log
        ;;
    "all"|*)
        echo "=== All Autoheal Logs ==="
        echo "Available log types: metrics, processes, anomalies, monitor"
        echo "Usage: autoheal-logs [metrics|processes|anomalies|monitor]"
        echo ""
        echo "Recent activity:"
        find /var/log/autoheal -name "*.log" -exec tail -n 5 {} \; -exec echo "---" \;
        ;;
esac
EOF

    chmod +x /usr/local/bin/autoheal-logs
    
    log "Helper scripts created"
}

# Test the installation
test_installation() {
    log "Testing installation..."
    
    # Test configuration file
    if python3 -c "import json; json.load(open('/etc/autoheal/monitor.conf'))" 2>/dev/null; then
        log "Configuration file is valid JSON"
    else
        error "Configuration file is invalid"
        exit 1
    fi
    
    # Test Python script syntax
    if python3 -m py_compile /opt/autoheal/monitor_agent.py; then
        log "Python script syntax is valid"
    else
        error "Python script has syntax errors"
        exit 1
    fi
    
    # Test systemd service file
    if systemctl is-enabled autoheal-monitor.service >/dev/null 2>&1; then
        log "Systemd service is enabled"
    else
        warn "Systemd service is not enabled"
    fi
    
    log "Installation test completed"
}

# Start the service
start_service() {
    log "Starting autoheal monitor service..."
    
    systemctl start autoheal-monitor.service
    
    # Wait a moment and check status
    sleep 3
    
    if systemctl is-active autoheal-monitor.service >/dev/null 2>&1; then
        log "Service started successfully"
    else
        error "Service failed to start"
        systemctl status autoheal-monitor.service --no-pager
        exit 1
    fi
}

# Create uninstall script
create_uninstall_script() {
    log "Creating uninstall script..."
    
    cat > /usr/local/bin/uninstall-autoheal-monitor << 'EOF'
#!/bin/bash
# Uninstall script for autoheal monitor

echo "Stopping and disabling autoheal monitor service..."
systemctl stop autoheal-monitor.service 2>/dev/null || true
systemctl disable autoheal-monitor.service 2>/dev/null || true

echo "Removing service file..."
rm -f /etc/systemd/system/autoheal-monitor.service
systemctl daemon-reload

echo "Removing application files..."
rm -rf /opt/autoheal
rm -rf /etc/autoheal

echo "Removing log files..."
rm -rf /var/log/autoheal

echo "Removing logrotate configuration..."
rm -f /etc/logrotate.d/autoheal-monitor

echo "Removing helper scripts..."
rm -f /usr/local/bin/autoheal-status
rm -f /usr/local/bin/autoheal-anomalies
rm -f /usr/local/bin/autoheal-logs
rm -f /usr/local/bin/uninstall-autoheal-monitor

echo "Autoheal monitor has been completely removed."
EOF

    chmod +x /usr/local/bin/uninstall-autoheal-monitor
    
    log "Uninstall script created at /usr/local/bin/uninstall-autoheal-monitor"
}

# Print usage information
print_usage() {
    echo "=== AWS Autoheal Monitor Installation Complete ==="
    echo ""
    echo "Service Management:"
    echo "  systemctl start autoheal-monitor.service    # Start the service"
    echo "  systemctl stop autoheal-monitor.service     # Stop the service"
    echo "  systemctl restart autoheal-monitor.service  # Restart the service"
    echo "  systemctl status autoheal-monitor.service   # Check service status"
    echo ""
    echo "Helper Commands:"
    echo "  autoheal-status      # Quick status overview"
    echo "  autoheal-anomalies   # View recent anomalies"
    echo "  autoheal-logs        # View logs (specify type: metrics, processes, anomalies, monitor)"
    echo ""
    echo "Configuration:"
    echo "  Edit /etc/autoheal/monitor.conf to modify settings"
    echo "  Restart service after configuration changes"
    echo ""
    echo "Log Files:"
    echo "  /var/log/autoheal/system_metrics.log    # System metrics"
    echo "  /var/log/autoheal/process_metrics.log   # Process information"
    echo "  /var/log/autoheal/anomaly_alerts.log    # Anomaly alerts"
    echo "  /var/log/autoheal/monitor_agent.log     # Agent logs"
    echo ""
    echo "Uninstall:"
    echo "  /usr/local/bin/uninstall-autoheal-monitor"
}

# Main installation function
main() {
    log "Starting AWS Autoheal Monitor installation..."
    
    check_root
    install_dependencies
    create_directories
    install_monitor
    create_config
    install_systemd_service
    setup_log_rotation
    create_helper_scripts
    test_installation
    start_service
    create_uninstall_script
    
    log "Installation completed successfully!"
    echo ""
    print_usage
}

# Handle command line arguments
case "${1:-install}" in
    "install")
        main
        ;;
    "uninstall")
        if [[ -f /usr/local/bin/uninstall-autoheal-monitor ]]; then
            /usr/local/bin/uninstall-autoheal-monitor
        else
            error "Uninstall script not found. Manual cleanup required."
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [install|uninstall|help]"
        echo ""
        echo "Commands:"
        echo "  install    - Install the autoheal monitor (default)"
        echo "  uninstall  - Remove the autoheal monitor"
        echo "  help       - Show this help message"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
