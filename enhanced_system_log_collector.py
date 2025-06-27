#!/usr/bin/env python3
"""
Enhanced System Log Collector with detailed command information
Similar to htop but logged to JSON for monitoring
"""

import os
import json
import logging
import subprocess
import datetime
import psutil
import pwd
import grp
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class EnhancedSystemLogCollector:
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

    def get_detailed_process_info(self, limit: int = 50) -> List[Dict]:
        """Get detailed process information similar to htop"""
        try:
            processes = []
            
            for proc in psutil.process_iter([
                'pid', 'ppid', 'name', 'exe', 'cmdline', 'username', 
                'cpu_percent', 'memory_percent', 'memory_info', 'status',
                'create_time', 'num_threads', 'cpu_times', 'nice'
            ]):
                try:
                    pinfo = proc.info
                    
                    # Get additional details
                    process_data = {
                        'pid': pinfo['pid'],
                        'ppid': pinfo['ppid'],
                        'name': pinfo['name'],
                        'exe': pinfo['exe'],
                        'cmdline': ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else pinfo['name'],
                        'username': pinfo['username'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent'],
                        'memory_rss': pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        'memory_vms': pinfo['memory_info'].vms if pinfo['memory_info'] else 0,
                        'status': pinfo['status'],
                        'num_threads': pinfo['num_threads'],
                        'nice': pinfo['nice'],
                        'create_time': datetime.datetime.fromtimestamp(pinfo['create_time']).isoformat(),
                        'cpu_times_user': pinfo['cpu_times'].user if pinfo['cpu_times'] else 0,
                        'cpu_times_system': pinfo['cpu_times'].system if pinfo['cpu_times'] else 0,
                    }
                    
                    # Try to get additional process details
                    try:
                        proc_obj = psutil.Process(pinfo['pid'])
                        process_data.update({
                            'cwd': proc_obj.cwd(),
                            'num_fds': proc_obj.num_fds() if hasattr(proc_obj, 'num_fds') else None,
                            'connections': len(proc_obj.connections()),
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                    
                    processes.append(process_data)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage (like htop default)
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Error collecting detailed process info: {e}")
            return []

    def get_system_overview(self) -> Dict:
        """Get system overview similar to htop header"""
        try:
            # CPU information
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Load average
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network information
            net_io = psutil.net_io_counters()
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = datetime.datetime.now().timestamp() - boot_time
            
            return {
                'timestamp': datetime.datetime.now().isoformat(),
                'uptime_seconds': uptime,
                'uptime_formatted': str(datetime.timedelta(seconds=int(uptime))),
                'boot_time': datetime.datetime.fromtimestamp(boot_time).isoformat(),
                'cpu': {
                    'count_physical': cpu_count,
                    'count_logical': cpu_count_logical,
                    'frequency_current': cpu_freq.current if cpu_freq else None,
                    'frequency_min': cpu_freq.min if cpu_freq else None,
                    'frequency_max': cpu_freq.max if cpu_freq else None,
                    'percent_total': sum(cpu_percent_per_core) / len(cpu_percent_per_core),
                    'percent_per_core': cpu_percent_per_core,
                    'load_average': {
                        '1min': load_avg[0],
                        '5min': load_avg[1],
                        '15min': load_avg[2]
                    }
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free,
                    'active': memory.active,
                    'inactive': memory.inactive,
                    'buffers': memory.buffers,
                    'cached': memory.cached,
                    'shared': memory.shared,
                    'slab': memory.slab if hasattr(memory, 'slab') else None
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                    'sin': swap.sin,
                    'sout': swap.sout
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100,
                    'io_read_count': disk_io.read_count if disk_io else None,
                    'io_write_count': disk_io.write_count if disk_io else None,
                    'io_read_bytes': disk_io.read_bytes if disk_io else None,
                    'io_write_bytes': disk_io.write_bytes if disk_io else None
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent if net_io else None,
                    'bytes_recv': net_io.bytes_recv if net_io else None,
                    'packets_sent': net_io.packets_sent if net_io else None,
                    'packets_recv': net_io.packets_recv if net_io else None,
                    'errin': net_io.errin if net_io else None,
                    'errout': net_io.errout if net_io else None,
                    'dropin': net_io.dropin if net_io else None,
                    'dropout': net_io.dropout if net_io else None
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system overview: {e}")
            return {}

    def get_running_services(self) -> List[Dict]:
        """Get systemd services status"""
        services = []
        try:
            result = subprocess.run([
                'systemctl', 'list-units', '--type=service', '--no-pager', '--no-legend'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                'unit': parts[0],
                                'load': parts[1],
                                'active': parts[2],
                                'sub': parts[3],
                                'description': ' '.join(parts[4:]) if len(parts) > 4 else ''
                            })
        except Exception as e:
            self.logger.warning(f"Could not get services: {e}")
        
        return services

    def get_network_connections(self) -> List[Dict]:
        """Get active network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                conn_info = {
                    'fd': conn.fd,
                    'family': conn.family.name if conn.family else None,
                    'type': conn.type.name if conn.type else None,
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                }
                
                # Try to get process name for the connection
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        conn_info['process_name'] = proc.name()
                        conn_info['process_cmdline'] = ' '.join(proc.cmdline())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                connections.append(conn_info)
        except Exception as e:
            self.logger.warning(f"Could not get network connections: {e}")
        
        return connections

    def get_htop_style_summary(self) -> Dict:
        """Generate htop-style summary with command details"""
        data = {
            'collection_timestamp': datetime.datetime.now().isoformat(),
            'system_overview': self.get_system_overview(),
            'detailed_processes': self.get_detailed_process_info(50),  # Top 50 processes
            'running_services': self.get_running_services(),
            'network_connections': self.get_network_connections(),
            'process_summary': {
                'total_processes': len(list(psutil.process_iter())),
                'running': len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_RUNNING]),
                'sleeping': len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_SLEEPING]),
                'zombie': len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_ZOMBIE])
            },
            'metadata': {
                'hostname': os.uname().nodename,
                'kernel': os.uname().release,
                'architecture': os.uname().machine,
                'collector_version': '2.0-enhanced'
            }
        }
        
        return data

    def save_to_json(self, data: Dict, filename: str):
        """Save data to JSON file"""
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Saved enhanced logs to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving to {filepath}: {e}")

    def collect_enhanced_logs(self):
        """Main collection method"""
        timestamp = datetime.datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        self.logger.info("Starting enhanced log collection (htop-style)")
        
        # Collect all data
        data = self.get_htop_style_summary()
        
        # Save with timestamp
        filename = f"enhanced_system_{timestamp_str}.json"
        self.save_to_json(data, filename)
        
        # Save as latest
        self.save_to_json(data, "latest_enhanced.json")
        
        # Cleanup old files
        self.cleanup_old_files()
        
        self.logger.info(f"Enhanced collection completed: {filename}")
        return data

    def cleanup_old_files(self):
        """Remove old files"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=self.retention_hours)
        
        for pattern in ["enhanced_system_*.json", "system_logs_*.json"]:
            for file_path in self.output_dir.glob(pattern):
                try:
                    file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        self.logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error deleting {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced System Log Collector (htop-style)')
    parser.add_argument('--output-dir', default='/var/log/monitoring', 
                       help='Directory to save logs')
    parser.add_argument('--retention-hours', type=int, default=24,
                       help='Hours to retain files')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously')
    parser.add_argument('--interval', type=int, default=300,
                       help='Collection interval in seconds')
    
    args = parser.parse_args()
    
    collector = EnhancedSystemLogCollector(args.output_dir, args.retention_hours)
    
    if args.continuous:
        import time
        print(f"Starting continuous enhanced collection every {args.interval} seconds")
        try:
            while True:
                collector.collect_enhanced_logs()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopped by user")
    else:
        collector.collect_enhanced_logs()

if __name__ == "__main__":
    main()
