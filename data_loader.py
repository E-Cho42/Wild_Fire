import math 
import elevatr
import pyproj
import numpy as np
import planetary_computer
import pystac_client
import rioxarray

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
    
    
def download_landcover(lat, long , size_km = 50):
    
    bounds = make_bounding_box(lat, long, size_km)
    catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
    )
    search = catalog.search(
    collections=["esa-worldcover"],
    bbox=[bounds["west"], bounds["south"], bounds["east"], bounds["north"]]
    )

    items = list(search.items())  
    
    item = items[0]
    data = rioxarray.open_rasterio(item.assets["map"].href) 
    
    data = data.rio.clip_box(
    minx=bounds["west"],
    miny=bounds["south"],
    maxx=bounds["east"],
    maxy=bounds["north"]
    ) 
    
    result = np.array(data.data).astype(np.float32)
    return np.squeeze(result)
        
if __name__ == "__main__":
    lat, lon = 44.4654, -72.6874
    landcover = download_landcover(lat, lon)
    print("Landcover shape:", landcover.shape)
    print("Unique values:", np.unique(landcover))