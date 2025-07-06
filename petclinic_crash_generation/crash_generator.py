#!/usr/bin/env python3
"""
PetClinic Crash Generator Script
Generates various failure scenarios for testing debugging agents.
"""

import os
import subprocess
import shutil
import json
import time
import signal
import socket
import threading
from pathlib import Path
from datetime import datetime

class CrashGenerator:
    def __init__(self):
        self.base_dir = "/home/ubuntu/spring-petclinic"
        self.jar_path = f"{self.base_dir}/target/spring-petclinic-3.5.0-SNAPSHOT.jar"
        self.service_file = "/etc/systemd/system/petclinic.service"
        self.backup_dir = "/tmp/petclinic_backup"
        self.state_file = "/tmp/crash_generator_state.json"
        self.log_file = "/tmp/crash_generator.log"
        
        # Create backup directory
        Path(self.backup_dir).mkdir(exist_ok=True)
        
        # Initialize state tracking
        self.state = {
            "active_scenario": None,
            "timestamp": None,
            "backup_created": False,
            "processes_started": [],
            "files_modified": [],
            "original_permissions": {},
            "iptables_rules": [],
            "service_modified": False
        }
        
        self.load_state()
    
    def log(self, message):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")
    
    def save_state(self):
        """Save current state to file"""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def load_state(self):
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.state.update(json.load(f))
            except:
                self.log("Warning: Could not load previous state")
    
    def create_backup(self):
        """Create backup of original files"""
        if self.state["backup_created"]:
            return
        
        self.log("Creating backup of original files...")
        
        # Backup JAR file
        if os.path.exists(self.jar_path):
            shutil.copy2(self.jar_path, f"{self.backup_dir}/spring-petclinic-3.5.0-SNAPSHOT.jar")
            self.log(f"Backed up JAR to {self.backup_dir}")
        
        # Backup service file
        if os.path.exists(self.service_file):
            shutil.copy2(self.service_file, f"{self.backup_dir}/petclinic.service")
            self.log(f"Backed up service file to {self.backup_dir}")
        
        # Backup application.properties if exists
        props_file = f"{self.base_dir}/src/main/resources/application.properties"
        if os.path.exists(props_file):
            shutil.copy2(props_file, f"{self.backup_dir}/application.properties")
            self.log(f"Backed up application.properties to {self.backup_dir}")
        
        self.state["backup_created"] = True
        self.save_state()
    
    def run_command(self, command, check=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
    
    def stop_service(self):
        """Stop petclinic service"""
        self.log("Stopping petclinic service...")
        self.run_command("sudo systemctl stop petclinic.service", check=False)
        time.sleep(2)
    
    def start_service(self):
        """Start petclinic service"""
        self.log("Starting petclinic service...")
        success, stdout, stderr = self.run_command("sudo systemctl start petclinic.service", check=False)
        if not success:
            self.log(f"Service failed to start: {stderr}")
        return success
    
    def scenario_1_port_conflict(self):
        """Generate port conflict by starting HTTP server on 8080"""
        self.log("=== Scenario 1: Port Conflict ===")
        
        # Start HTTP server on port 8080
        def start_http_server():
            try:
                import http.server
                import socketserver
                
                class QuietHandler(http.server.SimpleHTTPRequestHandler):
                    def log_message(self, format, *args):
                        pass
                
                with socketserver.TCPServer(("", 8080), QuietHandler) as httpd:
                    self.log("HTTP server started on port 8080")
                    httpd.serve_forever()
            except Exception as e:
                self.log(f"HTTP server error: {e}")
        
        # Start server in background thread
        server_thread = threading.Thread(target=start_http_server, daemon=True)
        server_thread.start()
        
        # Also start a simple netcat listener as backup
        nc_process = subprocess.Popen(["nc", "-l", "8080"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.state["processes_started"].append(("nc", nc_process.pid))
        
        time.sleep(2)
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_2_permission_error(self):
        """Generate permission error by changing JAR permissions"""
        self.log("=== Scenario 2: Permission Error ===")
        
        if not os.path.exists(self.jar_path):
            self.log("JAR file not found, skipping permission scenario")
            return False
        
        # Save original permissions
        stat_info = os.stat(self.jar_path)
        self.state["original_permissions"][self.jar_path] = oct(stat_info.st_mode)[-3:]
        
        # Remove execute permissions
        os.chmod(self.jar_path, 0o644)
        self.state["files_modified"].append(self.jar_path)
        
        self.log(f"Changed permissions of {self.jar_path} to 644")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_3_missing_file(self):
        """Generate missing file error by moving JAR"""
        self.log("=== Scenario 3: Missing File ===")
        
        if not os.path.exists(self.jar_path):
            self.log("JAR file not found, skipping missing file scenario")
            return False
        
        # Move JAR file to backup location
        moved_path = f"{self.backup_dir}/moved_jar.jar"
        shutil.move(self.jar_path, moved_path)
        self.state["files_modified"].append(f"moved:{self.jar_path}:{moved_path}")
        
        self.log(f"Moved JAR from {self.jar_path} to {moved_path}")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_4_memory_limit(self):
        """Generate memory limit error by modifying service"""
        self.log("=== Scenario 4: Memory Limit ===")
        
        if not os.path.exists(self.service_file):
            self.log("Service file not found, skipping memory limit scenario")
            return False
        
        # Read current service file
        with open(self.service_file, 'r') as f:
            content = f.read()
        
        # Modify ExecStart to use very low memory
        new_content = content.replace(
            'ExecStart=/usr/bin/java -jar',
            'ExecStart=/usr/bin/java -Xmx32m -Xms16m -jar'
        )
        
        # Write modified service file
        with open(self.service_file, 'w') as f:
            f.write(new_content)
        
        self.state["service_modified"] = True
        self.state["files_modified"].append(self.service_file)
        
        # Reload systemd
        self.run_command("sudo systemctl daemon-reload")
        
        self.log("Modified service file to use 32MB max memory")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_5_invalid_config(self):
        """Generate invalid configuration error"""
        self.log("=== Scenario 5: Invalid Configuration ===")
        
        props_file = f"{self.base_dir}/src/main/resources/application.properties"
        
        # Create invalid configuration
        invalid_config = """
# Invalid configuration added by crash generator
server.port=invalid_port_number
spring.datasource.url=jdbc:invalid://localhost:3306/invalid
spring.datasource.username=
spring.datasource.password=
logging.level.root=INVALID_LEVEL
"""
        
        with open(props_file, 'a') as f:
            f.write(invalid_config)
        
        self.state["files_modified"].append(props_file)
        
        self.log(f"Added invalid configuration to {props_file}")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_6_network_issues(self):
        """Generate network issues using iptables"""
        self.log("=== Scenario 6: Network Issues ===")
        
        # Block common ports
        rules = [
            "sudo iptables -A OUTPUT -p tcp --dport 80 -j DROP",
            "sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP",
            "sudo iptables -A OUTPUT -p tcp --dport 53 -j DROP"
        ]
        
        for rule in rules:
            success, _, _ = self.run_command(rule, check=False)
            if success:
                self.state["iptables_rules"].append(rule)
                self.log(f"Applied iptables rule: {rule}")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_7_user_permission(self):
        """Generate user permission issues"""
        self.log("=== Scenario 7: User Permission Issues ===")
        
        if not os.path.exists(self.service_file):
            self.log("Service file not found, skipping user permission scenario")
            return False
        
        # Read current service file
        with open(self.service_file, 'r') as f:
            content = f.read()
        
        # Change user to nobody
        new_content = content.replace('User=ubuntu', 'User=nobody')
        
        # Write modified service file
        with open(self.service_file, 'w') as f:
            f.write(new_content)
        
        self.state["service_modified"] = True
        self.state["files_modified"].append(self.service_file)
        
        # Reload systemd
        self.run_command("sudo systemctl daemon-reload")
        
        self.log("Changed service user to 'nobody'")
        
        # Try to start the service
        self.start_service()
        
        return True
    
    def scenario_8_disk_space(self):
        """Generate disk space issues"""
        self.log("=== Scenario 8: Disk Space Issues ===")
        
        # Create a large file to fill disk space (be careful!)
        large_file = "/tmp/crash_generator_large_file"
        
        try:
            # Get available space
            statvfs = os.statvfs('/tmp')
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            
            # Use 80% of available space
            file_size = int(free_bytes * 0.8)
            
            self.log(f"Creating {file_size} byte file to simulate disk space issue")
            
            with open(large_file, 'wb') as f:
                f.write(b'0' * file_size)
            
            self.state["files_modified"].append(large_file)
            
            # Try to start the service
            self.start_service()
            
            return True
        except Exception as e:
            self.log(f"Could not create large file: {e}")
            return False
    
    def run_scenario(self, scenario_num):
        """Run a specific scenario"""
        self.create_backup()
        self.stop_service()
        
        scenarios = {
            1: self.scenario_1_port_conflict,
            2: self.scenario_2_permission_error,
            3: self.scenario_3_missing_file,
            4: self.scenario_4_memory_limit,
            5: self.scenario_5_invalid_config,
            6: self.scenario_6_network_issues,
            7: self.scenario_7_user_permission,
            8: self.scenario_8_disk_space
        }
        
        if scenario_num not in scenarios:
            self.log(f"Invalid scenario number: {scenario_num}")
            return False
        
        self.state["active_scenario"] = scenario_num
        self.state["timestamp"] = datetime.now().isoformat()
        
        try:
            result = scenarios[scenario_num]()
            self.save_state()
            return result
        except Exception as e:
            self.log(f"Error running scenario {scenario_num}: {e}")
            return False
    
    def list_scenarios(self):
        """List all available scenarios"""
        scenarios = [
            "1. Port Conflict (HTTP server on 8080)",
            "2. Permission Error (JAR not executable)",
            "3. Missing File (JAR moved away)",
            "4. Memory Limit (32MB max heap)",
            "5. Invalid Configuration (bad application.properties)",
            "6. Network Issues (blocked outbound ports)",
            "7. User Permission (service runs as 'nobody')",
            "8. Disk Space Issues (fill disk space)"
        ]
        
        print("\nAvailable Crash Scenarios:")
        for scenario in scenarios:
            print(f"  {scenario}")
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate PetClinic crash scenarios")
    parser.add_argument("scenario", type=int, nargs='?', help="Scenario number (1-8)")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument("--status", action="store_true", help="Show current status")
    
    args = parser.parse_args()
    
    generator = CrashGenerator()
    
    if args.list:
        generator.list_scenarios()
        return
    
    if args.status:
        if os.path.exists(generator.state_file):
            with open(generator.state_file, 'r') as f:
                state = json.load(f)
            print(f"Current state: {json.dumps(state, indent=2)}")
        else:
            print("No active scenarios")
        return
    
    if args.scenario:
        if 1 <= args.scenario <= 8:
            generator.log(f"Starting crash scenario {args.scenario}")
            success = generator.run_scenario(args.scenario)
            if success:
                generator.log(f"Scenario {args.scenario} executed successfully")
                generator.log("Check service status with: sudo systemctl status petclinic.service")
                generator.log("Check logs with: sudo journalctl -u petclinic.service -f")
            else:
                generator.log(f"Scenario {args.scenario} failed to execute")
        else:
            generator.log("Invalid scenario number. Use --list to see available scenarios")
    else:
        generator.list_scenarios()
        print("Usage: python3 crash_generator.py <scenario_number>")

if __name__ == "__main__":
    main()
