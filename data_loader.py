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
            
            
            