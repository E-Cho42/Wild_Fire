import math
import numpy as np

def make_bounding_box(center_lat, center_lon, size_km=10):
    lat_offset = (size_km / 2) / 111
    lon_offset = (size_km / 2) / (111 * math.cos(math.radians(center_lat)))
    
    return {
        "north": center_lat + lat_offset,
        "south": center_lat - lat_offset,
        "west":  center_lon - lon_offset,
        "east":  center_lon + lon_offset,
    }

def is_in_colorado(lat, lon):
    return 36.99 <= lat <= 41.00 and -109.05 <= lon <= -102.05

def load_data(center_lat, center_lon, size_km=10):
    pass

if __name__ == "__main__":
    lat, lon = 40.55, -105.65   # somewhere near Fort Collins
    
    if is_in_colorado(lat, lon):
        bounds = make_bounding_box(lat, lon, size_km=10)
        print(bounds)
    else:
        print("Not in Colorado!")

