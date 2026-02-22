'''synthetic data generator'''

import random
import datetime

def generate_synthetic_observations(n: int = 100):
    """
    Generate synthetic air pollution observations.
    
    Each observation includes:
      - timestamp (datetime)
      - location (city name)
      - PM2.5, PM10, NO2, CO, O3 levels
      - air_quality_index (derived from pollutants)
    """

    cities = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bangalore", "Hyderabad"]
    data = []

    for _ in range(n):
        city = random.choice(cities)
        timestamp = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(0, 10000))
        
        pm25 = round(random.uniform(10, 200), 2)
        pm10 = round(random.uniform(20, 300), 2)
        no2 = round(random.uniform(5, 150), 2)
        co = round(random.uniform(0.1, 3.0), 2)
        o3 = round(random.uniform(10, 180), 2)

        # Simple derived AQI (placeholder logic)
        aqi = round((pm25 * 0.5 + pm10 * 0.3 + no2 * 0.1 + co * 10 + o3 * 0.1) / 2, 2)

        data.append({
            "timestamp": timestamp.isoformat(),
            "city": city,
            "PM2.5": pm25,
            "PM10": pm10,
            "NO2": no2,
            "CO": co,
            "O3": o3,
            "air_quality_index": aqi
        })

    return data


if __name__ == "__main__":
    # Example preview
    sample = generate_synthetic_observations(5)
    for entry in sample:
        print(entry)
