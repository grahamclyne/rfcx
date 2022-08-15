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
    # for index in range(3):
        print(f'processing image: {index}')
        # #get image of region
        region = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,index))
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(args.start_date, args.end_date).filterBounds(region).select('label')

       
        reduced = tools.imagecollection.reduceEqualInterval(dw,interval=1,unit='year',reducer=ee.Reducer.mode(),start_date=ee.Date(args.start_date),end_date=ee.Date(args.end_date)).select('label')
        data = tools.imagecollection.getValues(
        collection=reduced,
        geometry=region,
        reducer=ee.Reducer.frequencyHistogram(),
        scale=1,
        maxPixels=1e8,
        side='client',
        bestEffort=True)
        # print(data)
        new_dict = {}
        for key,value in data.items():
            print(key,value)
            sum = 0
            for val in value['label'].values():
                print(val)
                sum = sum + val
            if('1' in value['label']):
                new_dict[key] = {'1':value['label']['1'] / sum}
            else:
                new_dict[key] = {'1':0}
        # print(new_dict)
        datas.append(new_dict)


        # dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate('2020-01-01','2021-01-01').filterBounds(region)
        # dwImage = ee.Image(dw.mode()) #mode() returns most common pixel value
        # classification = dwImage.select('label').clip(region)
        # pixelCountStats = classification.reduceRegion(reducer=ee.Reducer.frequencyHistogram().unweighted(),geometry=region,bestEffort=True,maxPixels=1e8,scale=1)
        # print(pixelCountStats.get('label').getInfo())



    monthly_data_points = []
    fin_data = []

    #convert monthly image collection to pandas dataframe
    for data_point in datas: 
        print(data_point)
        x = tools.imagecollection.data2pandas(data_point)
        print(x)
        x = x['1']
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
    fin_df = fin_df.groupby(['id','index'])['1'].aggregate('first').unstack()
    fin_df.columns = ['2017','2018','2019','2020']

    fin_df = fin_df.reset_index()
    fig = px.bar(fin_df,x='id',y=['2017','2018','2019','2020'],barmode='group')
    fig.write_image('test_bar.png')
    fin_df.to_csv('yearly_test.csv')
    print('runtime: %f seconds' % (time.time() - start_time))
