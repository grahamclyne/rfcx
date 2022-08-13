import ee
import folium
import json

def shp_to_ee_fmt(geodf,index):
    data = json.loads(geodf.to_json())
    return data['features'][index]['geometry']['coordinates']

def get_whole_region(geodf):
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
    except:
        print("Could not display {}".format(name))
