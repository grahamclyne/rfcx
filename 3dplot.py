import json
from geetools import tools
from util import shp_to_ee_fmt
import pandas as pd 
import ee 
import geopandas as gpd
import plotly.express as px
import time 
from constants import DW_BANDS
from argparse import ArgumentParser

# This script generates a 3d plot of all geometries of a shapefile. The region's images are aggregated to a monthly time scale, and plotted using plotly

if __name__ == '__main__':
    start_time = time.time()
    try:     
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()
    parser = ArgumentParser()
    parser.add_argument("--start_date", type=str)
    parser.add_argument("--end_date", type=str)
    parser.add_argument("--shape_file", type=str)
    args = parser.parse_args()
    file_name = args.shape_file.split('/')[-1].split('.')[0]


    # read each geometry of shapefile
    shp_file = gpd.read_file(args.shape_file, crs='EPSG:4326')
    datas = []
    data = json.loads(shp_file.to_json())

    #for each feature in image, get monthly avg and get band values
    for index in range(len(data['features'])):
        print(f'processing image: {index}')
        #get image of region
        region = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,index))
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(args.start_date, args.end_date).filterBounds(region);
        dwTimeSeries = dw.select(DW_BANDS)

        #aggregate to monthly time series using max reducer
        reduced = tools.imagecollection.reduceEqualInterval(dwTimeSeries,interval=1,unit='month',reducer='mode')
        data = tools.imagecollection.getValues(
        collection=reduced,
        geometry=region,
        reducer='max',
        scale=1,
        maxPixels=1e9,
        side='client',
        bestEffort=True)
        datas.append(data)


    monthly_data_points = []
    fin_data = []

    #convert monthly image collection to pandas dataframe
    for data_point in datas: 
        x = tools.imagecollection.data2pandas(data_point)
        x = x.reset_index()
        x = x.fillna(0)
        x['index'] = pd.to_numeric(x['index']).map(lambda x : x + 1) #adjust index to represent month clearly
        monthly_data_points.append(x)
        x = x.sort_values(by=['index'])
        fin_data.append(x)

    #create column to id each region
    for df_index in range(len(fin_data)):
        fin_data[df_index]['id'] = df_index

    #combine into one dataframe
    fin_df = pd.concat(fin_data)

    #melt dataframe for easy visualization
    fin_df_melted = pd.melt(fin_df,id_vars=['index','id'])
    
    #generate image with 
    fig = px.scatter_3d(fin_df_melted, x='index', y='id', z='value',
                color='variable', labels={
                        "index": "Month",
                        "id": "Guardian ID",
                        "value": "% of land cover"
                    },title='')
    fig.write_html( file_name + '3d.html')
    print('runtime: %f seconds' % (time.time() - start_time))
