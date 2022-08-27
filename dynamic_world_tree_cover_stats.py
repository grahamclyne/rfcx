from geetools import tools
import pandas as pd 
import ee 
import geopandas as gpd
import plotly.express as px
import time 
from argparse import ArgumentParser
from utils import convert_3D_2D,convert_MultiPolygon_to_Polygon, get_whole_region,shp_to_ee_fmt

def get_region_data(region,start_date,end_date,time_interval) -> list:
    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start_date, end_date).filterBounds(region).select('label')
    #reduce data to time interval
    reduced = tools.imagecollection.reduceEqualInterval(
        dw,interval=1,unit=time_interval,reducer=ee.Reducer.mode(),
        start_date=ee.Date(args.start_date),end_date=ee.Date(args.end_date)
    ).select('label')

    #get pixel stats from each interval
    data = tools.imagecollection.getValues(
        collection=reduced,geometry=region,
        reducer=ee.Reducer.frequencyHistogram(),scale=10,maxPixels=1e8,side='client',bestEffort=True
    )
    new_dict = {}

    #select only the tree class
    for key,value in data.items():
        total_pixels = sum(value['label'].values())
        #'1' represents the "tree" class
        if('1' in value['label']):
            new_dict[key] = {'1':value['label']['1'] / total_pixels}
        else:
            new_dict[key] = {'1':0}
    dates = reduced.aggregate_array("reduced_to").getInfo()
    dates = list(map(lambda x : x.split('T')[0],dates))
    return list([new_dict,dates])



def convert_to_dataframe(regional_data) -> pd.DataFrame:
    data_points = []
    fin_data = []
    for data in regional_data:
        data_point = data[0]
        dates = data[1] 
        x = tools.imagecollection.data2pandas(data_point)
        x = x['1'].reset_index().fillna(0)
        x['timestamp'] = dates
        x['index'] = pd.to_numeric(x['index']).map(lambda x : x + 1) #adjust index to represent month clearly
        data_points.append(x)
        x = x.sort_values(by=['index'])
        fin_data.append(x)
    #create column to id each region
    for df_index in range(len(fin_data)):
        fin_data[df_index]['id'] = df_index
    #combine into one dataframe
    fin_df = pd.concat(fin_data)
    return fin_df



def plot_trend(geodf,start_date,end_date,file_name,time_interval) -> None:
    region = get_whole_region(geodf)
    regional_data = get_region_data(region,start_date,end_date,time_interval)       
    df = convert_to_dataframe([regional_data])
    fig = px.bar(df,x='index',y='1',title=f'{file_name} From {start_date} to {end_date}, {time_interval}',text=regional_data[1],labels={'index':time_interval + " (as of date indicated)",'1':'tree cover %'})
    fig.write_image(f'{file_name}_{start_date}_{end_date}_dynamic_world_{time_interval}_bar_plot.png')




#outputs csv of pixel stats over given timeframe
def pixel_stats_to_csv(geodf,start_date,end_date,file_name,time_interval) -> None:
    datas = []

    # for each feature in image, get monthly avg and get band values
    for index in range(len(geodf.geometry)):
        print(f'processing polygon {str(geodf.iloc[:,0][index]) + " " + str(geodf.iloc[:,1][index])}')
        region = ee.Geometry.Polygon(shp_to_ee_fmt(geodf,index))
        regional_data = get_region_data(region,start_date,end_date,time_interval)
        datas.append(regional_data)

    df = convert_to_dataframe(datas)

    #configure df for csv output
    df = df.groupby(['id','timestamp'])['1'].aggregate('first').unstack()
    df = df.reset_index()
    df['region'] = geodf.iloc[:,0].astype(str) + " " + geodf.iloc[:,0].astype(str)
    df.to_csv(f'{file_name}_{start_date}_{end_date}_dynamic_world_{time_interval}.csv')




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
    parser.add_argument("--time_interval",type=str) #needs to be either 'month' or 'year'
    args = parser.parse_args()
    file_name = args.shape_file.split('/')[-1].split('.')[0]


    # read each geometry of shapefile
    geodf = gpd.GeoDataFrame.from_file(args.shape_file)
    geodf = convert_3D_2D(geodf)
    geodf = convert_MultiPolygon_to_Polygon(geodf)
    plot_trend(geodf,args.start_date,args.end_date,file_name,args.time_interval)
    pixel_stats_to_csv(geodf,args.start_date,args.end_date,file_name,args.time_interval)
    print('runtime: %f seconds' % (time.time() - start_time))
