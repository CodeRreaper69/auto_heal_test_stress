import os
import json
import logging
import subprocess
import datetime
import psutil
import glob
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class SystemLogCollector:
    def __init__(self, output_dir: str = "/var/log/monitoring", retention_hours: int = 24):
        self.output_dir = Path(output_dir)
        self.retention_hours = retention_hours
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'collector.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_system_metrics(self) -> Dict:
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get load average (Linux/Unix)
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]  # Windows fallback
            
            return {
                'timestamp': datetime.datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'load_average': {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}

    def get_process_info(self, limit: int = 10) -> List[Dict]:
        """Get top processes by CPU and memory usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return processes[:limit]
        except Exception as e:
            self.logger.error(f"Error collecting process info: {e}")
            return []

    def collect_system_logs(self, lines: int = 1000) -> Dict[str, List[str]]:
        """Collect recent system logs from various sources"""
        logs = {}
        
        # Common log files to monitor
        log_files = {
            'syslog': ['/var/log/syslog', '/var/log/messages'],
            'auth': ['/var/log/auth.log', '/var/log/secure'],
            'kernel': ['/var/log/kern.log', '/var/log/dmesg'],
            'apache': ['/var/log/apache2/error.log', '/var/log/httpd/error_log'],
            'nginx': ['/var/log/nginx/error.log'],
            'mysql': ['/var/log/mysql/error.log', '/var/log/mysqld.log'],
            'application': ['/var/log/cpu_stress.log']  # Your custom app logs
        }
        
        for log_type, file_paths in log_files.items():
            for file_path in file_paths:
                if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                    try:
                        # Use tail to get recent lines
                        result = subprocess.run(
                            ['tail', '-n', str(lines), file_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            logs[f"{log_type}_{os.path.basename(file_path)}"] = result.stdout.strip().split('\n')
                            break  # Use first available file for this type
                    except Exception as e:
                        self.logger.warning(f"Could not read {file_path}: {e}")
        
        return logs

    def collect_journalctl_logs(self, since: str = "1 hour ago", lines: int = 1000) -> Dict[str, List[str]]:
        """Collect systemd journal logs"""
        logs = {}
        
        try:
            # Get general system logs
            result = subprocess.run([
                'journalctl', '--since', since, '-n', str(lines), '--no-pager', '-o', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                journal_entries = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            entry = json.loads(line)
                            journal_entries.append({
                                'timestamp': entry.get('__REALTIME_TIMESTAMP'),
                                'unit': entry.get('_SYSTEMD_UNIT', 'unknown'),
                                'message': entry.get('MESSAGE', ''),
                                'priority': entry.get('PRIORITY', '6')
                            })
                        except json.JSONDecodeError:
                            continue
                
                logs['systemd_journal'] = journal_entries
                
        except subprocess.TimeoutExpired:
            self.logger.warning("journalctl command timed out")
        except FileNotFoundError:
            self.logger.info("journalctl not available (not a systemd system)")
        except Exception as e:
            self.logger.error(f"Error collecting journal logs: {e}")
        
        return logs

    def filter_logs_by_time(self, logs: Dict, start_time: datetime.datetime, end_time: datetime.datetime) -> Dict:
        """Filter logs by time range"""
        filtered_logs = {}
        
        for log_type, log_entries in logs.items():
            filtered_entries = []
            
            if isinstance(log_entries, list) and log_entries:
                for entry in log_entries:
                    if isinstance(entry, dict) and 'timestamp' in entry:
                        # Handle structured logs
                        try:
                            entry_time = datetime.datetime.fromisoformat(entry['timestamp'])
                            if start_time <= entry_time <= end_time:
                                filtered_entries.append(entry)
                        except (ValueError, TypeError):
                            continue
                    elif isinstance(entry, str):
                        # Handle text logs - try to extract timestamp
                        # This is basic - you might want to improve timestamp parsing
                        # based on your specific log formats
                        if any(keyword in entry.lower() for keyword in ['error', 'critical', 'warning', 'fail']):
                            filtered_entries.append(entry)
            
            if filtered_entries:
                filtered_logs[log_type] = filtered_entries
        
        return filtered_logs

    def save_logs_to_json(self, data: Dict, filename: str):
        """Save collected data to JSON file"""
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Saved logs to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving logs to {filepath}: {e}")

    def cleanup_old_files(self):
        """Remove old log files based on retention policy"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=self.retention_hours)
        
        for file_path in self.output_dir.glob("*.json"):
            try:
                file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    self.logger.info(f"Deleted old file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error deleting {file_path}: {e}")

    def collect_all_logs(self, time_filter_minutes: Optional[int] = None):
        """Main method to collect all logs and metrics"""
        timestamp = datetime.datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        self.logger.info("Starting log collection")
        
        # Collect system metrics
        metrics = self.get_system_metrics()
        
        # Collect process information
        processes = self.get_process_info()
        
        # Collect system logs
        system_logs = self.collect_system_logs()
        
        # Collect journal logs
        journal_logs = self.collect_journalctl_logs()
        
        # Combine all logs
        all_logs = {**system_logs, **journal_logs}
        
        # Apply time filter if specified
        if time_filter_minutes:
            start_time = timestamp - datetime.timedelta(minutes=time_filter_minutes)
            all_logs = self.filter_logs_by_time(all_logs, start_time, timestamp)
        
        # Prepare final data structure
        collected_data = {
            'collection_timestamp': timestamp.isoformat(),
            'system_metrics': metrics,
            'top_processes': processes,
            'logs': all_logs,
            'metadata': {
                'collector_version': '1.0',
                'hostname': os.uname().nodename,
                'time_filter_minutes': time_filter_minutes
            }
        }
        
        # Save to JSON file
        filename = f"system_logs_{timestamp_str}.json"
        self.save_logs_to_json(collected_data, filename)
        
        # Also save as latest.json for easy access
        self.save_logs_to_json(collected_data, "latest.json")
        
        # Cleanup old files
        self.cleanup_old_files()
        
        self.logger.info(f"Log collection completed. File: {filename}")
        return collected_data

def main():
    parser = argparse.ArgumentParser(description='System Log Collector for n8n Monitoring')
    parser.add_argument('--output-dir', default='/var/log/monitoring', 
                       help='Directory to save collected logs')
    parser.add_argument('--retention-hours', type=int, default=24,
                       help='Hours to retain log files')
    parser.add_argument('--time-filter', type=int, 
                       help='Filter logs to last N minutes')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously (for daemon mode)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Collection interval in seconds (for continuous mode)')
    
    args = parser.parse_args()
    
    collector = SystemLogCollector(args.output_dir, args.retention_hours)
    
    if args.continuous:
        import time
        logging.info(f"Starting continuous collection every {args.interval} seconds")
        try:
            while True:
                collector.collect_all_logs(args.time_filter)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Stopped by user")
    else:
        collector.collect_all_logs(args.time_filter)

if __name__ == "__main__":
    main()
