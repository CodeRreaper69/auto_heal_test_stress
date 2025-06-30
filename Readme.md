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
2025-06-30 13:16:38,976 - INFO - Memory usage: 32.9% (0.03 GB allocated)
2025-06-30 13:16:39,488 - INFO - Memory usage: 33.3% (0.04 GB allocated)
2025-06-30 13:16:40,001 - INFO - Memory usage: 33.4% (0.05 GB allocated)
2025-06-30 13:16:40,510 - INFO - Memory usage: 33.6% (0.06 GB allocated)
2025-06-30 13:16:41,022 - INFO - Memory usage: 33.9% (0.07 GB allocated)
2025-06-30 13:16:41,531 - INFO - Memory usage: 34.1% (0.08 GB allocated)
2025-06-30 13:16:42,041 - INFO - Memory usage: 34.5% (0.09 GB allocated)
2025-06-30 13:16:42,551 - INFO - Memory usage: 34.7% (0.10 GB allocated)
2025-06-30 13:16:43,063 - INFO - Memory usage: 34.9% (0.11 GB allocated)
2025-06-30 13:16:43,574 - INFO - Memory usage: 35.4% (0.12 GB allocated)
2025-06-30 13:16:44,085 - INFO - Memory usage: 35.5% (0.13 GB allocated)
2025-06-30 13:16:44,594 - INFO - Memory usage: 35.8% (0.14 GB allocated)
2025-06-30 13:16:45,105 - INFO - Memory usage: 36.0% (0.15 GB allocated)
2025-06-30 13:16:45,614 - INFO - Memory usage: 36.4% (0.16 GB allocated)
2025-06-30 13:16:46,129 - INFO - Memory usage: 36.6% (0.17 GB allocated)
2025-06-30 13:16:46,645 - INFO - Memory usage: 36.8% (0.18 GB allocated)
2025-06-30 13:16:47,169 - INFO - Memory usage: 37.1% (0.19 GB allocated)
2025-06-30 13:16:47,684 - INFO - Memory usage: 37.5% (0.20 GB allocated)
2025-06-30 13:16:48,196 - INFO - Memory usage: 37.7% (0.21 GB allocated)
2025-06-30 13:16:48,711 - INFO - Memory usage: 37.9% (0.21 GB allocated)
2025-06-30 13:16:49,224 - INFO - Memory usage: 38.4% (0.22 GB allocated)
2025-06-30 13:16:49,734 - INFO - Memory usage: 38.4% (0.23 GB allocated)
2025-06-30 13:16:50,244 - INFO - Memory usage: 38.8% (0.24 GB allocated)
2025-06-30 13:16:50,753 - INFO - Memory usage: 39.1% (0.25 GB allocated)
2025-06-30 13:16:51,264 - INFO - Memory usage: 39.3% (0.26 GB allocated)
2025-06-30 13:16:51,778 - INFO - Memory usage: 39.5% (0.27 GB allocated)
2025-06-30 13:16:52,298 - INFO - Memory usage: 39.6% (0.28 GB allocated)
2025-06-30 13:16:52,809 - INFO - Memory usage: 39.9% (0.29 GB allocated)
2025-06-30 13:16:53,318 - INFO - Memory usage: 40.1% (0.30 GB allocated)
2025-06-30 13:16:53,832 - INFO - Memory usage: 40.5% (0.31 GB allocated)
2025-06-30 13:16:54,344 - INFO - Memory usage: 40.8% (0.32 GB allocated)
2025-06-30 13:16:54,855 - INFO - Memory usage: 40.8% (0.33 GB allocated)
2025-06-30 13:16:55,369 - INFO - Memory usage: 41.3% (0.34 GB allocated)
2025-06-30 13:16:55,878 - INFO - Memory usage: 41.4% (0.35 GB allocated)
2025-06-30 13:16:56,387 - INFO - Memory usage: 41.6% (0.36 GB allocated)
2025-06-30 13:16:56,896 - INFO - Memory usage: 42.0% (0.37 GB allocated)
2025-06-30 13:16:57,414 - INFO - Memory usage: 42.1% (0.38 GB allocated)
2025-06-30 13:16:57,926 - INFO - Memory usage: 42.5% (0.39 GB allocated)
2025-06-30 13:16:58,435 - INFO - Memory usage: 42.8% (0.40 GB allocated)
2025-06-30 13:16:58,945 - INFO - Memory usage: 43.1% (0.41 GB allocated)
2025-06-30 13:16:59,455 - INFO - Memory usage: 43.4% (0.42 GB allocated)
...
2025-06-30 13:17:51,747 - INFO - Memory usage: 70.1% (1.42 GB allocated)
2025-06-30 13:17:52,248 - INFO - Target reached. Holding memory for 240 seconds...
2025-06-30 13:18:11,220 - WARNING - Memory stress test interrupted by user
2025-06-30 13:18:11,220 - INFO - Releasing 145 memory blocks...
2025-06-30 13:18:11,543 - INFO - Memory stress test completed. Final usage: 33.7%
```
