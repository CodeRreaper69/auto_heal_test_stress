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
