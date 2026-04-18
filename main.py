import time
from TrafficStream import TrafficStream
import data_loader

def main():
    window_size = 1000
    monitor = TrafficStream(window_size=window_size)
    
    # Fetch processed data from the real-world dataset.
    raw_stream = data_loader.get_traffic_data_stream(20000)
    total_samples = len(raw_stream)
    
    if total_samples == 0:
        print("No data loaded. Check your data file path.")
        return
    
    print(f"--- Starting Analysis (N={total_samples}, Window={window_size}) ---")
    start_time = time.time()
    
    header = f"{'Index':<8} | {'Traffic Status':<18} | {'P15':<6} | {'P50':<6} | {'P85':<6}"
    print(header)
    print("-" * len(header))

    for i, (speed, label) in enumerate(raw_stream):
        monitor.add_number(speed)
        
        if (i + 1) % 1000 == 0:
            print(f"{i+1:<8} | {label:<18} | {monitor.get_p15():<6.1f} | {monitor.get_p50():<6.1f} | {monitor.get_p85():<6.1f}")
        
    duration = time.time() - start_time
    print("-" * len(header))
    print(f"Performance Analysis:")
    print(f" - Processing Time: {duration:.4f}s")
    print(f" - Throughput: {int(total_samples / duration)} vehicles/sec")
    

if __name__ == "__main__":
    main()
