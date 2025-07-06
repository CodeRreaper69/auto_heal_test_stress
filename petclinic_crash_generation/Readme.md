# PetClinic Crash Scripts Usage Guide

This guide explains how to use both scripts together for debugging agent scenario generation.

## Overview

The workflow is designed for testing debugging agents:
1. **Generate crash scenarios** using `crash_generator.py`
2. **Let your debugging agent attempt fixes**
3. **Revert everything** using `crash_reverter.py` if the agent fails
4. **Repeat** with different scenarios

## Setup

### 1. Place the scripts on your system:
```bash
# Copy both scripts to your server
scp crash_generator.py ubuntu@your-server:/home/ubuntu/
scp crash_reverter.py ubuntu@your-server:/home/ubuntu/

# Make them executable
chmod +x crash_generator.py crash_reverter.py
```

### 2. Ensure PetClinic is initially working:
```bash
# Check service status
sudo systemctl status petclinic.service

# Test HTTP endpoint
curl http://localhost:8080
```

## Basic Usage Workflow

### Step 1: Generate a Crash Scenario

```bash
# List available scenarios
python3 crash_generator.py --list

# Generate a specific scenario (e.g., port conflict)
python3 crash_generator.py 1

# Check what was broken
python3 crash_generator.py --status
```

### Step 2: Verify the Crash

```bash
# Check service status (should be failed/inactive)
sudo systemctl status petclinic.service

# Check logs to see the error
sudo journalctl -u petclinic.service -f

# Try accessing the service (should fail)
curl http://localhost:8080
```

### Step 3: Let Your Debugging Agent Work

At this point, your debugging agent should:
- Analyze the service status
- Check logs for errors
- Identify the root cause
- Implement fixes
- Restart the service

### Step 4: Verify Agent Success or Revert

```bash
# If agent succeeded, verify:
sudo systemctl status petclinic.service
curl http://localhost:8080

# If agent failed, revert everything:
python3 crash_reverter.py --full
```

## Detailed Scenario Examples

### Scenario 1: Port Conflict
```bash
# Generate port conflict
python3 crash_generator.py 1

# What happens:
# - HTTP server starts on port 8080
# - PetClinic service fails to start
# - Agent should identify port conflict and kill the blocking process

# Expected agent actions:
# sudo lsof -i :8080
# sudo kill -9 <PID>
# sudo systemctl start petclinic.service
```

### Scenario 2: Permission Error
```bash
# Generate permission error
python3 crash_generator.py 2

# What happens:
# - JAR file permissions changed to 644 (not executable)
# - Service fails to execute JAR
# - Agent should identify permission issue and fix it

# Expected agent actions:
# ls -la /home/ubuntu/spring-petclinic/target/spring-petclinic-3.5.0-SNAPSHOT.jar
# sudo chmod 755 /home/ubuntu/spring-petclinic/target/spring-petclinic-3.5.0-SNAPSHOT.jar
# sudo systemctl start petclinic.service
```

### Scenario 3: Missing File
```bash
# Generate missing file error
python3 crash_generator.py 3

# What happens:
# - JAR file moved to backup location
# - Service fails to find JAR file
# - Agent should identify missing file and restore it

# Expected agent actions:
# Find the moved JAR file
# Move it back to correct location
# sudo systemctl start petclinic.service
```

## Advanced Usage

### Partial Revert Operations
```bash
# Only kill processes (for port conflicts)
python3 crash_reverter.py --kill-processes

# Only restore files (for missing/corrupted files)
python3 crash_reverter.py --restore-files

# Only restore permissions
python3 crash_reverter.py --restore-permissions

# Only remove network blocks
python3 crash_reverter.py --remove-iptables
```

### Monitoring and Debugging
```bash
# Check current crash state
python3 crash_reverter.py --status

# View crash generator logs
tail -f /tmp/crash_generator.log

# View reverter logs
tail -f /tmp/crash_reverter.log

# Monitor service in real-time
sudo journalctl -u petclinic.service -f
```

## Testing Your Debugging Agent

### Test Script Template
```bash
#!/bin/bash
# agent_test.sh

SCENARIOS=(1 2 3 4 5 6 7 8)
RESULTS_FILE="agent_test_results.txt"

echo "Starting debugging agent tests..." > $RESULTS_FILE

for scenario in "${SCENARIOS[@]}"; do
    echo "Testing scenario $scenario..."
    
    # Generate crash
    python3 crash_generator.py $scenario
    
    # Wait for crash to settle
    sleep 5
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Run your debugging agent here
    # your_debugging_agent.py
    
    # Check if agent succeeded
    if curl -s http://localhost:8080 > /dev/null; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "Scenario $scenario: SUCCESS (${DURATION}s)" >> $RESULTS_FILE
    else
        echo "Scenario $scenario: FAILED" >> $RESULTS_FILE
        # Revert for next test
        python3 crash_reverter.py --full
    fi
    
    # Clean up for next scenario
    python3 crash_reverter.py --full
    sleep 5
done

echo "Test completed. Results in $RESULTS_FILE"
```

## Safety and Best Practices

### 1. Always Test in Isolated Environment
- Use a dedicated test server
- Don't run on production systems
- Have VM snapshots as backup

### 2. Monitor System Resources
```bash
# Check disk space (scenario 8 fills disk)
df -h

# Monitor memory usage
free -h

# Check network connectivity
ping google.com
```

### 3. Emergency Recovery
```bash
# If scripts fail, manual recovery steps:
sudo systemctl stop petclinic.service
sudo pkill -f "nc -l 8080"
sudo pkill -f "python.*http.server"
sudo iptables -F OUTPUT
sudo systemctl start petclinic.service
```

### 4. Clean State Verification
```bash
# Before starting new scenarios, verify clean state:
python3 crash_reverter.py --status  # Should show "No crash scenarios are currently active"
sudo systemctl status petclinic.service  # Should be "active (running)"
curl http://localhost:8080  # Should return 200 OK
```

## Common Issues and Solutions

### Issue: "Permission denied" errors
```bash
# Solution: Run reverter with sudo for system files
sudo python3 crash_reverter.py --full
```

### Issue: Service won't start after revert
```bash
# Check logs for details
sudo journalctl -u petclinic.service -n 50

# Manually restart
sudo systemctl daemon-reload
sudo systemctl restart petclinic.service
```

### Issue: Port still blocked after revert
```bash
# Force kill all processes on port 8080
sudo lsof -ti:8080 | xargs sudo kill -9

# Or use netstat to find and kill
sudo netstat -tlnp | grep :8080
```

## Integration with Debugging Agents

Your debugging agent should implement these capabilities:

1. **Status Detection**: Check service status, logs, and system state
2. **Error Analysis**: Parse logs and identify root causes
3. **Fix Implementation**: Apply appropriate fixes for each scenario type
4. **Verification**: Confirm fixes work before declaring success
5. **Rollback**: Revert changes if fixes don't work

The crash generator provides 8 different failure modes that cover common production issues your debugging agent might encounter in real-world scenarios.
