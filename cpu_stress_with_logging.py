# cpu_stress.py - CPU Stress Test with Logging
import multiprocessing
import time
import sys
import logging
import os

# Configure logging to /var/log/cpu_stress.log
LOG_PATH = "/var/log/cpu_stress.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def cpu_stress_worker():
    """Worker function to stress one CPU core"""
    logging.info("Stressing CPU core...")
    while True:
        for _ in range(10000):
            pass

def stress_cpu(duration_seconds=60, num_cores=None):
    """
    Stress test CPU for specified duration
    """
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()

    logging.info("Starting CPU stress test")
    logging.info(f"Duration: {duration_seconds} seconds")
    logging.info(f"Using {num_cores} cores")

    processes = []
    for i in range(num_cores):
        p = multiprocessing.Process(target=cpu_stress_worker)
        p.start()
        processes.append(p)

    try:
        time.sleep(duration_seconds)
    except KeyboardInterrupt:
        logging.warning("CPU stress test interrupted by user")

    for p in processes:
        p.terminate()
        p.join()

    logging.info("CPU stress test completed")

if __name__ == "__main__":
    duration = 60
    cores = None

    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            logging.error("Invalid duration argument")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            cores = int(sys.argv[2])
        except ValueError:
            logging.error("Invalid cores argument")
            sys.exit(1)

    stress_cpu(duration, cores)
