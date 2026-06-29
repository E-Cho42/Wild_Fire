import math 
import elevatr
import pyproj
import numpy as np
import planetary_computer
import pystac_client
import rioxarray
from scipy.ndimage import zoom

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
        
        dataset = elevatr.get_elev_raster( locations=bbox, crs=pyproj.CRS.from_epsg(4326), zoom=10)
        
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
        
        
def align_landcover(landcover, elevation):
    zoomfactor_R = np.shape(elevation)[0] / np.shape(landcover)[0] 
    zoomfactor_C = np.shape(elevation)[1] / np.shape(landcover)[1] 
    return zoom(landcover, (zoomfactor_R, zoomfactor_C), order=0)

    
    
    
if __name__ == "__main__":
    lat, lon = 44.4654, -72.6874
    elevation = download_elevation(lat, lon)
    landcover = download_landcover(lat, lon)
    landcover_aligned = align_landcover(landcover, elevation)
    print("Elevation shape:", elevation.shape)
    print("Landcover aligned shape:", landcover_aligned.shape)
    print("Unique values:", np.unique(landcover_aligned))