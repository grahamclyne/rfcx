from pystac_client import Client
from pystac.extensions.eo import EOExtension as eo
import planetary_computer as pc
import rasterio
from rasterio import windows
from rasterio import features
from rasterio import warp
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

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

time_of_interest = "2019-06-01/2019-07-01"


catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

search = catalog.search(
    collections=["sentinel-2-l2a"],
    intersects=area_of_interest,
    datetime=time_of_interest,
    query={"eo:cloud_cover": {"lt": 10}},
)

# Check how many items were returned
items = list(search.get_items())
print(f"Returned {len(items)} Items")


least_cloudy_item = sorted(items, key=lambda item: eo.ext(item).cloud_cover)[0]

print(
    f"Choosing {least_cloudy_item.id} from {least_cloudy_item.datetime.date()}"
    f" with {eo.ext(least_cloudy_item).cloud_cover}% cloud cover"
)


asset_href = least_cloudy_item.assets["visual"].href
signed_href = pc.sign(asset_href)

 


with rasterio.open(signed_href) as ds:
    aoi_bounds = features.bounds(area_of_interest)
    warped_aoi_bounds = warp.transform_bounds("epsg:4326", ds.crs, *aoi_bounds)
    aoi_window = windows.from_bounds(transform=ds.transform, *warped_aoi_bounds)
    band_data = ds.read(window=aoi_window)

import rioxarray
rds = rioxarray.open_rasterio(signed_href)
rds = rds.isel(x=np.logical_and(
    rds.x >= warped_aoi_bounds[0],rds.x <= warped_aoi_bounds[2]),
    y=np.logical_and(rds.y >= warped_aoi_bounds[1],rds.y <= warped_aoi_bounds[3])
    )
rds.plot()
rds = rds.squeeze().drop("spatial_ref")
rds.name = "data"
res = rds.to_dataframe()
res = res.unstack('band')
print(res)
res.to_csv('sentinel_test.csv')
img = Image.fromarray(np.transpose(band_data, axes=[1, 2, 0]))
w = img.size[0]
h = img.size[1]
aspect = w / h

target_w = 800
target_h = (int)(target_w / aspect)
img.resize((target_w, target_h), Image.BILINEAR)
# df = band_data.reshape(2,2212443).to_pandas()
# img.save('test_s2.png')