import math 
import elevatr
import pyproj
import numpy as np

def make_bounding_box(lat, long, size_km = 50):
    
    lat_offset = (size_km/2)/(111)
    long_offset = (size_km/2)/(111 * math.cos(math.radians(lat)))
    
    return { 
        "north" : lat + lat_offset,
        "south" : lat - lat_offset,
        "east" : long + long_offset,
        "west" : long - long_offset }
    
def is_in_colorado(lat,long):
    return(lat >= 36.99 and lat<=41.00 and long >= -109.05 and long <=-102.05)

def download_elevation(lat,long,size_km=50):
    if 1==1: #is_in_colorado(lat=lat, long = long):
        
        bounds = make_bounding_box(lat,long,size_km=50)
        bbox = (bounds["west"], bounds["south"], bounds["east"], bounds["north"])
        
        dataset = elevatr.get_elev_raster( locations=bbox, crs=pyproj.CRS.from_epsg(4326), zoom=12)
        
        return np.array(dataset.data).astype(np.float32)
    else:
        print("Not in CO")
        return None
    
if __name__ == "__main__":
    lat, lon = 44.4654, -72.6874
    elevation = download_elevation(lat, lon)
    print("Shape:", elevation.shape)
    print("Min:", elevation.min(), "Max:", elevation.max())