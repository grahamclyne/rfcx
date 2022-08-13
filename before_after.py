

from util import add_ee_layer, get_whole_region
from argparse import ArgumentParser
import folium
import ee
import geopandas as gpd
import json
import time 
import time 
from argparse import ArgumentParser

"""
This script determines tree cover change before/after a specified time period
--start_period: the first date of the year to compare before
--end_period: the first date of the year to compare after
"""


if __name__ == '__main__':
    start_time = time.time()

    try:     
        ee.Initialize() 
    except:
        ee.Authenticate()
        ee.Initialize()

    parser = ArgumentParser()
    parser.add_argument("--start_period", type=str)
    parser.add_argument("--end_period", type=str)
    parser.add_argument("--shape_file", type=str)
    args = parser.parse_args()
    shp_file = gpd.read_file(args.shape_file,crs='EPSG:4326')
    region = get_whole_region(shp_file)
    folium.Map.add_ee_layer = add_ee_layer    
    file_name = args.shape_file.split('/')[-1].split('.')[0]


    #create time periods
    before_start = ee.Date(args.start_period)
    before_end = before_start.advance(1, 'year')
    after_start = ee.Date(args.end_period)
    after_end = after_start.advance(1, 'year')

    #get tree band from DW images and filter for date
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(region)
    beforeDw = dw.select('trees').filterDate(before_start, before_end).mode()
    afterDw = dw.select('trees').filterDate(after_start, after_end).mode()

    # get regions that are probably new deforestations
    new_tree = (beforeDw.gt(0.7)).And(afterDw.lt(0.2))
    my_map = folium.Map(location=[shp_file.geometry[0].exterior.coords.xy[1][0],shp_file.geometry[0].exterior.coords.xy[0][0]], zoom_start=13, height=500)
    change_vis_params = {'min': 0, 'max': 1, 'palette': ['white', 'red'],'opacity':0.5}
    my_map.add_ee_layer(new_tree.clip(region), change_vis_params, 'New Tree')

    #get mode reduction
    dw_vis_params = {'min': 0,'max': 8,'palette': ['#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A','#C4281B', '#A59B8F', '#B39FE1']}
    my_map.add_ee_layer(dw.select('label').filterDate(before_start,before_end).mode(), dw_vis_params,'base layer')

    my_map.save(file_name + 'before_after_dw.html')
    print('runtime: %f seconds' % (time.time() - start_time))
