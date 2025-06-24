# memory_stress.py - Memory Stress Test for Windows
import time
import sys
import psutil

def stress_memory(target_percent=80, duration_seconds=60):
    """
    Stress test memory by consuming RAM up to target percentage
    
    Args:
        target_percent: Target memory usage percentage (default 80%)
        duration_seconds: How long to maintain memory usage (default 60 seconds)
    """
    print(f"Starting Memory stress test...")
    print(f"Target: {target_percent}% memory usage")
    print(f"Duration: {duration_seconds} seconds")
    print("Press Ctrl+C to stop early")
    
    # Get total memory
    total_memory = psutil.virtual_memory().total
    target_bytes = int((target_percent / 100) * total_memory)
    
    print(f"Total Memory: {total_memory / (1024**3):.2f} GB")
    print(f"Target Memory: {target_bytes / (1024**3):.2f} GB")
    
    memory_blocks = []
    block_size = 1024 * 1024 * 10  # 10MB blocks
    
    try:
        # Gradually consume memory
        current_usage = psutil.virtual_memory().percent
        print(f"Current memory usage: {current_usage:.1f}%")
        
        while current_usage < target_percent:
            # Allocate memory block
            block = bytearray(block_size)
            # Write to ensure it's actually allocated
            for i in range(0, len(block), 4096):
                block[i] = 1
            
            memory_blocks.append(block)
            current_usage = psutil.virtual_memory().percent
            
            print(f"Memory usage: {current_usage:.1f}% "
                  f"({len(memory_blocks) * block_size / (1024**3):.2f} GB allocated)")
            
            time.sleep(0.5)  # Small delay to prevent system freeze
            
            if current_usage >= 95:  # Safety limit
                print("Reached 95% memory usage - stopping for safety")
                break
        
        print(f"Target reached! Maintaining {current_usage:.1f}% memory usage...")
        
        # Hold memory for specified duration
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            current_usage = psutil.virtual_memory().percent
            print(f"Holding memory: {current_usage:.1f}%", end='\r')
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nStopping memory stress test...")
    except MemoryError:
        print("Memory allocation failed - system limit reached")
    
    # Clean up memory
    print(f"\nReleasing {len(memory_blocks)} memory blocks...")
    memory_blocks.clear()
    
    # Force garbage collection
    import gc
    gc.collect()
    
    final_usage = psutil.virtual_memory().percent
    print(f"Memory stress test completed. Current usage: {final_usage:.1f}%")

def gradual_memory_stress(max_percent=85, step_percent=5, hold_seconds=10):
    """
    Gradually increase memory usage in steps
    """
    print("Starting gradual memory stress test...")
    memory_blocks = []
    block_size = 1024 * 1024 * 10  # 10MB blocks
    
    try:
        for target in range(step_percent, max_percent + 1, step_percent):
            print(f"\nTarget: {target}% memory usage")
            
            current_usage = psutil.virtual_memory().percent
            while current_usage < target:
                block = bytearray(block_size)
                for i in range(0, len(block), 4096):
                    block[i] = 1
                memory_blocks.append(block)
                current_usage = psutil.virtual_memory().percent
                time.sleep(0.2)
            
            print(f"Reached {current_usage:.1f}% - holding for {hold_seconds} seconds...")
            time.sleep(hold_seconds)
    
    except KeyboardInterrupt:
        print("\nStopping gradual memory stress test...")
    
    # Clean up
    memory_blocks.clear()
    import gc
    gc.collect()
    print("Memory released.")

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