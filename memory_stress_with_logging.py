# memory_stress.py - Memory Stress Test with Logging

import time
import sys
import psutil
import logging
import os
import gc

# Set up logging
LOG_PATH = "/var/log/memory_stress.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def stress_memory(target_percent=80, duration_seconds=60):
    logging.info("Starting Memory stress test...")
    logging.info(f"Target: {target_percent}% memory usage for {duration_seconds} seconds")
    
    total_memory = psutil.virtual_memory().total
    target_bytes = int((target_percent / 100) * total_memory)
    
    logging.info(f"Total Memory: {total_memory / (1024**3):.2f} GB")
    logging.info(f"Target Memory: {target_bytes / (1024**3):.2f} GB")
    
    memory_blocks = []
    block_size = 1024 * 1024 * 10  # 10MB

    try:
        current_usage = psutil.virtual_memory().percent
        logging.info(f"Initial memory usage: {current_usage:.1f}%")

        while current_usage < target_percent:
            block = bytearray(block_size)
            for i in range(0, len(block), 4096):
                block[i] = 1
            memory_blocks.append(block)
            current_usage = psutil.virtual_memory().percent

            logging.info(f"Memory usage: {current_usage:.1f}% "
                         f"({len(memory_blocks) * block_size / (1024**3):.2f} GB allocated)")
            time.sleep(0.5)

            if current_usage >= 95:
                logging.warning("Reached 95% memory usage, stopping for safety")
                break

        logging.info(f"Target reached. Holding memory for {duration_seconds} seconds...")

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            current_usage = psutil.virtual_memory().percent
            time.sleep(1)

    except KeyboardInterrupt:
        logging.warning("Memory stress test interrupted by user")
    except MemoryError:
        logging.error("Memory allocation failed - system limit reached")

    logging.info(f"Releasing {len(memory_blocks)} memory blocks...")
    memory_blocks.clear()
    gc.collect()
    final_usage = psutil.virtual_memory().percent
    logging.info(f"Memory stress test completed. Final usage: {final_usage:.1f}%")

def gradual_memory_stress(max_percent=85, step_percent=5, hold_seconds=10):
    logging.info("Starting gradual memory stress test...")
    memory_blocks = []
    block_size = 1024 * 1024 * 10  # 10MB

    try:
        for target in range(step_percent, max_percent + 1, step_percent):
            logging.info(f"Target: {target}% memory usage")
            current_usage = psutil.virtual_memory().percent

            while current_usage < target:
                block = bytearray(block_size)
                for i in range(0, len(block), 4096):
                    block[i] = 1
                memory_blocks.append(block)
                current_usage = psutil.virtual_memory().percent
                time.sleep(0.2)

            logging.info(f"Reached {current_usage:.1f}%. Holding for {hold_seconds} seconds...")
            time.sleep(hold_seconds)

    except KeyboardInterrupt:
        logging.warning("Gradual memory stress interrupted by user")

    logging.info(f"Releasing {len(memory_blocks)} memory blocks...")
    memory_blocks.clear()
    gc.collect()
    logging.info("Gradual memory stress completed. Memory released.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "gradual":
            gradual_memory_stress()
        else:
            try:
                target = int(sys.argv[1])
                duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
                stress_memory(target, duration)
            except ValueError:
                print("Usage:")
                print("  python memory_stress.py [target_percent] [duration_seconds]")
                print("  python memory_stress.py gradual")
                sys.exit(1)
    else:
        stress_memory()
