import random

def get_traffic_data_stream(total_samples=20000):
    """
    Data generator.
    Returns a list of simulated vehicle speeds based on different traffic phases.
    """

    # Simulation Stages: (Label, Mean Speed, Standard Deviation, Count)
    stages = [
        ("Off-Peak (Fast)", 72, 4, int(total_samples * 0.25)),      # High speed, low variance
        ("Accident/Congest", 18, 12, int(total_samples * 0.50)),   # Sharp drop, high variance
        ("Recovery Phase", 40, 6, int(total_samples * 0.25))        # Gradual speed increase
    ]

    stream = []
    for label, mu, sigma, n in stages:
        for _ in range(n):
            speed = max(3.0, random.gauss(mu, sigma))
            stream.append((speed, label))
    
    return stream
            
            
            