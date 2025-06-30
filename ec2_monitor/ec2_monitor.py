#!/usr/bin/env python3
"""
Enhanced EC2 Instance Monitor for Complete Observability
Collects system metrics, application logs, and security events
"""

import json
import time
import psutil
import logging
import os
import re
import subprocess
import glob
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
import pytz
import threading
from collections import defaultdict, deque
import socket
import pwd
import grp

class EnhancedEC2Monitor:
    def __init__(self, log_dir="/var/log/ec2-monitor", interval=30):
        self.log_dir = log_dir
        self.interval = interval
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logger
        self.setup_logger()
        
        # Thresholds
        self.memory_threshold = 80
        self.cpu_threshold = 85
        self.disk_threshold = 90
        self.load_threshold = 5.0
        
        # Track log file positions for tailing
        self.log_positions = {}
        self.network_baseline = {}
        
        # Initialize baseline metrics
        self.initialize_baselines()
        
    def setup_logger(self):
        """Setup rotating file handler with IST timezone"""
        log_file = os.path.join(self.log_dir, "ec2_comprehensive.log")
        
        formatter = logging.Formatter('%(message)s')
        
        # Rotate every hour, keep only 2 files (2 hours total)
        handler = TimedRotatingFileHandler(
            log_file, 
            when='H', 
            interval=1, 
            backupCount=2
        )
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('ec2_enhanced_monitor')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        # Start cleanup thread
        self.start_cleanup_thread()
    
    def get_ist_timestamp(self):
        """Get current timestamp in IST"""
        return datetime.now(self.ist).isoformat()
    
    def initialize_baselines(self):
        """Initialize baseline metrics for comparison"""
        try:
            net_io = psutil.net_io_counters(pernic=True)
            self.network_baseline = {
                interface: {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'timestamp': time.time()
                }
                for interface, stats in net_io.items()
            }
        except Exception:
            self.network_baseline = {}
    
    def get_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            load_avg = os.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # All disk partitions
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / 1024**3, 2),
                        'used_gb': round(usage.used / 1024**3, 2),
                        'free_gb': round(usage.free / 1024**3, 2),
                        'percent': round((usage.used / usage.total) * 100, 2)
                    }
                except PermissionError:
                    continue
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Network interfaces
            net_io = psutil.net_io_counters(pernic=True)
            network_stats = {}
            current_time = time.time()
            
            for interface, stats in net_io.items():
                if interface in self.network_baseline:
                    time_diff = current_time - self.network_baseline[interface]['timestamp']
                    bytes_sent_rate = (stats.bytes_sent - self.network_baseline[interface]['bytes_sent']) / time_diff if time_diff > 0 else 0
                    bytes_recv_rate = (stats.bytes_recv - self.network_baseline[interface]['bytes_recv']) / time_diff if time_diff > 0 else 0
                    
                    network_stats[interface] = {
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv,
                        'bytes_sent_rate': round(bytes_sent_rate, 2),
                        'bytes_recv_rate': round(bytes_recv_rate, 2),
                        'packets_sent': stats.packets_sent,
                        'packets_recv': stats.packets_recv,
                        'errors_in': stats.errin,
                        'errors_out': stats.errout,
                        'drops_in': stats.dropin,
                        'drops_out': stats.dropout
                    }
                    
                    # Update baseline
                    self.network_baseline[interface] = {
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv,
                        'timestamp': current_time
                    }
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            uptime_seconds = time.time() - psutil.boot_time()
            
            return {
                'cpu': {
                    'percent_overall': round(sum(cpu_percent) / len(cpu_percent), 2),
                    'percent_per_core': [round(p, 2) for p in cpu_percent],
                    'count': psutil.cpu_count(),
                    'frequency_mhz': round(cpu_freq.current, 2) if cpu_freq else None,
                    'load_avg': {
                        '1min': round(load_avg[0], 2),
                        '5min': round(load_avg[1], 2),
                        '15min': round(load_avg[2], 2)
                    }
                },
                'memory': {
                    'total_gb': round(memory.total / 1024**3, 2),
                    'used_gb': round(memory.used / 1024**3, 2),
                    'available_gb': round(memory.available / 1024**3, 2),
                    'percent': memory.percent,
                    'buffers_gb': round(memory.buffers / 1024**3, 2),
                    'cached_gb': round(memory.cached / 1024**3, 2)
                },
                'swap': {
                    'total_gb': round(swap.total / 1024**3, 2),
                    'used_gb': round(swap.used / 1024**3, 2),
                    'percent': swap.percent
                },
                'disk': {
                    'partitions': disk_usage,
                    'io': {
                        'read_bytes': disk_io.read_bytes if disk_io else 0,
                        'write_bytes': disk_io.write_bytes if disk_io else 0,
                        'read_count': disk_io.read_count if disk_io else 0,
                        'write_count': disk_io.write_count if disk_io else 0
                    }
                },
                'network': {
                    'interfaces': network_stats,
                    'connections_count': connections
                },
                'system': {
                    'boot_time': boot_time,
                    'uptime_hours': round(uptime_seconds / 3600, 2),
                    'hostname': socket.gethostname(),
                    'users_count': len(psutil.users())
                }
            }
            
        except Exception as e:
            self.log_error(f"Error collecting system metrics: {e}")
            return None
    
    def get_process_metrics(self):
        """Get detailed process information"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                           'memory_percent', 'status', 'create_time', 
                                           'cmdline', 'num_threads', 'memory_info']):
                try:
                    pinfo = proc.info
                    pinfo['memory_rss_mb'] = round(pinfo['memory_info'].rss / 1024**2, 2) if pinfo['memory_info'] else 0
                    pinfo['memory_vms_mb'] = round(pinfo['memory_info'].vms / 1024**2, 2) if pinfo['memory_info'] else 0
                    pinfo['create_time'] = datetime.fromtimestamp(pinfo['create_time']).isoformat() if pinfo['create_time'] else None
                    del pinfo['memory_info']  # Remove raw memory_info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and get top processes
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:15]
            top_memory = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:15]
            
            return {
                'total_processes': len(processes),
                'top_cpu_processes': top_cpu,
                'top_memory_processes': top_memory,
                'process_status_counts': self.get_process_status_counts(processes)
            }
            
        except Exception as e:
            self.log_error(f"Error collecting process metrics: {e}")
            return None
    
    def get_process_status_counts(self, processes):
        """Count processes by status"""
        status_counts = defaultdict(int)
        for proc in processes:
            status_counts[proc['status']] += 1
        return dict(status_counts)
    
    def get_system_logs(self):
        """Parse system log files"""
        logs = {}
        
        # System log files to monitor
        log_files = {
            'syslog': '/var/log/syslog',
            'auth': '/var/log/auth.log',
            'kern': '/var/log/kern.log',
            'daemon': '/var/log/daemon.log',
            'mail': '/var/log/mail.log',
            'cron': '/var/log/cron.log'
        }
        
        for log_type, log_path in log_files.items():
            try:
                if os.path.exists(log_path):
                    logs[log_type] = self.tail_log_file(log_path, lines=50)
            except Exception as e:
                logs[log_type] = f"Error reading {log_path}: {e}"
        
        return logs
    
    def get_application_logs(self):
        """Parse application-specific logs"""
        app_logs = {}
        
        # Common application log patterns
        app_log_patterns = {
            'nginx': ['/var/log/nginx/*.log', '/var/log/nginx/*/*.log'],
            'apache': ['/var/log/apache2/*.log', '/var/log/httpd/*.log'],
            'mysql': ['/var/log/mysql/*.log', '/var/log/mysqld.log'],
            'postgresql': ['/var/log/postgresql/*.log'],
            'redis': ['/var/log/redis/*.log'],
            'docker': ['/var/log/docker.log', '/var/lib/docker/containers/*/*.log'],
            'systemd': ['/var/log/systemd/*.log']
        }
        
        for app_name, patterns in app_log_patterns.items():
            app_logs[app_name] = []
            for pattern in patterns:
                for log_file in glob.glob(pattern):
                    try:
                        if os.path.exists(log_file) and os.access(log_file, os.R_OK):
                            recent_logs = self.tail_log_file(log_file, lines=20)
                            if recent_logs:
                                app_logs[app_name].append({
                                    'file': log_file,
                                    'logs': recent_logs
                                })
                    except Exception as e:
                        app_logs[app_name].append({
                            'file': log_file,
                            'error': str(e)
                        })
        
        return app_logs
    
    # def tail_log_file(self, file_path, lines=50):
    #     """Get last N lines from a log file"""
    #     try:
    #         with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    #             return deque(f, maxlen=lines)
    #     except Exception:
    #         return []
    def tail_log_file(self, file_path, lines=50):
        """Get last N lines from a log file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return list(deque(f, maxlen=lines))  # Convert deque to list
        except Exception:
            return []
    
    def get_security_events(self):
        """Extract security-related events"""
        security_events = []
        
        try:
            # Parse auth.log for security events
            auth_log = '/var/log/auth.log'
            if os.path.exists(auth_log):
                recent_auth = self.tail_log_file(auth_log, lines=100)
                
                # Look for security patterns
                security_patterns = [
                    r'Failed password',
                    r'Invalid user',
                    r'authentication failure',
                    r'sudo:.*COMMAND',
                    r'session opened',
                    r'session closed',
                    r'su:.*'
                ]
                
                for line in recent_auth:
                    for pattern in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            security_events.append({
                                'timestamp': self.extract_timestamp_from_log(line),
                                'event': line.strip(),
                                'type': pattern.replace(r'.*', '').replace(r'\w+', '').strip()
                            })
                            break
        
        except Exception as e:
            security_events.append({'error': f"Error parsing security events: {e}"})
        
        return security_events[-20:]  # Return last 20 events
    
    def extract_timestamp_from_log(self, log_line):
        """Extract timestamp from log line"""
        try:
            # Try to extract timestamp from common log formats
            timestamp_patterns = [
                r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',  # Nov 15 10:30:45
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # 2023-11-15T10:30:45
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'  # 2023-11-15 10:30:45
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, log_line)
                if match:
                    return match.group(1)
            
            return self.get_ist_timestamp()
        except Exception:
            return self.get_ist_timestamp()
    
    def get_docker_info(self):
        """Get Docker container information if available"""
        docker_info = {}
        
        try:
            # Check if Docker is installed and running
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            containers.append(container)
                        except json.JSONDecodeError:
                            continue
                
                docker_info['containers'] = containers
                docker_info['container_count'] = len(containers)
                
                # Get Docker system info
                system_result = subprocess.run(['docker', 'system', 'df', '--format', 'json'], 
                                             capture_output=True, text=True, timeout=10)
                if system_result.returncode == 0:
                    docker_info['system_usage'] = system_result.stdout.strip()
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            docker_info['status'] = 'Docker not available or not running'
        
        return docker_info
    
    def check_alerts(self, metrics):
        """Check for alert conditions"""
        alerts = []
        
        try:
            # Memory alert
            if metrics['memory']['percent'] > self.memory_threshold:
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'WARNING',
                    'value': metrics['memory']['percent'],
                    'threshold': self.memory_threshold,
                    'message': f"Memory usage at {metrics['memory']['percent']}% exceeds threshold"
                })
            
            # CPU alert
            if metrics['cpu']['percent_overall'] > self.cpu_threshold:
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'WARNING',
                    'value': metrics['cpu']['percent_overall'],
                    'threshold': self.cpu_threshold,
                    'message': f"CPU usage at {metrics['cpu']['percent_overall']}% exceeds threshold"
                })
            
            # Load average alert
            if metrics['cpu']['load_avg']['1min'] > self.load_threshold:
                alerts.append({
                    'type': 'high_load_average',
                    'severity': 'WARNING',
                    'value': metrics['cpu']['load_avg']['1min'],
                    'threshold': self.load_threshold,
                    'message': f"Load average at {metrics['cpu']['load_avg']['1min']} exceeds threshold"
                })
            
            # Disk usage alerts
            for mount, disk_info in metrics['disk']['partitions'].items():
                if disk_info['percent'] > self.disk_threshold:
                    alerts.append({
                        'type': 'high_disk_usage',
                        'severity': 'CRITICAL',
                        'mount': mount,
                        'value': disk_info['percent'],
                        'threshold': self.disk_threshold,
                        'message': f"Disk usage at {mount} is {disk_info['percent']}%"
                    })
            
        except Exception as e:
            alerts.append({
                'type': 'monitoring_error',
                'severity': 'ERROR',
                'message': f"Error checking alerts: {e}"
            })
        
        return alerts
    
    def log_error(self, message):
        """Log error messages"""
        error_log = {
            'timestamp': self.get_ist_timestamp(),
            'level': 'ERROR',
            'service': 'ec2-enhanced-monitor',
            'message': message
        }
        self.logger.error(json.dumps(error_log))
    
    def collect_comprehensive_metrics(self):
        """Collect all metrics and logs"""
        try:
            # System metrics
            system_metrics = self.get_system_metrics()
            if not system_metrics:
                return None
            
            # Process metrics
            process_metrics = self.get_process_metrics()
            
            # System logs
            system_logs = self.get_system_logs()
            
            # Application logs
            app_logs = self.get_application_logs()
            
            # Security events
            security_events = self.get_security_events()
            
            # Docker info
            docker_info = self.get_docker_info()
            
            # Check for alerts
            alerts = self.check_alerts(system_metrics)
            
            # Build comprehensive metrics object
            comprehensive_metrics = {
                'timestamp': self.get_ist_timestamp(),
                'level': 'INFO',
                'service': 'ec2-enhanced-monitor',
                'system_metrics': system_metrics,
                'process_metrics': process_metrics,
                'system_logs': system_logs,
                'application_logs': app_logs,
                'security_events': security_events,
                'docker_info': docker_info,
                'alerts': alerts
            }
            
            # Log alerts separately if they exist
            if alerts:
                alert_log = {
                    'timestamp': self.get_ist_timestamp(),
                    'level': 'WARNING',
                    'service': 'ec2-enhanced-monitor',
                    'alerts': alerts,
                    'system_snapshot': {
                        'cpu_percent': system_metrics['cpu']['percent_overall'],
                        'memory_percent': system_metrics['memory']['percent'],
                        'load_avg': system_metrics['cpu']['load_avg']['1min']
                    }
                }
                self.logger.warning(json.dumps(alert_log))
            
            return comprehensive_metrics
            
        except Exception as e:
            self.log_error(f"Failed to collect comprehensive metrics: {e}")
            return None
    
    def cleanup_old_logs(self):
        """Remove logs older than 2 hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=2)
            log_pattern = os.path.join(self.log_dir, "ec2_comprehensive.log*")
            
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
        print(f"Starting Enhanced EC2 Monitor - logging to {self.log_dir}")
        print(f"Collection interval: {self.interval} seconds")
        print("Monitoring: System metrics, Process info, System logs, App logs, Security events, Docker")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                metrics = self.collect_comprehensive_metrics()
                if metrics:
                    self.logger.info(json.dumps(metrics))
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\nStopping Enhanced EC2 Monitor...")
        except Exception as e:
            print(f"Monitor error: {e}")
            self.log_error(f"Monitor crashed: {e}")

if __name__ == "__main__":
    monitor = EnhancedEC2Monitor()
    monitor.run()
