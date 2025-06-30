#!/usr/bin/env python3
"""
EC2 Instance Monitor for Grafana/Loki Integration
Collects system metrics every 30 seconds with 2-hour log rotation
"""

import json
import time
import psutil
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import pytz
import threading
import glob

class EC2Monitor:
    def __init__(self, log_dir="/var/log/ec2-monitor", interval=30):
        self.log_dir = log_dir
        self.interval = interval
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logger
        self.setup_logger()
        
        # Memory threshold for alerts (80%)
        self.memory_threshold = 80
        
    def setup_logger(self):
        """Setup rotating file handler with IST timezone"""
        log_file = os.path.join(self.log_dir, "ec2_metrics.log")
        
        # Custom formatter for IST timestamps
        formatter = logging.Formatter('%(message)s')
        
        # Rotate every hour, keep only 2 files (2 hours total)
        handler = TimedRotatingFileHandler(
            log_file, 
            when='H', 
            interval=1, 
            backupCount=2
        )
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('ec2_monitor')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        # Start cleanup thread
        self.start_cleanup_thread()
    
    def get_ist_timestamp(self):
        """Get current timestamp in IST"""
        return datetime.now(self.ist).isoformat()
    
    def collect_metrics(self):
        """Collect htop-like system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Top processes (like htop)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage, get top 10
            top_processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:10]
            
            # Build metrics object
            metrics = {
                "timestamp": self.get_ist_timestamp(),
                "level": "INFO",
                "service": "ec2-monitor",
                "metrics": {
                    "cpu": {
                        "percent": cpu_percent,
                        "count": cpu_count,
                        "load_avg": {
                            "1min": load_avg[0],
                            "5min": load_avg[1], 
                            "15min": load_avg[2]
                        }
                    },
                    "memory": {
                        "total_gb": round(memory.total / 1024**3, 2),
                        "used_gb": round(memory.used / 1024**3, 2),
                        "available_gb": round(memory.available / 1024**3, 2),
                        "percent": memory.percent
                    },
                    "swap": {
                        "total_gb": round(swap.total / 1024**3, 2),
                        "used_gb": round(swap.used / 1024**3, 2),
                        "percent": swap.percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / 1024**3, 2),
                        "used_gb": round(disk.used / 1024**3, 2),
                        "free_gb": round(disk.free / 1024**3, 2),
                        "percent": round((disk.used / disk.total) * 100, 2)
                    },
                    "network": {
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv
                    },
                    "top_processes": top_processes
                }
            }
            
            # Check for memory alert
            if memory.percent > self.memory_threshold:
                alert_metrics = metrics.copy()
                alert_metrics["level"] = "WARNING"
                alert_metrics["alert"] = {
                    "type": "high_memory_usage",
                    "value": memory.percent,
                    "threshold": self.memory_threshold,
                    "message": f"Memory usage at {memory.percent}% exceeds threshold of {self.memory_threshold}%"
                }
                self.logger.warning(json.dumps(alert_metrics))
            
            return metrics
            
        except Exception as e:
            error_log = {
                "timestamp": self.get_ist_timestamp(),
                "level": "ERROR",
                "service": "ec2-monitor",
                "error": str(e),
                "message": "Failed to collect metrics"
            }
            self.logger.error(json.dumps(error_log))
            return None
    
    def cleanup_old_logs(self):
        """Remove logs older than 2 hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=2)
            log_pattern = os.path.join(self.log_dir, "ec2_metrics.log*")
            
            for log_file in glob.glob(log_pattern):
                if os.path.isfile(log_file):
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_time:
                        os.remove(log_file)
                        print(f"Removed old log file: {log_file}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def start_cleanup_thread(self):
        """Start background thread for log cleanup"""
        def cleanup_worker():
            while True:
                time.sleep(1800)  # Run every 30 minutes
                self.cleanup_old_logs()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def run(self):
        """Main monitoring loop"""
        print(f"Starting EC2 Monitor - logging to {self.log_dir}")
        print(f"Collection interval: {self.interval} seconds")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                metrics = self.collect_metrics()
                if metrics:
                    self.logger.info(json.dumps(metrics))
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\nStopping EC2 Monitor...")
        except Exception as e:
            print(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor = EC2Monitor()
    monitor.run()
