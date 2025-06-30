# To run the cpu_stress_with_logging.py run this - 
- sudo python3 cpu_stress_with_logging.py <time in seconds for running it> <Number of cores you want to stress>
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
- sudo python3 memory_stress_with_logging.py <How much percent of memory to stress>  <Time in seconds until it runs>
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
2025-06-30 13:16:59,971 - INFO - Memory usage: 43.6% (0.43 GB allocated)
2025-06-30 13:17:00,491 - INFO - Memory usage: 43.8% (0.44 GB allocated)
2025-06-30 13:17:01,000 - INFO - Memory usage: 44.0% (0.45 GB allocated)
2025-06-30 13:17:01,523 - INFO - Memory usage: 44.5% (0.46 GB allocated)
2025-06-30 13:17:02,039 - INFO - Memory usage: 44.5% (0.47 GB allocated)
2025-06-30 13:17:02,552 - INFO - Memory usage: 44.9% (0.48 GB allocated)
2025-06-30 13:17:03,062 - INFO - Memory usage: 45.2% (0.49 GB allocated)
2025-06-30 13:17:03,574 - INFO - Memory usage: 45.6% (0.50 GB allocated)
2025-06-30 13:17:04,083 - INFO - Memory usage: 45.8% (0.51 GB allocated)
2025-06-30 13:17:04,592 - INFO - Memory usage: 46.0% (0.52 GB allocated)
2025-06-30 13:17:05,101 - INFO - Memory usage: 46.2% (0.53 GB allocated)
2025-06-30 13:17:05,611 - INFO - Memory usage: 46.6% (0.54 GB allocated)
2025-06-30 13:17:06,121 - INFO - Memory usage: 46.8% (0.55 GB allocated)
2025-06-30 13:17:06,635 - INFO - Memory usage: 46.9% (0.56 GB allocated)
2025-06-30 13:17:07,144 - INFO - Memory usage: 47.4% (0.57 GB allocated)
2025-06-30 13:17:07,655 - INFO - Memory usage: 47.6% (0.58 GB allocated)
2025-06-30 13:17:08,170 - INFO - Memory usage: 47.7% (0.59 GB allocated)
2025-06-30 13:17:08,686 - INFO - Memory usage: 48.2% (0.60 GB allocated)
2025-06-30 13:17:09,199 - INFO - Memory usage: 48.2% (0.61 GB allocated)
2025-06-30 13:17:09,711 - INFO - Memory usage: 48.5% (0.62 GB allocated)
2025-06-30 13:17:10,227 - INFO - Memory usage: 48.9% (0.62 GB allocated)
2025-06-30 13:17:10,738 - INFO - Memory usage: 49.1% (0.63 GB allocated)
2025-06-30 13:17:11,248 - INFO - Memory usage: 49.5% (0.64 GB allocated)
2025-06-30 13:17:11,758 - INFO - Memory usage: 49.7% (0.65 GB allocated)
2025-06-30 13:17:12,267 - INFO - Memory usage: 50.0% (0.66 GB allocated)
2025-06-30 13:17:12,778 - INFO - Memory usage: 50.4% (0.67 GB allocated)
2025-06-30 13:17:13,288 - INFO - Memory usage: 50.5% (0.68 GB allocated)
2025-06-30 13:17:13,798 - INFO - Memory usage: 50.8% (0.69 GB allocated)
2025-06-30 13:17:14,308 - INFO - Memory usage: 51.0% (0.70 GB allocated)
2025-06-30 13:17:14,821 - INFO - Memory usage: 51.2% (0.71 GB allocated)
2025-06-30 13:17:15,330 - INFO - Memory usage: 51.6% (0.72 GB allocated)
2025-06-30 13:17:15,839 - INFO - Memory usage: 51.8% (0.73 GB allocated)
2025-06-30 13:17:16,348 - INFO - Memory usage: 52.0% (0.74 GB allocated)
2025-06-30 13:17:16,860 - INFO - Memory usage: 52.4% (0.75 GB allocated)
2025-06-30 13:17:17,371 - INFO - Memory usage: 52.4% (0.76 GB allocated)
2025-06-30 13:17:17,882 - INFO - Memory usage: 52.8% (0.77 GB allocated)
2025-06-30 13:17:18,397 - INFO - Memory usage: 53.0% (0.78 GB allocated)
2025-06-30 13:17:18,910 - INFO - Memory usage: 53.2% (0.79 GB allocated)
2025-06-30 13:17:19,422 - INFO - Memory usage: 53.6% (0.80 GB allocated)
2025-06-30 13:17:19,937 - INFO - Memory usage: 53.8% (0.81 GB allocated)
2025-06-30 13:17:20,446 - INFO - Memory usage: 54.0% (0.82 GB allocated)
2025-06-30 13:17:20,961 - INFO - Memory usage: 54.1% (0.83 GB allocated)
2025-06-30 13:17:21,471 - INFO - Memory usage: 54.5% (0.84 GB allocated)
2025-06-30 13:17:21,988 - INFO - Memory usage: 54.7% (0.85 GB allocated)
2025-06-30 13:17:22,501 - INFO - Memory usage: 54.9% (0.86 GB allocated)
2025-06-30 13:17:23,012 - INFO - Memory usage: 55.3% (0.87 GB allocated)
2025-06-30 13:17:23,521 - INFO - Memory usage: 55.5% (0.88 GB allocated)
2025-06-30 13:17:24,035 - INFO - Memory usage: 55.9% (0.89 GB allocated)
2025-06-30 13:17:24,547 - INFO - Memory usage: 56.3% (0.90 GB allocated)
2025-06-30 13:17:25,057 - INFO - Memory usage: 56.5% (0.91 GB allocated)
2025-06-30 13:17:25,568 - INFO - Memory usage: 56.7% (0.92 GB allocated)
2025-06-30 13:17:26,086 - INFO - Memory usage: 56.9% (0.93 GB allocated)
2025-06-30 13:17:26,597 - INFO - Memory usage: 57.1% (0.94 GB allocated)
2025-06-30 13:17:27,108 - INFO - Memory usage: 57.5% (0.95 GB allocated)
2025-06-30 13:17:27,624 - INFO - Memory usage: 57.6% (0.96 GB allocated)
2025-06-30 13:17:28,136 - INFO - Memory usage: 58.0% (0.97 GB allocated)
2025-06-30 13:17:28,647 - INFO - Memory usage: 58.6% (0.98 GB allocated)
2025-06-30 13:17:29,156 - INFO - Memory usage: 58.8% (0.99 GB allocated)
2025-06-30 13:17:29,667 - INFO - Memory usage: 59.2% (1.00 GB allocated)
2025-06-30 13:17:30,176 - INFO - Memory usage: 59.3% (1.01 GB allocated)
2025-06-30 13:17:30,691 - INFO - Memory usage: 59.6% (1.02 GB allocated)
2025-06-30 13:17:31,206 - INFO - Memory usage: 59.8% (1.03 GB allocated)
2025-06-30 13:17:31,719 - INFO - Memory usage: 60.2% (1.04 GB allocated)
2025-06-30 13:17:32,235 - INFO - Memory usage: 60.3% (1.04 GB allocated)
2025-06-30 13:17:32,750 - INFO - Memory usage: 60.7% (1.05 GB allocated)
2025-06-30 13:17:33,261 - INFO - Memory usage: 60.9% (1.06 GB allocated)
2025-06-30 13:17:33,771 - INFO - Memory usage: 61.2% (1.07 GB allocated)
2025-06-30 13:17:34,282 - INFO - Memory usage: 61.4% (1.08 GB allocated)
2025-06-30 13:17:34,801 - INFO - Memory usage: 61.8% (1.09 GB allocated)
2025-06-30 13:17:35,312 - INFO - Memory usage: 62.0% (1.10 GB allocated)
2025-06-30 13:17:35,829 - INFO - Memory usage: 62.2% (1.11 GB allocated)
2025-06-30 13:17:36,337 - INFO - Memory usage: 62.4% (1.12 GB allocated)
2025-06-30 13:17:36,860 - INFO - Memory usage: 62.7% (1.13 GB allocated)
2025-06-30 13:17:37,370 - INFO - Memory usage: 62.8% (1.14 GB allocated)
2025-06-30 13:17:37,884 - INFO - Memory usage: 63.1% (1.15 GB allocated)
2025-06-30 13:17:38,397 - INFO - Memory usage: 63.4% (1.16 GB allocated)
2025-06-30 13:17:38,914 - INFO - Memory usage: 63.5% (1.17 GB allocated)
2025-06-30 13:17:39,425 - INFO - Memory usage: 63.9% (1.18 GB allocated)
2025-06-30 13:17:39,948 - INFO - Memory usage: 63.8% (1.19 GB allocated)
2025-06-30 13:17:40,458 - INFO - Memory usage: 64.1% (1.20 GB allocated)
2025-06-30 13:17:40,967 - INFO - Memory usage: 64.5% (1.21 GB allocated)
2025-06-30 13:17:41,476 - INFO - Memory usage: 64.7% (1.22 GB allocated)
2025-06-30 13:17:41,986 - INFO - Memory usage: 64.9% (1.23 GB allocated)
2025-06-30 13:17:42,499 - INFO - Memory usage: 65.1% (1.24 GB allocated)
2025-06-30 13:17:43,009 - INFO - Memory usage: 65.5% (1.25 GB allocated)
2025-06-30 13:17:43,522 - INFO - Memory usage: 65.9% (1.26 GB allocated)
2025-06-30 13:17:44,038 - INFO - Memory usage: 66.0% (1.27 GB allocated)
2025-06-30 13:17:44,552 - INFO - Memory usage: 66.2% (1.28 GB allocated)
2025-06-30 13:17:45,070 - INFO - Memory usage: 66.4% (1.29 GB allocated)
2025-06-30 13:17:45,580 - INFO - Memory usage: 66.7% (1.30 GB allocated)
2025-06-30 13:17:46,094 - INFO - Memory usage: 66.9% (1.31 GB allocated)
2025-06-30 13:17:46,611 - INFO - Memory usage: 67.3% (1.32 GB allocated)
2025-06-30 13:17:47,125 - INFO - Memory usage: 67.5% (1.33 GB allocated)
2025-06-30 13:17:47,637 - INFO - Memory usage: 67.9% (1.34 GB allocated)
2025-06-30 13:17:48,147 - INFO - Memory usage: 68.1% (1.35 GB allocated)
2025-06-30 13:17:48,660 - INFO - Memory usage: 68.5% (1.36 GB allocated)
2025-06-30 13:17:49,183 - INFO - Memory usage: 68.7% (1.37 GB allocated)
2025-06-30 13:17:49,693 - INFO - Memory usage: 69.0% (1.38 GB allocated)
2025-06-30 13:17:50,205 - INFO - Memory usage: 69.2% (1.39 GB allocated)
2025-06-30 13:17:50,719 - INFO - Memory usage: 69.6% (1.40 GB allocated)
2025-06-30 13:17:51,231 - INFO - Memory usage: 69.9% (1.41 GB allocated)
2025-06-30 13:17:51,747 - INFO - Memory usage: 70.1% (1.42 GB allocated)
2025-06-30 13:17:52,248 - INFO - Target reached. Holding memory for 240 seconds...
2025-06-30 13:18:11,220 - WARNING - Memory stress test interrupted by user
2025-06-30 13:18:11,220 - INFO - Releasing 145 memory blocks...
2025-06-30 13:18:11,543 - INFO - Memory stress test completed. Final usage: 33.7%
```
