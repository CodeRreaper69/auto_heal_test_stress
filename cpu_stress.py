# cpu_stress.py - CPU Stress Test for Windows
import multiprocessing
import time
import sys

def cpu_stress_worker():
    """Worker function to stress one CPU core"""
    print(f"Stressing CPU core...")
    while True:
        # Busy loop to consume CPU
        for i in range(10000):
            pass

def stress_cpu(duration_seconds=60, num_cores=None):
    """
    Stress test CPU for specified duration
    
    Args:
        duration_seconds: How long to stress (default 60 seconds)
        num_cores: Number of cores to stress (default: all available)
    """
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()
    
    print(f"Starting CPU stress test...")
    print(f"Duration: {duration_seconds} seconds")
    print(f"Using {num_cores} cores")
    print("Press Ctrl+C to stop early")
    
    # Start worker processes
    processes = []
    for i in range(num_cores):
        p = multiprocessing.Process(target=cpu_stress_worker)
        p.start()
        processes.append(p)
    
    try:
        # Let it run for specified duration
        time.sleep(duration_seconds)
    except KeyboardInterrupt:
        print("\nStopping CPU stress test...")
    
    # Terminate all processes
    for p in processes:
        p.terminate()
        p.join()
    
    print("CPU stress test completed.")

if __name__ == "__main__":
    # Parse command line arguments
    duration = 60  # default 60 seconds
    cores = None   # default all cores
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("Usage: python cpu_stress.py [duration_seconds] [num_cores]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            cores = int(sys.argv[2])
        except ValueError:
            print("Usage: python cpu_stress.py [duration_seconds] [num_cores]")
            sys.exit(1)
    
    stress_cpu(duration, cores)