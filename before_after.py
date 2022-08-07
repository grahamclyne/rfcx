#want to determine tree cover change before/after

import geopandas as gpd
import json
import ee
import folium
from util import add_ee_layer, get_whole_region,
from argparse import ArgumentParser
import folium
import ee
import geopandas as gpd
import json
import time 
import requests
import time 



if __name__ == '__main__':
    try:     
        ee.Initialize() 
    except:
        ee.Authenticate()
        ee.Initialize()


    shp_file = gpd.read_file('/Users/gclyne/Downloads/rfcx_sensor_placement/Graham_Amazon/Bacajai_JP1.shp', crs='EPSG:4326')
    region = get_whole_region(shp_file)
    file_name = 'test'
    folium.Map.add_ee_layer = add_ee_layer    


    beforeYear = 2020;
    afterYear = 2021;
    beforeStart = ee.Date.fromYMD(beforeYear, 1, 1);
    beforeEnd = beforeStart.advance(1, 'year');

    afterStart = ee.Date.fromYMD(afterYear, 1, 1);
    afterEnd = afterStart.advance(1, 'year');

    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(region).select('trees')

    beforeDw = dw.filterDate(beforeStart, beforeEnd).mean()
    afterDw = dw.filterDate(afterStart, afterEnd).mean()
    new_tree = (beforeDw.lt(0.2)).And(afterDw.gt(0.5))
    my_map = folium.Map(location=[region.getInfo()['coordinates'][0][0][1],region.getInfo()['coordinates'][0][0][0]], zoom_start=13, height=500)
    
    changeVisParams = {'min': 0, 'max': 1, 'palette': ['white', 'red'],'opacity':0.5};
    my_map.add_ee_layer(new_tree.clip(region), changeVisParams, 'New Tree');
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate('2020-01-01','2021-01-01').filterBounds(region)
    dwImage = ee.Image(dw.mode()).clip(region).select('label')
    dwVisParams = {'min': 0,'max': 8,'palette': ['#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A','#C4281B', '#A59B8F', '#B39FE1']}

    my_map.add_ee_layer(dwImage, dwVisParams,'base layer')

    my_map.save('before_after_dw.html')