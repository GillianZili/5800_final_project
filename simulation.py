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


def get_route_traffic_stream(route_id, total_samples=600):
    """
    Generate traffic data for a specific route with staggered congestion patterns.
    Uses the same gaussian generation approach as get_traffic_data_stream,
    but each route has a different congestion timing so that the recommended
    route shifts over time.

    Route 0 (Highway 101):    Congests early   -> recovers mid-run
    Route 1 (Route 280):      Free-flowing first -> congests in the middle
    Route 2 (El Camino Real): Moderate start    -> stays moderate, best late-game
    """

    if route_id == 0:
        stages = [
            ("Off-Peak (Fast)", 70, 4, int(total_samples * 0.15)),
            ("Accident/Congest", 16, 10, int(total_samples * 0.40)),
            ("Recovery Phase", 42, 6, int(total_samples * 0.20)),
            ("Off-Peak (Fast)", 68, 5, int(total_samples * 0.25)),
        ]
    elif route_id == 1:
        stages = [
            ("Off-Peak (Fast)", 65, 5, int(total_samples * 0.35)),
            ("Accident/Congest", 20, 12, int(total_samples * 0.40)),
            ("Recovery Phase", 38, 7, int(total_samples * 0.25)),
        ]
    else:
        stages = [
            ("Moderate Flow", 45, 6, int(total_samples * 0.25)),
            ("Moderate Flow", 50, 5, int(total_samples * 0.35)),
            ("Off-Peak (Fast)", 62, 4, int(total_samples * 0.40)),
        ]

    stream = []
    for label, mu, sigma, n in stages:
        for _ in range(n):
            speed = max(3.0, random.gauss(mu, sigma))
            stream.append((speed, label))

    return stream
