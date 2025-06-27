"""
n8n HTTP Endpoint for Reading System Logs
This script can be used as a webhook endpoint in n8n to fetch filtered logs
"""

from flask import Flask, request, jsonify
import json
import os
import datetime
from pathlib import Path
import glob

app = Flask(__name__)

LOG_DIR = "/var/log/monitoring"

def get_available_log_files():
    """Get list of available log files"""
    log_dir = Path(LOG_DIR)
    files = []
    
    for file_path in log_dir.glob("system_logs_*.json"):
        stat = file_path.stat()
        files.append({
            'filename': file_path.name,
            'timestamp': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'size': stat.st_size
        })
    
    # Sort by timestamp (newest first)
    files.sort(key=lambda x: x['timestamp'], reverse=True)
    return files

def load_log_file(filename):
    """Load a specific log file"""
    file_path = Path(LOG_DIR) / filename
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {'error': f'Failed to load file: {str(e)}'}

def filter_logs_by_alert_context(logs_data, alert_time, time_window_minutes=30):
    """Filter logs based on alert timestamp and context"""
    alert_timestamp = datetime.datetime.fromisoformat(alert_time.replace('Z', '+00:00'))
    start_time = alert_timestamp - datetime.timedelta(minutes=time_window_minutes)
    end_time = alert_timestamp + datetime.timedelta(minutes=time_window_minutes//2)
    
    filtered_data = {
        'alert_context': {
            'alert_time': alert_time,
            'filter_window': f"{time_window_minutes} minutes",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        },
        'system_metrics': logs_data.get('system_metrics', {}),
        'top_processes': logs_data.get('top_processes', []),
        'relevant_logs': {}
    }
    
    # Filter logs within the time window
    for log_type, log_entries in logs_data.get('logs', {}).items():
        relevant_entries = []
        
        if isinstance(log_entries, list):
            for entry in log_entries:
                # For structured logs with timestamps
                if isinstance(entry, dict) and 'timestamp' in entry:
                    try:
                        entry_time = datetime.datetime.fromisoformat(entry['timestamp'])
                        if start_time <= entry_time <= end_time:
                            relevant_entries.append(entry)
                    except (ValueError, TypeError):
                        continue
                # For text logs, include error/warning lines
                elif isinstance(entry, str):
                    if any(keyword in entry.lower() for keyword in ['error', 'critical', 'warning', 'fail', 'exception']):
                        relevant_entries.append(entry)
        
        if relevant_entries:
            filtered_data['relevant_logs'][log_type] = relevant_entries
    
    return filtered_data

@app.route('/logs/latest', methods=['GET'])
def get_latest_logs():
    """Get the latest collected logs"""
    try:
        latest_file = Path(LOG_DIR) / "latest.json"
        if latest_file.exists():
            with open(latest_file, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'No latest logs available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs/alert-context', methods=['POST'])
def get_alert_context_logs():
    """Get logs filtered by alert context - designed for n8n webhook"""
    try:
        request_data = request.get_json()
        
        # Expected input from n8n/Prometheus alert
        alert_time = request_data.get('alert_time')  # ISO format timestamp
        time_window = request_data.get('time_window_minutes', 30)
        
        if not alert_time:
            return jsonify({'error': 'alert_time is required'}), 400
        
        # Load latest logs
        latest_data = load_log_file('latest.json')
        if latest_data is None:
            return jsonify({'error': 'No log data available'}), 404
        
        # Filter logs based on alert context
        filtered_logs = filter_logs_by_alert_context(latest_data, alert_time, time_window)
        
        return jsonify(filtered_logs)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
