import pandas as pd
import os

def get_traffic_data_stream(total_samples=20000):
    """
    Data loader for PeMS real-world traffic data(https://pems.dot.ca.gov/?dnode=Clearinghouse&type=station_5min&district_id=4&submit=Submit).
    Parses raw speed data and assigns descriptive traffic labels.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data", "d04_text_station_5min_2026_04_02.txt")

    stream = []
    try:
        # PeMS raw data has no header. Column 12 (index 11) is the average speed.
        df = pd.read_csv(file_path, header=None)
        
        # Convert speed column to numeric, coerce errors to NaN, and drop missing values.
        raw_speeds = pd.to_numeric(df[11], errors='coerce').dropna()
        
        for speed in raw_speeds:
            speed = float(speed)
            
            # Categorize traffic state based on speed thresholds for monitoring.
            if speed < 20:
                label = "Real: Congested"
            elif speed > 65:
                label = "Real: Free-Flow"
            else:
                label = "Real: Moderate"
                
            stream.append((speed, label))
            
            # Stop once the requested sample count is reached.
            if len(stream) >= total_samples:
                break
                
        return stream

    except Exception as e:
        print(f"Error loading real-world data: {e}")
        # Return empty list if file reading or parsing fails.
        return []


# Freeway IDs used to split real PeMS data into separate routes.
# Column 3 = freeway number, Column 5 = lane type (ML = mainline).
_ROUTE_FREEWAYS = [101, 580, 680]
_ROUTE_CACHE = {}


def _load_route_data():
    """Load and split the PeMS dataset by freeway once, then cache."""
    if _ROUTE_CACHE:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data", "d04_text_station_5min_2026_04_02.txt")

    try:
        df = pd.read_csv(file_path, header=None)

        # Column 3 = freeway number, Column 5 = lane type, Column 11 = avg speed
        df[3] = pd.to_numeric(df[3], errors="coerce")
        df[11] = pd.to_numeric(df[11], errors="coerce")

        # Keep only mainline (ML) rows with valid speed readings
        ml = df[(df[5] == "ML") & df[11].notna()].copy()

        for idx, fwy in enumerate(_ROUTE_FREEWAYS):
            subset = ml[ml[3] == fwy][11]
            stream = []
            for speed in subset:
                speed = float(speed)
                if speed < 20:
                    label = "Real: Congested"
                elif speed > 65:
                    label = "Real: Free-Flow"
                else:
                    label = "Real: Moderate"
                stream.append((speed, label))
            _ROUTE_CACHE[idx] = stream

    except Exception as e:
        print(f"Error loading route data: {e}")
        for idx in range(len(_ROUTE_FREEWAYS)):
            _ROUTE_CACHE[idx] = []


def get_route_traffic_stream(route_id, total_samples=600):
    """
    Return speed readings for a specific route (freeway) from the PeMS dataset.
    Route 0 = I-101, Route 1 = I-580, Route 2 = I-680.
    Returns the same (speed, label) tuple format as get_traffic_data_stream.
    """
    _load_route_data()

    stream = _ROUTE_CACHE.get(route_id, [])
    if not stream:
        return []

    # If we have more data than requested, return a slice.
    # If less, return everything we have.
    return stream[:total_samples]
