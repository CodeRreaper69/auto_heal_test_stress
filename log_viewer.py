#!/usr/bin/env python3
"""
Htop-style viewer for collected system logs
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

def format_bytes(bytes_value):
    """Format bytes in human readable format"""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}PB"

def format_time(seconds):
    """Format seconds into human readable time"""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def display_system_overview(data):
    """Display system overview similar to htop header"""
    overview = data.get('system_overview', {})
    cpu_data = overview.get('cpu', {})
    memory_data = overview.get('memory', {})
    
    print("=" * 80)
    print(f"System Overview - {data.get('collection_timestamp', 'Unknown time')}")
    print("=" * 80)
    
    # System info
    metadata = data.get('metadata', {})
    print(f"Hostname: {metadata.get('hostname', 'Unknown')}")
    print(f"Uptime: {overview.get('uptime_formatted', 'Unknown')}")
    print(f"Kernel: {metadata.get('kernel', 'Unknown')} ({metadata.get('architecture', 'Unknown')})")
    print()
    
    # CPU info
    print("CPU Information:")
    print(f"  Cores: {cpu_data.get('count_physical', 'N/A')} physical, {cpu_data.get('count_logical', 'N/A')} logical")
    print(f"  Usage: {cpu_data.get('percent_total', 0):.1f}%")
    
    load_avg = cpu_data.get('load_average', {})
    print(f"  Load Average: {load_avg.get('1min', 0):.2f}, {load_avg.get('5min', 0):.2f}, {load_avg.get('15min', 0):.2f}")
    print()
    
    # Memory info
    print("Memory Information:")
    total_mem = memory_data.get('total', 0)
    used_mem = memory_data.get('used', 0)
    free_mem = memory_data.get('free', 0)
    print(f"  Total: {format_bytes(total_mem)}")
    print(f"  Used:  {format_bytes(used_mem)} ({memory_data.get('percent', 0):.1f}%)")
    print(f"  Free:  {format_bytes(free_mem)}")
    print()

def display_process_table(data, limit=20):
    """Display process table similar to htop"""
    processes = data.get('detailed_processes', [])[:limit]
    
    if not processes:
        print("No process data available")
        return
    
    print("Process Table (Top {} by CPU usage):".format(len(processes)))
    print("-" * 120)
    
    # Header
    header = f"{'PID':>6} {'USER':>10} {'CPU%':>6} {'MEM%':>6} {'MEMORY':>8} {'TIME':>8} {'COMMAND':<50}"
    print(header)
    print("-" * 120)
    
    # Process rows
    for proc in processes:
        pid = proc.get('pid', 0)
        user = proc.get('username', 'unknown')[:10]
        cpu_pct = proc.get('cpu_percent', 0)
        mem_pct = proc.get('memory_percent', 0)
        mem_rss = proc.get('memory_rss', 0)
        
        # Calculate runtime from CPU times
        cpu_user = proc.get('cpu_times_user', 0)
        cpu_system = proc.get('cpu_times_system', 0)
        total_cpu_time = cpu_user + cpu_system
        
        command = proc.get('cmdline', proc.get('name', 'unknown'))
        if len(command) > 50:
            command = command[:47] + "..."
        
        row = f"{pid:>6} {user:>10} {cpu_pct:>5.1f} {mem_pct:>5.1f} {format_bytes(mem_rss):>8} {format_time(total_cpu_time):>8} {command:<50}"
        print(row)

def display_services(data, limit=10):
    """Display running services"""
    services = data.get('running_services', [])
    
    if not services:
        return
    
    print(f"\nRunning Services (showing {min(limit, len(services))}):")
    print("-" * 80)
    
    for service in services[:limit]:
        status = service.get('active', 'unknown')
        name = service.get('unit', 'unknown')
        desc = service.get('description', '')[:40]
        
        status_color = "●" if status == "active" else "○"
        print(f"{status_color} {name:30} {status:10} {desc}")

def display_network_connections(data, limit=10):
    """Display network connections"""
    connections = data.get('network_connections', [])
    
    if not connections:
        return
    
    print(f"\nNetwork Connections (showing {min(limit, len(connections))}):")
    print("-" * 100)
    print(f"{'TYPE':>6} {'LOCAL':>20} {'REMOTE':>20} {'STATUS':>12} {'PID':>6} {'PROCESS':<20}")
    print("-" * 100)
    
    for conn in connections[:limit]:
        conn_type = conn.get('type', 'unknown')
        local = conn.get('local_address', 'N/A')[:20]
        remote = conn.get('remote_address', 'N/A')[:20]
        status = conn.get('status', 'unknown')
        pid = conn.get('pid', 0) or 0
        process = conn.get('process_name', 'unknown')[:20]
        
        print(f"{conn_type:>6} {local:>20} {remote:>20} {status:>12} {pid:>6} {process:<20}")

def main():
    parser = argparse.ArgumentParser(description='View system logs in htop-style format')
    parser.add_argument('--log-dir', default='/var/log/monitoring',
                       help='Directory containing log files')
    parser.add_argument('--file', help='Specific log file to view')
    parser.add_argument('--processes', type=int, default=20,
                       help='Number of processes to show')
    parser.add_argument('--services', type=int, default=10,
                       help='Number of services to show')
    parser.add_argument('--connections', type=int, default=10,
                       help='Number of network connections to show')
    parser.add_argument('--list-files', action='store_true',
                       help='List available log files')
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    
    if args.list_files:
        print("Available log files:")
        for pattern in ["enhanced_system_*.json", "system_logs_*.json", "latest*.json"]:
            for file_path in sorted(log_dir.glob(pattern)):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                size = file_path.stat().st_size
                print(f"  {file_path.name:40} {mtime.strftime('%Y-%m-%d %H:%M:%S'):20} {format_bytes(size):>8}")
        return
    
    # Determine which file to read
    if args.file:
        log_file = log_dir / args.file
    else:
        # Try to find the latest enhanced log, then fall back to regular latest
        log_file = log_dir / "latest_enhanced.json"
        if not log_file.exists():
            log_file = log_dir / "latest.json"
    
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        print("Available files:")
        for f in log_dir.glob("*.json"):
            print(f"  {f.name}")
        sys.exit(1)
    
    # Load and display data
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        # Clear screen (optional)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Display sections
        display_system_overview(data)
        display_process_table(data, args.processes)
        display_services(data, args.services)
        display_network_connections(data, args.connections)
        
        print(f"\nData from: {log_file}")
        
    except Exception as e:
        print(f"Error reading log file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
