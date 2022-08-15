from util import add_ee_layer, get_whole_region
from argparse import ArgumentParser
import folium
import ee
import geopandas as gpd
import time 

#visualize layers of dynamic world and world cover based on time frame specified by user 


#add sentinel-2 base layer underneath land-cover classification
def add_copernicus_layer(region,start,end):
    s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED').filterDate(start,end).filterBounds(region).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    s2Image = ee.Image(s2.mosaic())
    s2VisParams = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    my_map = folium.Map(location=[region.getInfo()['coordinates'][0][0][0][1],region.getInfo()['coordinates'][0][0][0][0]], zoom_start=13, height=500)
    my_map.add_ee_layer(s2Image, s2VisParams, 'sentinel-2 image')
    return my_map


#add dw land-cover layer using mode reduction
def visualize_dynamic_world(region,start,end,file_name):
    my_map = add_copernicus_layer(region,start,end)
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start,end).filterBounds(region)
    dwImage = ee.Image(dw.mode()).clip(region) #here we use mode reduction, takes the most common pixel value over time period
    classification = dwImage.select('label')
    dwVisParams = {'min': 0,'max': 8,'palette': ['#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A','#C4281B', '#A59B8F', '#B39FE1']}
    my_map.add_ee_layer(classification, dwVisParams, 'Classified Image')
    my_map.save(file_name + '_dw.html')

#add wc land-cover layer, no reduction needed as there is only one time period available
def visualize_world_cover(region,start,end,file_name):
    my_map = add_copernicus_layer(region,start,end)
    wc = ee.ImageCollection("ESA/WorldCover/v100").first().clip(region)
    visualization = {'bands': ['Map']}
    my_map.add_ee_layer(wc, visualization, 'Classified Image')
    my_map.save(file_name + '_wc.html')

#this function saves the dw layer as a geotiff to a google drive account that is used to register
def save_dw_geotiff(region,start_date,end_date):
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start_date,end_date).filterBounds(region)
    dwImage = ee.Image(dw.max()).clip(region).select('label')
    task = ee.batch.Export.image.toDrive(image= dwImage,description='test',scale=1,maxPixels=1e11,folder='output',region= region,fileFormat='GeoTIFF',fileNamePrefix='export_dw_',crs='epsg:4326')
    task.start()
    while task.active():
        print('Polling for task (id: {}).'.format(task.id))
        print(task.status())
        time.sleep(5)

    print(task.status()) #this is how to check for problems ie failing tasks etc, can also log onto https://code.earthengine.google.com/ to see current tasks and completed tasks


if __name__ == "__main__":
    start_time = time.time()
    parser = ArgumentParser()
    parser.add_argument("--start_date", type=str)
    parser.add_argument("--end_date", type=str)
    parser.add_argument("--shape_file", type=str)

    args = parser.parse_args()
    folium.Map.add_ee_layer = add_ee_layer    
    try:     
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()
    file_name = args.shape_file.split('/')[-1].split('.')[0]
    start = ee.Date(args.start_date);
    end = ee.Date(args.end_date)
    shp_file = gpd.read_file(args.shape_file,crs='EPSG:4326')
    region = get_whole_region(shp_file)
    
    visualize_dynamic_world(region,start,end,file_name)
    visualize_world_cover(region,start,end,file_name)
    print('runtime: %f seconds' % (time.time() - start_time))
    
