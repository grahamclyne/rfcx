import ee
import folium
import json
# Define a method for displaying Earth Engine image tiles on a folium map.

def shp_to_ee_fmt(geodf,index):
    data = json.loads(geodf.to_json())
    return data['features'][index]['geometry']['coordinates']



def get_whole_region(shp_file):
    data = json.loads(shp_file.to_json())
    features = len(data['features'])
    region = None
    for feature_index in range(0,features):
        if(region == None):
            region = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,feature_index))
        else:
            geometry = ee.Geometry.Polygon(shp_to_ee_fmt(shp_file,feature_index))
            region = geometry.union(region)
    return region
    
def add_ee_layer(self, ee_object, vis_params, name):
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
            ee_object_new = ee.Image().paint(ee_object, 0, 2)
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
