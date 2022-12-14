import ee
import numpy as np
import folium
import geopandas as gpd
from collections import defaultdict
import matplotlib.pyplot as plt
from constants import DW_CLASSES,WC_CLASSES
from util import add_ee_layer,get_whole_region
from argparse import ArgumentParser
import time



def transform_normalize_dict(output):
    totals = np.empty(0)
    #convert pixel totals to single dictionary 
    dd = defaultdict(lambda: np.zeros(0))
    for d in (output): 
        totals = np.append(totals,sum(d.values()))
        for index in range(0,9): #0-8 for each class
            key = str(index)
            if(key not in d.keys()):
                dd[key] = np.append(dd[key],0)
            else:
                dd[key] = np.append(dd[key],d[key])
    #normalize
    for i in range(0,9):
        dd[str(i)] = dd[str(i)] / totals
    return dd




def pixel_stats_dynamic_world(region,start,end):
    output = []
    labels = []
    while(end.difference(start,'days').gt(0).getInfo()):
        temp_end = start.advance(1,'year')
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start,temp_end).filterBounds(region).select('label')
        dwImage = ee.Image(dw.mode()).clip(region) #mode() returns most common pixel value
        labels.append(start.format('YYYY').getInfo())
        classification = dwImage.select('label').clip(region)
        
        pixelCountStats = classification.reduceRegion(reducer=ee.Reducer.frequencyHistogram(),geometry=region,bestEffort=True,maxPixels=1e8,scale=10)
        pixelCounts = ee.Dictionary(pixelCountStats.get('label'));
        output.append(pixelCounts.getInfo())
        start = start.advance(1,'year')
    return (transform_normalize_dict(output),labels)




def add_bar_plot(values=[],width=0.1,label='unknown',index=0, ax=None,x=np.empty(0)):
    ax.bar(x + width*index,values,width,label=label)



def plot_multiple_bar_from_dict(data,labels,file_name,classes,datasource):
    fig, ax = plt.subplots()
    x = np.arange(len(labels))  # the label locations
    if(datasource == 'worldcover'):
        for key in data.keys():
            add_bar_plot(data[key],label=classes[key],index=int(key)/10,ax=ax,x=x)
    elif(datasource == 'dynamicworld'):
        for key in data.keys():
            add_bar_plot(data[key],label=classes[key],index=int(key),ax=ax,x=x)        
    elif(datasource == 'gfw'):
        for index in range(len(data)):
            add_bar_plot(data[index],index=index,ax=ax,x=x)
    ax.set_xticks(x, labels)
    # ax.set_yscale('log')
    ax.set_ylabel('% of land cover')
    ax.set_title('Land types in hulu batang hari')
    # fig.tight_layout()
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.savefig(file_name,bbox_inches='tight')
    

def pixel_stats_world_cover(region):
    dataset = ee.ImageCollection("ESA/WorldCover/v100").first().clip(region)
    pixelCountStats = dataset.reduceRegion(reducer=ee.Reducer.frequencyHistogram(),geometry=region,bestEffort=True,maxPixels=1e8,scale=10)
    output = pixelCountStats.getInfo()['Map']
    #normalize
    normalized_output = {}
    for key in output.keys():
        normalized_output[key] = output[key] / sum(output.values())
    return (normalized_output,[2020])




def pixel_stats_global_forest_watch(region,start,end):
    cc = ee.Number(10);
    gfc2021 = ee.Image('UMD/hansen/global_forest_change_2021_v1_9')
    canopyCover = gfc2021.select(['treecover2000'])
    canopyCover10 = canopyCover.gte(cc).selfMask()
    forestSize = canopyCover10.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= region,
        scale= 10,
        maxPixels= 1e9,
        bestEffort=True);

    forest_size = list(forestSize.getInfo().values())[0]

    treeLoss = gfc2021.select(['lossyear']);
    losses = []
    gfc2021.select(['gain']);
    for i in range(1,int(end.format('YY').getInfo())):
        print(f'calculating year {i}')
        treeLoss01 = treeLoss.eq(i).selfMask()
        treecoverLoss01 = canopyCover10.And(treeLoss01).rename('loss' + str(i)).selfMask();
        lossSize = treecoverLoss01.reduceRegion(
            reducer= ee.Reducer.sum(),
            geometry=region,
            scale= 10,
            maxPixels= 1e9,
            bestEffort=True
        )
        losses.append(list(lossSize.getInfo().values())[0])
        print(losses)
    gains = gfc2021.select(['gain'])
    # canopyCover10 = canopyCover.gte(ee.Number(10)).selfMask()
    gains_summed = gains.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= region,
        scale= 10,
        maxPixels= 1e9,
        bestEffort=True);

    lost = sum(losses) + gains_summed.getInfo()['gain']
    diff = (forest_size - lost) / forest_size
    return [diff]



if __name__ == "__main__":
    start_time = time.time()
    folium.Map.add_ee_layer = add_ee_layer    
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
    start = ee.Date(args.start_date);
    end = ee.Date(args.end_date)
    shp_file = gpd.read_file(args.shape_file,crs='EPSG:4326')
    region = get_whole_region(shp_file)
    
    dynamic_world_data,labels = pixel_stats_dynamic_world(region,start,end)
    print(dynamic_world_data)
    plot_multiple_bar_from_dict(dynamic_world_data,labels,file_name + 'dynamic_world.png',DW_CLASSES,'dynamicworld')
    
    # worldcover,labels = pixel_stats_world_cover(region)
    # plot_multiple_bar_from_dict(worldcover,labels,file_name + "_world_cover.png",WC_CLASSES,'worldcover')

    # gfc_data = pixel_stats_global_forest_watch(region,start,end)
    # print(gfc_data)
    # plot_multiple_bar_from_dict(gfc_data,[2020],file_name + '_gfw_data.png',DW_CLASSES,'gfw')
    # print('runtime: %f seconds' % (time.time() - start_time))