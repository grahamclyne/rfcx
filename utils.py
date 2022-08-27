import ee
import folium
import json
from shapely.geometry import Polygon, MultiPolygon
from geopandas import GeoDataFrame



#case where shapefile is 3d, convert to 2d
def convert_3D_2D(geodf:GeoDataFrame) -> GeoDataFrame:
    new_geo = []
    for p in geodf.geometry:
        if p.geom_type == 'Polygon':
            lines = [xy[:2] for xy in list(p.exterior.coords)]
            new_p = Polygon(lines)
            new_geo.append(new_p)
        elif p.geom_type == 'MultiPolygon':
            new_multi_p = []
            for ap in p.geoms:
                lines = [xy[:2] for xy in list(ap.exterior.coords)]
                new_p = Polygon(lines)
                new_multi_p.append(new_p)
            new_geo.append(MultiPolygon(new_multi_p))
    geodf.geometry = new_geo
    return geodf



#if file contains multipolygon, need to conver to polygon for gee. need to explode multipolygon in case of non-overlapping multipolygon
def convert_MultiPolygon_to_Polygon(geodf:GeoDataFrame) -> GeoDataFrame:
    for p in geodf.geometry:
        if p.geom_type == 'MultiPolygon':
           return geodf.explode(index_parts=True).reset_index().drop(columns='level_0')
    return geodf


#convert shapefile to list format for gee
def shp_to_ee_fmt(geodf: GeoDataFrame,index: int) -> list:
    data = json.loads(geodf.to_json())
    fin_data = data['features'][index]['geometry']['coordinates']
    return fin_data


def get_whole_region(geodf:GeoDataFrame ) -> ee.Geometry.Polygon:
    data = json.loads(geodf.to_json())
    features = len(data['features'])
    region = None
    for feature_index in range(0,features):
        if(region == None):
            region = ee.Geometry.Polygon(shp_to_ee_fmt(geodf,feature_index))
        else:
            geometry = ee.Geometry.Polygon(shp_to_ee_fmt(geodf,feature_index))
            region = geometry.union(region)
    return region
    
# Define a method for displaying Earth Engine image tiles on a folium map.
def add_ee_layer(self, ee_object, vis_params, name) -> None:
    try:    
        # display ee.Image()
        if isinstance(ee_object, ee.image.Image):  
            map_id_dict = ee.Image(ee_object).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
            ).add_to(self)
        # display ee.ImageCollection()
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):    
            print("ic here")
            ee_object_new = ee_object.mosaic()
            map_id_dict = ee.Image(ee_object_new).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
            ).add_to(self)
        # display ee.Geometry()
        elif isinstance(ee_object, ee.geometry.Geometry):    
            folium.GeoJson(
            data = ee_object.getInfo(),
            name = name,
            overlay = True,
            control = True
        ).add_to(self)
        # display ee.FeatureCollection()
        elif isinstance(ee_object, ee.featurecollection.FeatureCollection):  
            ee_object_new = ee.Image().paint(ee_object, 0, 1)
            map_id_dict = ee.Image(ee_object_new).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
        ).add_to(self)
    
    except:
        print("Could not display {}".format(name))