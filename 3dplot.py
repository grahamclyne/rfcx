import json
from geetools import tools
from util import shp_to_ee_fmt
import pandas as pd 
import ee 
import geopandas as gpd
import plotly.express as px
import time 



if __name__ == '__main__':

    start_time = time.time()


    try:     
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()


    startDate = '2020-01-01';
    endDate = '2021-01-01';
    shape_file = '/Users/gclyne/Downloads/RFCx_GQ_Shapefiles/Hulu_Batang_Hari_sites_Buffer1k.shp'
    #shape_file = '/Users/gclyne/Downloads/RFCx_GQ_Shapefiles/Tembe_Reserve_sites_Buffer1k.shp'
    shp_file = gpd.read_file(shape_file, crs='EPSG:4326')
    probabilityBands = [
    'water', 'trees', 'grass', 'flooded_vegetation', 'crops', 'shrub_and_scrub',
    'built', 'bare', 'snow_and_ice'
    ]

    datas = []
    data = json.loads(shp_file.to_json())

    #for each feature in image, get monthly avg and get band values
    for index in range(len(data['features'])):
        print(index)
        region = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,index))
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(startDate, endDate).filterBounds(region);
        dwTimeSeries = dw.select(probabilityBands)

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


    arrays = []
    for data_point in datas: 
        x = tools.imagecollection.data2pandas(data_point)
        x = x.reset_index()
        x = x.dropna()
        x['index'] = pd.to_numeric(x['index'])
        arrays.append(x)

        fin_data = []
    for array in arrays:
        months = array['index'].tolist()
        for index in range(12):
            if(index in months):
                continue
            else: 
                array = array.append({'index':index},ignore_index=True)
        array=array.fillna(0)
        array = array.sort_values(by=['index'])
        fin_data.append(array)
    for df_index in range(len(fin_data)):
        fin_data[df_index]['id'] = df_index

    fin_df = pd.concat(fin_data)
    fin_df_melted = pd.melt(fin_df,id_vars=['index','id'])
    fin_df_melted['index'] = fin_df_melted['index'].map(lambda x : x + 1)
    file_name = shape_file.split('/')[-1].split('.')[0]

    df = px.data.iris()
    fig = px.scatter_3d(fin_df_melted, x='index', y='id', z='value',
                color='variable', labels={
                        "index": "Month",
                        "id": "Guardian ID",
                        "value": "% of land cover"
                    },title='')
    fig.show()
    fig.write_html( file_name + '3d.html')
    print('runtime: %f seconds' % (time.time() - start_time))
