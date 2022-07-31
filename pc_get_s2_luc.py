from pystac_client import Client
import numpy as np
import pandas as pd
import planetary_computer as pc
import rasterio
from rasterio import windows
from rasterio import features
from rasterio import warp


time_of_interest = "2019-06-01/2019-06-02"
area_of_interest = {
    "type": "Polygon",
    "coordinates": [
        [
[-51.8609754914384,-3.777515829709419],
[-51.78544448557903,-3.777515829709419],
[-51.78544448557903,-3.6980343861803275],
[-51.8609754914384,-3.6980343861803275],
[-51.8609754914384,-3.777515829709419]
        ]
    ],
}

catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

search_luc = catalog.search(
    collections=["io-lulc-9-class"],
    intersects=area_of_interest,
    time=time_of_interest
)
search_sentinel = catalog.search(
    collections=["sentinel-2-l2a"],
    intersects=area_of_interest,
    datetime=time_of_interest,
    query={"eo:cloud_cover": {"lt": 10}},
)

# Check how many items were returned
luc_items = list(search_luc.get_items())
# Check how many items were returned
sentinel_items = list(search_sentinel.get_items())


# The STAC metadata contains some information we'll want to use when creating
# our merged dataset. Get the EPSG code of the first item and the nodata value.
luc_item = luc_items[0]
sentinel_item = sentinel_items[0]

luc_signed_href = pc.sign(luc_item.assets["data"].href)
sentinel_signed_href = pc.sign(sentinel_item.assets["data"].href)

with rasterio.open(luc_signed_href) as ds:
    aoi_bounds = features.bounds(area_of_interest)
    warped_aoi_bounds = warp.transform_bounds("epsg:4326", ds.crs, *aoi_bounds)
    aoi_window = windows.from_bounds(transform=ds.transform, *warped_aoi_bounds)
    band_data = ds.read(window=aoi_window)


import rioxarray
luc_rds = rioxarray.open_rasterio(luc_signed_href)
luc_rds = luc_rds.isel(x=np.logical_and(
    luc_rds.x >= warped_aoi_bounds[0],luc_rds.x <= warped_aoi_bounds[2]),
    y=np.logical_and(luc_rds.y >= warped_aoi_bounds[1],luc_rds.y <= warped_aoi_bounds[3])
    )



# df = merged.stack(pixel=("y", "x")).T.to_pandas()
# df.to_csv('io_luc.csv')