import random
import time
from MedianStream import TrafficStream

def run_traffic_pressure_test():
    """
    Performs a large-scale simulation (N=20,000) to test the 
    Four-Heap Traffic Monitoring System.
    """
    monitor = TrafficStream()
    total_samples = 20000
    
    print(f"--- Starting Large-Scale Traffic Simulation (N={total_samples}) ---")
    start_time = time.time()

    # Simulation Stages: (Label, Mean Speed, Standard Deviation, Count)
    stages = [
        ("Off-Peak (Fast)", 72, 4, 5000),      # High speed, low variance
        ("Accident/Congest", 18, 12, 10000),   # Sharp drop, high variance
        ("Recovery Phase", 40, 6, 5000)        # Gradual speed increase
    ]
    
    processed = 0
    
    header = f"{'Index':<8} | {'Traffic Status':<18} | {'P15':<6} | {'P50 (Med)':<10} | {'P85':<6}"
    print(header)
    print("-" * len(header))

    for label, mu, sigma, n in stages:
        for _ in range(n):
            speed = max(3.0, random.gauss(mu, sigma))
            
            monitor.add_speed(speed)
            processed += 1
            
            # Snapshot every 4000 entries to show convergence/shift
            if processed % 4000 == 0:
                print(f"{processed:<8} | {label:<18} | {monitor.get_p15():<6.1f} | {monitor.get_p50():<10.1f} | {monitor.get_p85():<6.1f}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("-" * len(header))
    print(f"Simulation Analysis:")
    print(f" - Total Time: {duration:.4f} seconds")
    print(f" - System Throughput: {int(total_samples / duration)} vehicles/sec")
    print(f" - Status: On track for Week 2 milestones[cite: 58, 59].")

if __name__ == "__main__":
    run_traffic_pressure_test()