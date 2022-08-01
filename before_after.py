#want to determine tree cover change before/after

import geopandas as gpd
import json
import ee
import folium
from util import add_ee_layer, get_whole_region
from argparse import ArgumentParser
import folium
import ee
import seaborn
import geopandas as gpd
import json
import time 
import requests
from pydrive.drive import GoogleDrive
import time 





if __name__ == "__main__":
    start_time = time.time()
    parser = ArgumentParser()
    parser.add_argument("--before_date", type=str)
    parser.add_argument("--after_date", type=str)
    parser.add_argument("--shape_file", type=str)
    folium.Map.add_ee_layer = add_ee_layer    

    args = parser.parse_args()
    seaborn.set()
    folium.Map.add_ee_layer = add_ee_layer    
    try:     
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()


    shp_file = gpd.read_file('/home/graham/Downloads/Bacajai_JP1.shp', crs='EPSG:4326')
    region = get_whole_region(shp_file)

    file_name = 'test'
    my_map = folium.Map(location=[region['coordinates'][0][0][1],region['coordinates'][0][0][0]], zoom_start=13, height=500)


    beforeStart = ee.Date.fromYMD(args.before_date)
    beforeEnd = beforeStart.advance(1, 'year')

    afterStart = ee.Date.fromYMD(args.after_date)
    afterEnd = afterStart.advance(1, 'year')

    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(region).select('trees')

    beforeDw = dw.filterDate(beforeStart, beforeEnd).mean()
    afterDw = dw.filterDate(afterStart, afterEnd).mean()

    newUrban = (beforeDw.lt(0.2)).And(afterDw.gt(0.5))
    my_map = folium.Map(location=[region.getInfo()['coordinates'][0][0][1],region.getInfo()['coordinates'][0][0][0]], zoom_start=13, height=500)

    changeVisParams = {'min': 0, 'max': 1, 'palette': ['white', 'red'],'opacity':0.5}
    my_map.add_ee_layer(newUrban.clip(region), changeVisParams, 'Forest Cover Change')

    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate('2019','2020').filterBounds(region)
    dwImage = ee.Image(dw.mode()).clip(region)
    classification = dwImage.select('label')
    dwVisParams = {'min': 0,'max': 8,'palette': ['#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A','#C4281B', '#A59B8F', '#B39FE1'],'opacity':0.5}
    my_map.add_ee_layer(classification, dwVisParams, 'Classified Image');
    my_map.save(file_name + '_before_after.html')