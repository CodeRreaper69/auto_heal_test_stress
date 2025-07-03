# To run the cpu_stress_with_logging.py run this - 
- ```sudo python3 cpu_stress_with_logging.py <time in seconds for running it> <Number of cores you want to stress>```
- Example run - ```sudo python3 cpu_stress_with_logging.py 240 2``` - ## This will run it for 240 seconds occupying 2 CPU cores
- Logs will get saved at - ```/var/log/cpu_stress.log```
Sample output (Will not be visible on command prompt, but rather on Grafana or in log files, to get the logs on command line, run the same but the codes without `with_logging` part' i.e, `python3 cpu_stress.py  240 2` )
```
2025-06-26 06:45:19,420 - INFO - Stressing CPU core...
2025-06-26 06:45:19,469 - INFO - Stressing CPU core...
2025-06-26 06:45:19,591 - INFO - Stressing CPU core...
2025-06-26 06:45:19,540 - INFO - Stressing CPU core...
2025-06-26 06:45:19,541 - INFO - Stressing CPU core...
2025-06-26 06:45:19,649 - INFO - Stressing CPU core...
2025-06-26 06:49:20,747 - INFO - CPU stress test completed
2025-06-27 06:50:23,494 - INFO - Starting CPU stress test
2025-06-27 06:50:23,495 - INFO - Duration: 240 seconds
2025-06-27 06:50:23,495 - INFO - Using 2 cores
2025-06-27 06:50:23,509 - INFO - Stressing CPU core...
2025-06-27 06:50:23,515 - INFO - Stressing CPU core...
2025-06-27 06:54:18,752 - WARNING - CPU stress test interrupted by user
2025-06-27 06:54:18,755 - INFO - CPU stress test completed
```

# To run the memory_stress_with_logging.py run this -
- ```sudo python3 memory_stress_with_logging.py <How much percent of memory to stress>  <Time in seconds until it runs>```
- Example run - ```sudo python3 memory_stress_with_logging.py 70 240``` ## This will run it for 240 seconds occupying 70% of the memory
- Logs will get saved at - ```/var/log/memory_stress.log```
Sample output (Will not be visible on command prompt, but rather on Grafana or in log files to get the logs on command line, run the same but the codes without `with_logging` part' i.e, `python3 memory_stress.py  70 240` )
```
2025-06-30 13:16:37,938 - INFO - Starting Memory stress test...
2025-06-30 13:16:37,939 - INFO - Target: 70% memory usage for 240 seconds
2025-06-30 13:16:37,939 - INFO - Total Memory: 3.76 GB
2025-06-30 13:16:37,939 - INFO - Target Memory: 2.63 GB
2025-06-30 13:16:37,939 - INFO - Initial memory usage: 32.2%
2025-06-30 13:16:37,949 - INFO - Memory usage: 32.4% (0.01 GB allocated)
2025-06-30 13:16:38,462 - INFO - Memory usage: 32.7% (0.02 GB allocated)
2025-06-30 13:16:43,063 - INFO - Memory usage: 34.9% (0.11 GB allocated)
2025-06-30 13:16:43,574 - INFO - Memory usage: 35.4% (0.12 GB allocated)
2025-06-30 13:16:58,945 - INFO - Memory usage: 43.1% (0.41 GB allocated)
2025-06-30 13:16:59,455 - INFO - Memory usage: 43.4% (0.42 GB allocated)
...
2025-06-30 13:17:51,747 - INFO - Memory usage: 70.1% (1.42 GB allocated)
2025-06-30 13:17:52,248 - INFO - Target reached. Holding memory for 240 seconds...
2025-06-30 13:18:11,220 - WARNING - Memory stress test interrupted by user
2025-06-30 13:18:11,220 - INFO - Releasing 145 memory blocks...
2025-06-30 13:18:11,543 - INFO - Memory stress test completed. Final usage: 33.7%
```
# To install python libraries, the correct command instead of ```pip3 install <lib name>``` is ```sudo apt install python3-<library-name>``` 
