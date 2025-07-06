#!/usr/bin/env python3
"""
PetClinic Crash Reverter Script
Reverts all changes made by the crash generator script.
"""

import os
import subprocess
import shutil
import json
import signal
import time
from pathlib import Path
from datetime import datetime

class CrashReverter:
    def __init__(self):
        self.base_dir = "/home/ubuntu/spring-petclinic"
        self.jar_path = f"{self.base_dir}/target/spring-petclinic-3.5.0-SNAPSHOT.jar"
        self.service_file = "/etc/systemd/system/petclinic.service"
        self.backup_dir = "/tmp/petclinic_backup"
        self.state_file = "/tmp/crash_generator_state.json"
        self.log_file = "/tmp/crash_reverter.log"
        
        self.state = {}
        self.load_state()
    
    def log(self, message):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")
    
    def load_state(self):
        """Load state from crash generator"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
                self.log("Loaded crash generator state")
            except Exception as e:
                self.log(f"Could not load state: {e}")
                self.state = {}
        else:
            self.log("No crash generator state found")
    
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
        if success:
            self.log("Service started successfully")
        else:
            self.log(f"Service failed to start: {stderr}")
        return success
    
    def kill_processes(self):
        """Kill processes started by crash generator"""
        self.log("=== Killing Processes ===")
        
        processes = self.state.get("processes_started", [])
        
        for process_name, pid in processes:
            try:
                self.log(f"Killing process {process_name} (PID: {pid})")
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Already dead
            except ProcessLookupError:
                self.log(f"Process {pid} already terminated")
            except Exception as e:
                self.log(f"Error killing process {pid}: {e}")
        
        # Kill any remaining processes on port 8080
        self.log("Killing any remaining processes on port 8080...")
        success, stdout, stderr = self.run_command("sudo lsof -ti:8080", check=False)
        if success and stdout.strip():
            pids = stdout.strip().split('\n')
            for pid in pids:
                try:
                    self.run_command(f"sudo kill -9 {pid}", check=False)
                    self.log(f"Killed process {pid} on port 8080")
                except:
                    pass
        
        # Kill netcat processes
        self.run_command("sudo pkill -f 'nc -l 8080'", check=False)
        
        # Kill Python HTTP servers
        self.run_command("sudo pkill -f 'python.*http.server'", check=False)
    
    def restore_files(self):
        """Restore original files from backup"""
        self.log("=== Restoring Files ===")
        
        modified_files = self.state.get("files_modified", [])
        
        for file_entry in modified_files:
            if file_entry.startswith("moved:"):
                # Handle moved files
                _, original_path, moved_path = file_entry.split(":", 2)
                if os.path.exists(moved_path):
                    shutil.move(moved_path, original_path)
                    self.log(f"Restored moved file: {original_path}")
                else:
                    self.log(f"Moved file not found: {moved_path}")
            else:
                # Handle modified files
                file_path = file_entry
                backup_name = os.path.basename(file_path)
                backup_path = f"{self.backup_dir}/{backup_name}"
                
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, file_path)
                    self.log(f"Restored file: {file_path}")
                else:
                    self.log(f"Backup not found for: {file_path}")
                    
                    # Try to clean up invalid additions
                    if file_path.endswith("application.properties"):
                        self.clean_application_properties(file_path)
                    elif file_path.startswith("/tmp/crash_generator_large_file"):
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            self.log(f"Removed large file: {file_path}")
    
    def clean_application_properties(self, props_file):
        """Clean up invalid configuration from application.properties"""
        if not os.path.exists(props_file):
            return
        
        try:
            with open(props_file, 'r') as f:
                lines = f.readlines()
            
            # Remove lines added by crash generator
            clean_lines = []
            skip_section = False
            
            for line in lines:
                if "# Invalid configuration added by crash generator" in line:
                    skip_section = True
                    continue
                elif skip_section and (line.strip() == "" or line.startswith("#")):
                    continue
                elif skip_section and not line.startswith("server.port=invalid") and not line.startswith("spring.datasource.url=jdbc:invalid") and not line.startswith("spring.datasource.username=") and not line.startswith("spring.datasource.password=") and not line.startswith("logging.level.root=INVALID"):
                    skip_section = False
                    clean_lines.append(line)
                elif not skip_section:
                    clean_lines.append(line)
            
            with open(props_file, 'w') as f:
                f.writelines(clean_lines)
            
            self.log(f"Cleaned up {props_file}")
            
        except Exception as e:
            self.log(f"Error cleaning application.properties: {e}")
    
    def restore_permissions(self):
        """Restore original file permissions"""
        self.log("=== Restoring Permissions ===")
        
        original_permissions = self.state.get("original_permissions", {})
        
        for file_path, permissions in original_permissions.items():
            try:
                # Convert octal string to integer
                perm_int = int(permissions, 8)
                os.chmod(file_path, perm_int)
                self.log(f"Restored permissions for {file_path}: {permissions}")
            except Exception as e:
                self.log(f"Error restoring permissions for {file_path}: {e}")
    
    def remove_iptables_rules(self):
        """Remove iptables rules added by crash generator"""
        self.log("=== Removing iptables Rules ===")
        
        rules = self.state.get("iptables_rules", [])
        
        for rule in rules:
            # Convert ADD rule to DELETE rule
            delete_rule = rule.replace("-A OUTPUT", "-D OUTPUT")
            success, stdout, stderr = self.run_command(delete_rule, check=False)
            if success:
                self.log(f"Removed iptables rule: {delete_rule}")
            else:
                self.log(f"Could not remove rule (may not exist): {delete_rule}")
        
        # Flush all OUTPUT rules as backup (be careful!)
        self.run_command("sudo iptables -F OUTPUT", check=False)
        self.log("Flushed OUTPUT iptables rules")
    
    def restore_service_file(self):
        """Restore original service file"""
        if not self.state.get("service_modified", False):
            return
        
        self.log("=== Restoring Service File ===")
        
        backup_service = f"{self.backup_dir}/petclinic.service"
        
        if os.path.exists(backup_service):
            shutil.copy2(backup_service, self.service_file)
            self.log(f"Restored service file: {self.service_file}")
            
            # Reload systemd
            self.run_command("sudo systemctl daemon-reload")
            self.log("Reloaded systemd configuration")
        else:
            self.log("No backup service file found")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        self.log("=== Cleaning Up Temporary Files ===")
        
        temp_files = [
            "/tmp/crash_generator_large_file",
            "/tmp/petclinic_backup_temp",
        ]
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                    else:
                        shutil.rmtree(temp_file)
                    self.log(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    self.log(f"Error removing {temp_file}: {e}")
    
    def verify_service_health(self):
        """Verify that the service is healthy"""
        self.log("=== Verifying Service Health ===")
        
        # Check if service is running
        success, stdout, stderr = self.run_command("sudo systemctl is-active petclinic.service", check=False)
        if success and "active" in stdout:
            self.log("✅ Service is active")
        else:
            self.log("❌ Service is not active")
            return False
        
        # Check if port 8080 is listening
        time.sleep(5)  # Give service time to start
        success, stdout, stderr = self.run_command("netstat -tlnp | grep :8080", check=False)
        if success and "8080" in stdout:
            self.log("✅ Service is listening on port 8080")
        else:
            self.log("❌ Service is not listening on port 8080")
            return False
        
        # Try to connect to the service
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8080", timeout=10)
            if response.getcode() == 200:
                self.log("✅ Service is responding to HTTP requests")
                return True
            else:
                self.log(f"❌ Service returned status code: {response.getcode()}")
                return False
        except Exception as e:
            self.log(f"❌ Could not connect to service: {e}")
            return False
    
    def clear_state(self):
        """Clear the crash generator state"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
            self.log("Cleared crash generator state")
    
    def full_revert(self):
        """Perform complete revert of all changes"""
        self.log("Starting full revert of all crash scenarios...")
        
        # Stop service first
        self.stop_service()
        
        # Revert all changes
        self.kill_processes()
        self.remove_iptables_rules()
        self.restore_service_file()
        self.restore_files()
        self.restore_permissions()
        self.cleanup_temp_files()
        
        # Start service
        self.start_service()
        
        # Verify health
        if self.verify_service_health():
            self.log("✅ Full revert completed successfully")
            self.clear_state()
            return True
        else:
            self.log("❌ Service health check failed after revert")
            return False
    
    def show_status(self):
        """Show current status"""
        if not self.state:
            print("No crash scenarios are currently active")
            return
        
        print("\n=== Current Crash Generator State ===")
        print(f"Active scenario: {self.state.get('active_scenario', 'None')}")
        print(f"Timestamp: {self.state.get('timestamp', 'Unknown')}")
        print(f"Processes started: {len(self.state.get('processes_started', []))}")
        print(f"Files modified: {len(self.state.get('files_modified', []))}")
        print(f"Permissions changed: {len(self.state.get('original_permissions', {}))}")
        print(f"Iptables rules: {len(self.state.get('iptables_rules', []))}")
        print(f"Service modified: {self.state.get('service_modified', False)}")
        print()
        
        # Show service status
        success, stdout, stderr = self.run_command("sudo systemctl is-active petclinic.service", check=False)
        print(f"Service status: {stdout.strip() if success else 'Unknown'}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Revert PetClinic crash scenarios")
    parser.add_argument("--full", action="store_true", help="Perform full revert of all changes")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--kill-processes", action="store_true", help="Kill crash generator processes only")
    parser.add_argument("--restore-files", action="store_true", help="Restore modified files only")
    parser.add_argument("--restore-permissions", action="store_true", help="Restore file permissions only")
    parser.add_argument("--remove-iptables", action="store_true", help="Remove iptables rules only")
    parser.add_argument("--restore-service", action="store_true", help="Restore service file only")
    parser.add_argument("--cleanup-temp", action="store_true", help="Clean up temporary files only")
    parser.add_argument("--verify-health", action="store_true", help="Verify service health only")
    parser.add_argument("--clear-state", action="store_true", help="Clear crash generator state only")
    
    args = parser.parse_args()
    
    reverter = CrashReverter()
    
    if args.status:
        reverter.show_status()
        return
    
    if args.full:
        success = reverter.full_revert()
        if success:
            print("\n✅ Full revert completed successfully!")
            print("The PetClinic service should now be running normally.")
        else:
            print("\n❌ Full revert completed with issues.")
            print("Please check the logs and service status manually.")
        return
    
    # Individual operations
    if args.kill_processes:
        reverter.kill_processes()
        print("✅ Processes killed")
    
    if args.restore_files:
        reverter.restore_files()
        print("✅ Files restored")
    
    if args.restore_permissions:
        reverter.restore_permissions()
        print("✅ Permissions restored")
    
    if args.remove_iptables:
        reverter.remove_iptables_rules()
        print("✅ Iptables rules removed")
    
    if args.restore_service:
        reverter.restore_service_file()
        print("✅ Service file restored")
    
    if args.cleanup_temp:
        reverter.cleanup_temp_files()
        print("✅ Temporary files cleaned up")
    
    if args.verify_health:
        if reverter.verify_service_health():
            print("✅ Service health check passed")
        else:
            print("❌ Service health check failed")
    
    if args.clear_state:
        reverter.clear_state()
        print("✅ State cleared")
    
    # If no specific arguments provided, show help
    if not any([args.full, args.status, args.kill_processes, args.restore_files, 
               args.restore_permissions, args.remove_iptables, args.restore_service, 
               args.cleanup_temp, args.verify_health, args.clear_state]):
        parser.print_help()
        print("\nMost common usage:")
        print("  python3 crash_reverter.py --full      # Revert all changes")
        print("  python3 crash_reverter.py --status    # Show current status")

if __name__ == "__main__":
    main()
