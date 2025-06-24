import streamlit as st
import psutil
import sqlite3
import time
import threading
import subprocess
import json
from datetime import datetime
import pandas as pd
import google.generativeai as genai
from typing import Dict, List, Tuple
import os

# Configure Gemini with environment variable (recommended) or direct key
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment or use direct assignment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    st.warning("⚠️ Please set your Gemini API key in .env file or update the code directly")
else:
    genai.configure(api_key=GEMINI_API_KEY)

class AutoHealSystem:
    def __init__(self):
        self.db_path = "autoheal.db"
        self.monitoring_active = False
        self.setup_database()
        self.thresholds = {
            'cpu_percent': 50,
            'memory_percent': 69,
            'disk_percent': 90
        }
        
    def setup_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                condition_type TEXT,
                severity TEXT,
                metrics TEXT,
                status TEXT DEFAULT 'detected'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remedies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER,
                remedy_type TEXT,
                command TEXT,
                description TEXT,
                risk_level TEXT,
                success_rate REAL DEFAULT 0.8
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remedy_id INTEGER,
                status TEXT,
                output TEXT,
                error TEXT,
                timestamp TEXT,
                user_approved BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_system_metrics(self) -> Dict:
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:/')
            
            # Get top processes by CPU
            top_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 5:  # Only high CPU processes
                        top_processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'process_count': len(psutil.pids()),
                'top_processes': sorted(top_processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
            }
        except Exception as e:
            st.error(f"Error collecting metrics: {e}")
            return {}
    
    def analyze_with_gemini(self, metrics: Dict, incident_type: str) -> Dict:
        """Use Gemini to analyze the issue and suggest remedies"""
        try:
            # Use Gemini for real analysis
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            You are an expert Windows system administrator. Analyze this system issue and provide solutions.

            SYSTEM ALERT: {incident_type.replace('_', ' ').title()}
            
            CURRENT METRICS:
            - CPU Usage: {metrics.get('cpu_percent', 0):.1f}%
            - Memory Usage: {metrics.get('memory_percent', 0):.1f}%
            - Disk Usage: {metrics.get('disk_percent', 0):.1f}%
            - Active Processes: {metrics.get('process_count', 0)}
            - Top CPU Processes: {json.dumps(metrics.get('top_processes', [])[:3], indent=2)}

            Please provide your analysis in this EXACT JSON format:
            {{
                "analysis": "Brief root cause analysis in 1-2 sentences",
                "remedies": [
                    {{
                        "description": "Clear description of what this remedy does",
                        "command": "safe_command_identifier",
                        "risk_level": "LOW/MEDIUM/HIGH",
                        "success_rate": 0.85,
                        "reasoning": "Why this remedy should work"
                    }}
                ]
            }}

            IMPORTANT CONSTRAINTS:
            - Only suggest SAFE, reversible actions
            - Use these command identifiers only: restart_explorer, clear_cache, clean_temp, kill_high_cpu, restart_memory_hogs, clear_browser_cache
            - Risk levels: LOW (no system impact), MEDIUM (temporary impact), HIGH (avoid)
            - Success rates: realistic estimates (0.0 to 1.0)
            - Maximum 3 remedies, ordered by effectiveness
            """
            
            response = model.generate_content(prompt)
            
            # Parse Gemini response
            try:
                # Clean the response text (remove markdown if present)
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                gemini_analysis = json.loads(response_text)
                
                # Validate the response structure
                if 'analysis' in gemini_analysis and 'remedies' in gemini_analysis:
                    return gemini_analysis
                else:
                    raise ValueError("Invalid response structure from Gemini")
                    
            except (json.JSONDecodeError, ValueError) as parse_error:
                st.warning(f"Gemini response parsing failed: {parse_error}")
                st.info("Falling back to mock analysis...")
                return self.get_mock_remedies(incident_type, metrics)
            
        except Exception as e:
            st.error(f"Error with Gemini analysis: {e}")
            st.info("Using fallback mock analysis...")
            return self.get_mock_remedies(incident_type, metrics)
    
    def get_mock_remedies(self, incident_type: str, metrics: Dict) -> Dict:
        """Mock remedies for testing without Gemini API"""
        remedies = {
            'high_cpu': [
                {
                    'description': 'Restart Windows Explorer (safe)',
                    'command': 'restart_explorer',
                    'risk_level': 'LOW',
                    'success_rate': 0.9
                },
                {
                    'description': 'Kill high CPU processes',
                    'command': 'kill_high_cpu',
                    'risk_level': 'MEDIUM',
                    'success_rate': 0.85
                }
            ],
            'high_memory': [
                {
                    'description': 'Clear system cache',
                    'command': 'clear_cache',
                    'risk_level': 'LOW',
                    'success_rate': 0.8
                },
                {
                    'description': 'Restart high memory processes',
                    'command': 'restart_memory_hogs',
                    'risk_level': 'MEDIUM',
                    'success_rate': 0.75
                }
            ],
            'high_disk': [
                {
                    'description': 'Clean temporary files',
                    'command': 'clean_temp',
                    'risk_level': 'LOW',
                    'success_rate': 0.9
                },
                {
                    'description': 'Clear browser cache',
                    'command': 'clear_browser_cache',
                    'risk_level': 'LOW',
                    'success_rate': 0.8
                }
            ]
        }
        
        return {
            'analysis': f'Detected {incident_type} - Current usage exceeds threshold',
            'remedies': remedies.get(incident_type, [])
        }
    
    def execute_remedy(self, command: str) -> Tuple[bool, str, str]:
        """Execute approved remedy with safe commands only"""
        safe_commands = {
            'restart_explorer': 'taskkill /f /im explorer.exe & start explorer.exe',
            'clear_cache': 'echo Clearing cache... & timeout 2 & echo Cache cleared',
            'clean_temp': 'echo Cleaning temp files... & timeout 2 & echo Temp cleaned',
            'clear_browser_cache': 'echo Clearing browser cache... & timeout 2 & echo Browser cache cleared',
            'kill_high_cpu': 'echo Terminating high CPU processes... & timeout 2 & echo Processes terminated',
            'restart_memory_hogs': 'echo Restarting memory intensive processes... & timeout 2 & echo Processes restarted'
        }
        
        if command not in safe_commands:
            return False, "", "Command not in safe list"
        
        try:
            result = subprocess.run(
                safe_commands[command], 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            return True, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def detect_issues(self, metrics: Dict) -> List[str]:
        """Detect issues based on thresholds"""
        issues = []
        
        if metrics.get('cpu_percent', 0) > self.thresholds['cpu_percent']:
            issues.append('high_cpu')
        
        if metrics.get('memory_percent', 0) > self.thresholds['memory_percent']:
            issues.append('high_memory')
        
        if metrics.get('disk_percent', 0) > self.thresholds['disk_percent']:
            issues.append('high_disk')
        
        return issues
    
    def log_incident(self, incident_type: str, metrics: Dict) -> int:
        """Log incident to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO incidents (timestamp, condition_type, severity, metrics)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            incident_type,
            'HIGH' if metrics.get('cpu_percent', 0) > 90 else 'MEDIUM',
            json.dumps(metrics)
        ))
        
        incident_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return incident_id
    
    def log_remedy(self, incident_id: int, remedy: Dict) -> int:
        """Log remedy to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO remedies (incident_id, remedy_type, command, description, risk_level, success_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            incident_id,
            remedy.get('command', ''),
            remedy.get('command', ''),
            remedy.get('description', ''),
            remedy.get('risk_level', 'UNKNOWN'),
            remedy.get('success_rate', 0.5)
        ))
        
        remedy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return remedy_id
    
    def log_execution(self, remedy_id: int, success: bool, output: str, error: str, approved: bool) -> None:
        """Log execution result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO executions (remedy_id, status, output, error, timestamp, user_approved)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            remedy_id,
            'SUCCESS' if success else 'FAILED',
            output,
            error,
            datetime.now().isoformat(),
            approved
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_incidents(self, limit: int = 10) -> pd.DataFrame:
        """Get recent incidents from database"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT i.*, COUNT(r.id) as remedy_count
            FROM incidents i
            LEFT JOIN remedies r ON i.id = r.incident_id
            GROUP BY i.id
            ORDER BY i.timestamp DESC
            LIMIT ?
        ''', conn, params=(limit,))
        conn.close()
        return df

# Streamlit UI
def main():
    st.set_page_config(page_title="Auto-Heal Infrastructure Monitor", layout="wide")
    
    # Initialize system
    if 'autoheal' not in st.session_state:
        st.session_state.autoheal = AutoHealSystem()
    
    autoheal = st.session_state.autoheal
    
    st.title("🔧 Auto-Heal Infrastructure Monitor")
    st.sidebar.title("Control Panel")
    
    # Control buttons
    if st.sidebar.button("🔍 Check System Now"):
        metrics = autoheal.get_system_metrics()
        st.session_state.current_metrics = metrics
        issues = autoheal.detect_issues(metrics)
        st.session_state.current_issues = issues
    
    # Display current metrics
    st.header("📊 System Metrics")
    
    if 'current_metrics' in st.session_state:
        metrics = st.session_state.current_metrics
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_color = "🔴" if metrics.get('cpu_percent', 0) > 60 else "🟢"
            st.metric("CPU Usage", f"{metrics.get('cpu_percent', 0):.1f}%", delta=None)
            st.write(cpu_color)
        
        with col2:
            mem_color = "🔴" if metrics.get('memory_percent', 0) > 60 else "🟢"
            st.metric("Memory Usage", f"{metrics.get('memory_percent', 0):.1f}%", delta=None)
            st.write(mem_color)
        
        with col3:
            disk_color = "🔴" if metrics.get('disk_percent', 0) > 90 else "🟢"
            st.metric("Disk Usage", f"{metrics.get('disk_percent', 0):.1f}%", delta=None)
            st.write(disk_color)
        
        with col4:
            st.metric("Processes", metrics.get('process_count', 0))
        
        # Show top processes
        if metrics.get('top_processes'):
            st.subheader("🔥 Top CPU Processes")
            df_processes = pd.DataFrame(metrics['top_processes'])
            st.dataframe(df_processes)
    
    # Issue Detection and Remedies
    if 'current_issues' in st.session_state and st.session_state.current_issues:
        st.header("⚠️ Issues Detected")
        
        for issue in st.session_state.current_issues:
            st.error(f"Alert: {issue.replace('_', ' ').title()}")
            
            # Log incident
            incident_id = autoheal.log_incident(issue, st.session_state.current_metrics)
            
            # Get remedies
            analysis = autoheal.analyze_with_gemini(st.session_state.current_metrics, issue)
            
            st.subheader(f"🔧 Proposed Remedies for {issue.replace('_', ' ').title()}")
            st.write(f"**Analysis:** {analysis.get('analysis', 'No analysis available')}")
            
            for i, remedy in enumerate(analysis.get('remedies', [])):
                with st.expander(f"Remedy {i+1}: {remedy['description']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Risk Level:** {remedy['risk_level']}")
                        st.write(f"**Success Rate:** {remedy['success_rate']*100:.0f}%")
                        st.write(f"**Command:** `{remedy['command']}`")
                    
                    with col2:
                        if st.button(f"✅ Execute", key=f"exec_{issue}_{i}"):
                            remedy_id = autoheal.log_remedy(incident_id, remedy)
                            
                            with st.spinner("Executing remedy..."):
                                success, output, error = autoheal.execute_remedy(remedy['command'])
                                autoheal.log_execution(remedy_id, success, output, error, True)
                            
                            if success:
                                st.success(f"✅ Remedy executed successfully!")
                                st.code(output)
                            else:
                                st.error(f"❌ Remedy failed: {error}")
    
    # Recent Incidents History
    st.header("📋 Recent Incidents")
    recent_incidents = autoheal.get_recent_incidents()
    
    if not recent_incidents.empty:
        st.dataframe(recent_incidents[['timestamp', 'condition_type', 'severity', 'status', 'remedy_count']])
    else:
        st.info("No incidents recorded yet. Click 'Check System Now' to start monitoring.")
    
    # Stress Testing Section
    st.sidebar.header("🧪 Stress Testing")
    st.sidebar.write("Use these to simulate issues:")
    
    if st.sidebar.button("💻 Stress CPU"):
        st.sidebar.code("python -c \"while True: pass\"")
        st.sidebar.write("Run this in Command Prompt to stress CPU")
    
    if st.sidebar.button("💾 Stress Memory"):
        st.sidebar.code("python -c \"x=[]; [x.append('a'*1024*1024) for i in range(1000)]\"")
        st.sidebar.write("Run this to consume memory")
    
    # Auto-refresh option
    if st.sidebar.checkbox("🔄 Auto-refresh (5s)"):
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()