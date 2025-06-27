#!/usr/bin/env python3
"""
AWS Autoheal System Monitoring Agent
Monitors system resources, processes, and logs for anomaly detection
Runs as a systemd service and provides htop-like monitoring capabilities
"""

import psutil
import time
import json
import logging
import os
import sys
import threading
import signal
import socket
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import subprocess
import re

@dataclass
class SystemMetrics:
    timestamp: str
    hostname: str
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    memory_total: int
    disk_usage_percent: float
    disk_free: int
    disk_used: int
    disk_total: int
    load_avg_1: float
    load_avg_5: float
    load_avg_15: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    boot_time: float
    uptime_seconds: float

@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int
    memory_vms: int
    status: str
    create_time: float
    num_threads: int
    num_fds: int
    cmdline: str
    username: str

@dataclass
class AnomalyAlert:
    timestamp: str
    severity: str
    metric: str
    current_value: float
    threshold: float
    duration_minutes: int
    description: str
    hostname: str

class SystemMonitor:
    def __init__(self, config_file="/etc/autoheal/monitor.conf"):
        self.hostname = socket.gethostname()
        self.config = self.load_config(config_file)
        self.setup_logging()
        
        # Data storage for anomaly detection
        self.metrics_history = deque(maxlen=3600)  # 1 hour of data (1 per second)
        self.process_history = deque(maxlen=3600)
        self.network_baseline = None
        self.disk_baseline = None
        
        # Anomaly thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'load_avg_1': psutil.cpu_count() * 2,
            'process_cpu_high': 50.0,
            'process_memory_high': 30.0
        }
        
        # Time windows for anomaly detection (in minutes)
        self.time_windows = [3, 5, 15, 60]
        
        self.running = True
        self.lock = threading.Lock()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def load_config(self, config_file):
        """Load configuration from file or use defaults"""
        default_config = {
            "log_level": "INFO",
            "log_path": "/var/log/autoheal",
            "monitoring_interval": 1,
            "anomaly_check_interval": 60,
            "max_log_size": "100MB",
            "log_retention_days": 7,
            "enable_process_monitoring": True,
            "enable_network_monitoring": True,
            "enable_disk_monitoring": True
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        
        return default_config

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.config['log_path']
        os.makedirs(log_dir, exist_ok=True)
        
        # Main system metrics log
        self.metrics_logger = self.create_logger(
            'metrics', 
            os.path.join(log_dir, 'system_metrics.log'),
            '%(asctime)s - METRICS - %(message)s'
        )
        
        # Process monitoring log
        self.process_logger = self.create_logger(
            'processes',
            os.path.join(log_dir, 'process_metrics.log'),
            '%(asctime)s - PROCESS - %(message)s'
        )
        
        # Anomaly detection log
        self.anomaly_logger = self.create_logger(
            'anomalies',
            os.path.join(log_dir, 'anomaly_alerts.log'),
            '%(asctime)s - ANOMALY - %(levelname)s - %(message)s'
        )
        
        # Main application log
        self.app_logger = self.create_logger(
            'app',
            os.path.join(log_dir, 'monitor_agent.log'),
            '%(asctime)s - %(levelname)s - %(message)s'
        )

    def create_logger(self, name, filename, format_str):
        """Create a logger with specified configuration"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.config['log_level']))
        
        handler = logging.FileHandler(filename)
        handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(handler)
        
        return logger

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.app_logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Load average
            load_avg = os.getloadavg()
            
            # Network
            network = psutil.net_io_counters()
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                hostname=self.hostname,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_usage_percent=disk.percent,
                disk_free=disk.free,
                disk_used=disk.used,
                disk_total=disk.total,
                load_avg_1=load_avg[0],
                load_avg_5=load_avg[1],
                load_avg_15=load_avg[2],
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                boot_time=boot_time,
                uptime_seconds=uptime
            )
        except Exception as e:
            self.app_logger.error(f"Error collecting system metrics: {e}")
            return None

    def get_top_processes(self, limit=20) -> List[ProcessInfo]:
        """Get top processes similar to htop output"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'status', 'create_time', 
                                           'num_threads', 'cmdline', 'username']):
                try:
                    pinfo = proc.info
                    if pinfo['cmdline']:
                        cmdline = ' '.join(pinfo['cmdline'][:5])  # First 5 args
                    else:
                        cmdline = pinfo['name']
                    
                    # Get file descriptor count safely
                    num_fds = 0
                    try:
                        num_fds = proc.num_fds()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'],
                        cpu_percent=pinfo['cpu_percent'] or 0.0,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        memory_vms=pinfo['memory_info'].vms if pinfo['memory_info'] else 0,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'] or 0.0,
                        num_threads=pinfo['num_threads'] or 0,
                        num_fds=num_fds,
                        cmdline=cmdline[:100],  # Limit cmdline length
                        username=pinfo['username'] or 'unknown'
                    )
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Sort by CPU usage
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.app_logger.error(f"Error collecting process information: {e}")
            return []

    def detect_anomalies(self) -> List[AnomalyAlert]:
        """Detect anomalies in system metrics over different time windows"""
        anomalies = []
        current_time = datetime.now()
        
        if len(self.metrics_history) < 180:  # Need at least 3 minutes of data
            return anomalies
        
        with self.lock:
            metrics_list = list(self.metrics_history)
        
        for window_minutes in self.time_windows:
            cutoff_time = current_time - timedelta(minutes=window_minutes)
            
            # Filter metrics for this time window
            window_metrics = [
                m for m in metrics_list 
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
            
            if not window_metrics:
                continue
                
            # Check CPU anomalies
            avg_cpu = sum(m.cpu_percent for m in window_metrics) / len(window_metrics)
            if avg_cpu > self.thresholds['cpu_percent']:
                anomalies.append(AnomalyAlert(
                    timestamp=current_time.isoformat(),
                    severity='HIGH' if avg_cpu > 95 else 'MEDIUM',
                    metric='cpu_percent',
                    current_value=avg_cpu,
                    threshold=self.thresholds['cpu_percent'],
                    duration_minutes=window_minutes,
                    description=f"High CPU usage detected: {avg_cpu:.1f}% over {window_minutes} minutes",
                    hostname=self.hostname
                ))
            
            # Check Memory anomalies
            avg_memory = sum(m.memory_percent for m in window_metrics) / len(window_metrics)
            if avg_memory > self.thresholds['memory_percent']:
                anomalies.append(AnomalyAlert(
                    timestamp=current_time.isoformat(),
                    severity='HIGH' if avg_memory > 95 else 'MEDIUM',
                    metric='memory_percent',
                    current_value=avg_memory,
                    threshold=self.thresholds['memory_percent'],
                    duration_minutes=window_minutes,
                    description=f"High memory usage detected: {avg_memory:.1f}% over {window_minutes} minutes",
                    hostname=self.hostname
                ))
            
            # Check Load average anomalies
            avg_load = sum(m.load_avg_1 for m in window_metrics) / len(window_metrics)
            if avg_load > self.thresholds['load_avg_1']:
                anomalies.append(AnomalyAlert(
                    timestamp=current_time.isoformat(),
                    severity='MEDIUM',
                    metric='load_avg_1',
                    current_value=avg_load,
                    threshold=self.thresholds['load_avg_1'],
                    duration_minutes=window_minutes,
                    description=f"High load average detected: {avg_load:.2f} over {window_minutes} minutes",
                    hostname=self.hostname
                ))
        
        return anomalies

    def check_process_anomalies(self, processes: List[ProcessInfo]) -> List[AnomalyAlert]:
        """Check for process-level anomalies"""
        anomalies = []
        current_time = datetime.now()
        
        for proc in processes[:10]:  # Check top 10 processes
            # High CPU usage by single process
            if proc.cpu_percent > self.thresholds['process_cpu_high']:
                anomalies.append(AnomalyAlert(
                    timestamp=current_time.isoformat(),
                    severity='MEDIUM',
                    metric='process_cpu',
                    current_value=proc.cpu_percent,
                    threshold=self.thresholds['process_cpu_high'],
                    duration_minutes=0,
                    description=f"Process {proc.name} (PID: {proc.pid}) using {proc.cpu_percent:.1f}% CPU",
                    hostname=self.hostname
                ))
            
            # High memory usage by single process
            if proc.memory_percent > self.thresholds['process_memory_high']:
                anomalies.append(AnomalyAlert(
                    timestamp=current_time.isoformat(),
                    severity='MEDIUM',
                    metric='process_memory',
                    current_value=proc.memory_percent,
                    threshold=self.thresholds['process_memory_high'],
                    duration_minutes=0,
                    description=f"Process {proc.name} (PID: {proc.pid}) using {proc.memory_percent:.1f}% memory",
                    hostname=self.hostname
                ))
        
        return anomalies

    def log_metrics(self, metrics: SystemMetrics):
        """Log system metrics"""
        metrics_json = json.dumps(asdict(metrics))
        self.metrics_logger.info(metrics_json)

    def log_processes(self, processes: List[ProcessInfo]):
        """Log process information"""
        for proc in processes:
            process_json = json.dumps(asdict(proc))
            self.process_logger.info(process_json)

    def log_anomalies(self, anomalies: List[AnomalyAlert]):
        """Log anomaly alerts"""
        for anomaly in anomalies:
            log_level = logging.ERROR if anomaly.severity == 'HIGH' else logging.WARNING
            anomaly_json = json.dumps(asdict(anomaly))
            self.anomaly_logger.log(log_level, anomaly_json)

    def print_status(self, metrics: SystemMetrics, processes: List[ProcessInfo]):
        """Print current status to stdout (optional, for debugging)"""
        print(f"\n=== System Status - {metrics.timestamp} ===")
        print(f"Hostname: {metrics.hostname}")
        print(f"CPU: {metrics.cpu_percent:.1f}%")
        print(f"Memory: {metrics.memory_percent:.1f}% ({metrics.memory_used // (1024**3)}GB/{metrics.memory_total // (1024**3)}GB)")
        print(f"Disk: {metrics.disk_usage_percent:.1f}% ({metrics.disk_used // (1024**3)}GB/{metrics.disk_total // (1024**3)}GB)")
        print(f"Load: {metrics.load_avg_1:.2f}, {metrics.load_avg_5:.2f}, {metrics.load_avg_15:.2f}")
        print(f"Uptime: {metrics.uptime_seconds / 3600:.1f} hours")
        
        print(f"\n=== Top Processes ===")
        print(f"{'PID':<8} {'NAME':<15} {'CPU%':<6} {'MEM%':<6} {'STATUS':<8} {'THREADS':<8} {'COMMAND'}")
        for proc in processes[:10]:
            print(f"{proc.pid:<8} {proc.name[:14]:<15} {proc.cpu_percent:<6.1f} {proc.memory_percent:<6.1f} {proc.status:<8} {proc.num_threads:<8} {proc.cmdline[:40]}")

    def run(self):
        """Main monitoring loop"""
        self.app_logger.info("Starting AWS Autoheal System Monitor")
        self.app_logger.info(f"Hostname: {self.hostname}")
        self.app_logger.info(f"Monitoring interval: {self.config['monitoring_interval']}s")
        
        anomaly_check_counter = 0
        anomaly_check_interval = self.config['anomaly_check_interval']
        
        try:
            while self.running:
                # Collect metrics
                metrics = self.get_system_metrics()
                if metrics:
                    # Store metrics for anomaly detection
                    with self.lock:
                        self.metrics_history.append(metrics)
                    
                    # Log metrics
                    self.log_metrics(metrics)
                    
                    # Collect and log process information
                    if self.config['enable_process_monitoring']:
                        processes = self.get_top_processes()
                        self.log_processes(processes)
                        
                        # Print status (optional - comment out for production)
                        # self.print_status(metrics, processes)
                    
                    # Check for anomalies periodically
                    anomaly_check_counter += self.config['monitoring_interval']
                    if anomaly_check_counter >= anomaly_check_interval:
                        anomaly_check_counter = 0
                        
                        # System anomalies
                        system_anomalies = self.detect_anomalies()
                        
                        # Process anomalies
                        process_anomalies = []
                        if processes:
                            process_anomalies = self.check_process_anomalies(processes)
                        
                        all_anomalies = system_anomalies + process_anomalies
                        if all_anomalies:
                            self.log_anomalies(all_anomalies)
                            self.app_logger.warning(f"Detected {len(all_anomalies)} anomalies")
                
                time.sleep(self.config['monitoring_interval'])
                
        except KeyboardInterrupt:
            self.app_logger.info("Monitor interrupted by user")
        except Exception as e:
            self.app_logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.app_logger.info("AWS Autoheal System Monitor stopped")

def main():
    """Main entry point"""
    # Check if running as root (recommended for system monitoring)
    if os.geteuid() != 0:
        print("Warning: Running as non-root user. Some metrics may not be available.")
    
    # Create config directory if it doesn't exist
    os.makedirs("/etc/autoheal", exist_ok=True)
    
    # Start the monitor
    monitor = SystemMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
