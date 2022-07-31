#want to determine tree cover change before/after

import geopandas as gpd
import json
import ee
from util import add_ee_layer,shp_to_ee_fmt
import folium


try:     
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()


shp_file = gpd.read_file('/home/graham/Downloads/Bacajai_JP1.shp', crs='EPSG:4326')

geometry = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,0))


# Add EE drawing method to folium.
file_name = 'test'
folium.Map.add_ee_layer = add_ee_layer    
my_map = folium.Map(location=[geometry['coordinates'][0][0][1],geometry['coordinates'][0][0][0]], zoom_start=13, height=500)
my_map.add_ee_layer(geometry, {'color':'red'}, 'Selected Location')
my_map.save(file_name + '_before_after.html')


beforeYear = 2020;
afterYear = 2021;
beforeStart = ee.Date.fromYMD(beforeYear, 1, 1);
beforeEnd = beforeStart.advance(1, 'year');

afterStart = ee.Date.fromYMD(afterYear, 1, 1);
afterEnd = afterStart.advance(1, 'year');

dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(geometry).select('trees')

beforeDw = dw.filterDate(beforeStart, beforeEnd).mean()
afterDw = dw.filterDate(afterStart, afterEnd).mean()
newUrban = (beforeDw.lt(0.2)).And(afterDw.gt(0.5))
my_map = folium.Map(location=[geometry.getInfo()['coordinates'][0][0][1],geometry.getInfo()['coordinates'][0][0][0]], zoom_start=13, height=500)

changeVisParams = {'min': 0, 'max': 1, 'palette': ['white', 'red']};
# my_map.add_ee_layer(newUrban.clip(geometry), changeVisParams, 'New Urban');

s2 = ee.ImageCollection('COPERNICUS/S2').filterBounds(geometry).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 35));

beforeS2 = s2.filterDate(beforeStart, beforeEnd).median();
afterS2 = s2.filterDate(afterStart, afterEnd).median();

s2VisParams = {'bands': ['B4', 'B3', 'B2'], min: 0, max: 3000};
#my_map.add_ee_layer(beforeS2.clip(geometry), s2VisParams, 'Before S2');
# my_map.add_ee_layer(afterS2.clip(geometry), s2VisParams, 'After S2');

print(newUrban.getInfo())
my_map.add_ee_layer(newUrban, {'color':'red'}, 'Selected Location')
