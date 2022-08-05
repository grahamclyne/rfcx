from util import add_ee_layer, shp_to_ee_fmt
from argparse import ArgumentParser
import folium
import ee
import seaborn
import geopandas as gpd
import json
import time 
import requests
import time 

def add_copernicus_layer(region,start,end):
    s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED').filterDate(start,end).filterBounds(region).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    s2Image = ee.Image(s2.mosaic())
    s2VisParams = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    my_map = folium.Map(location=[region.getInfo()['coordinates'][0][0][0][1],region.getInfo()['coordinates'][0][0][0][0]], zoom_start=13, height=500)
    my_map.add_ee_layer(s2Image, s2VisParams, 'sentinel-2 image')
    return my_map

def visualize_dynamic_world(region,start,end,file_name):
    my_map = add_copernicus_layer(region,start,end)
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start,end).filterBounds(region)
    dwImage = ee.Image(dw.mode()).clip(region)
    classification = dwImage.select('label')
    dwVisParams = {'min': 0,'max': 8,'palette': ['#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A','#C4281B', '#A59B8F', '#B39FE1']}
    my_map.add_ee_layer(classification, dwVisParams, 'Classified Image')
    my_map.save(file_name + '_dw.html')


def visualize_world_cover(region,start,end,file_name):
    my_map = add_copernicus_layer(region,start,end)
    wc = ee.ImageCollection("ESA/WorldCover/v100").first().clip(region)
    visualization = {'bands': ['Map']}
    my_map.add_ee_layer(wc, visualization, 'Classified Image')
    my_map.save(file_name + '_wc.html')


def save_geotiff(start_date,end_date,geometry):
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start_date,end_date).filterBounds(geometry)
    dwImage = ee.Image(dw.max()).clip(geometry).select('label')
    task = ee.batch.Export.image.toDrive(image= dwImage,description='imageToDriveExample_transform',scale=1,maxPixels=1e11,
    folder='output',region= geometry,fileFormat='GeoTIFF',fileNamePrefix='test')
    task.start()
    # # Multi-band GeoTIFF file.
    # url = dwImage.getDownloadUrl({
    #     'bands': ['trees'],
    #     'region': geometry,
    #     'scale': 1,
    #     'format': 'GEO_TIFF'
    # })
    # response = requests.get(url)
    # with open('multi_band.tif', 'wb') as fd:
    #     fd.write(response.content)
    
    while task.active():
        print('Polling for task (id: {}).'.format(task.id))
        print(task.status())
        time.sleep(5)

    print(task.status()) #how to check for errors....



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
    data = json.loads(shp_file.to_json())
    features = len(data['features'])
    region = None
    for feature_index in range(0,features):
        if(region == None):
            region = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,feature_index))
        else:
            geometry = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,feature_index))
            region = geometry.union(region)

    # print(geo.getInfo()['coordinates'][0][0][1])
    visualize_dynamic_world(region,start,end,file_name)
    visualize_world_cover(region,start,end,file_name)
    # save_geotiff(args.start_date,args.end_date,geo)
    print('runtime: %f seconds' % (time.time() - start_time))
    
