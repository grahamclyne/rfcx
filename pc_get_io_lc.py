from dask.distributed import Client as dask_client
from matplotlib.colors import ListedColormap
from pystac_client import Client

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import rasterio
import rasterio.features
import stackstac
import matplotlib.pyplot as plt
from rasterio import windows
from rasterio import features
from rasterio import warp

# Set the environment variable PC_SDK_SUBSCRIPTION_KEY, or set it here.
# The Hub sets PC_SDK_SUBSCRIPTION_KEY automatically.
# pc.settings.set_subscription_key(<YOUR API Key>)


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

search = catalog.search(collections=["io-lulc-9-class"], intersects=area_of_interest)

# Check how many items were returned
items = list(search.get_items())
print(f"Returned {len(items)} Items")


# The STAC metadata contains some information we'll want to use when creating
# our merged dataset. Get the EPSG code of the first item and the nodata value.
item = items[0]
signed_items = [pc.sign(item).to_dict() for item in items]
bounds_latlon = rasterio.features.bounds(area_of_interest)
# Create a single DataArray from out multiple resutls with the corresponding
# rasters projected to a single CRS. Note that we set the dtype to ubyte, which
# matches our data, since stackstac will use float64 by default.
stack = stackstac.stack(
    signed_items,
    dtype=np.ubyte,
    fill_value=255,
    bounds_latlon=bounds_latlon,
)

client = dask_client(processes=False)
print(f"/proxy/{client.scheduler_info()['services']['dashboard']}/status")

nodata = {"nodata": 0} if stackstac.__version__ >= "0.3.0" else {}
merged = stack.squeeze().compute()

print(merged)
from pystac.extensions.item_assets import ItemAssetsExtension

collection = catalog.get_collection("io-lulc-9-class")
ia = ItemAssetsExtension.ext(collection)

x = ia.item_assets["data"]
class_names = {x["summary"]: x["values"][0] for x in x.properties["file:values"]}
values_to_classes = {v: k for k, v in class_names.items()}
class_count = len(class_names)

# with rasterio.open(pc.sign(item.assets["data"].href)) as src:
#     colormap_def = src.colormap(1)  # get metadata colormap for band 1
#     colormap = [
#         np.array(colormap_def[i]) / 255 for i in range(max(class_names.values()))
#     ]  # transform to matplotlib color format

signed_href = pc.sign(item.assets["data"].href)

with rasterio.open(signed_href) as ds:
    aoi_bounds = features.bounds(area_of_interest)
    warped_aoi_bounds = warp.transform_bounds("epsg:4326", ds.crs, *aoi_bounds)
    aoi_window = windows.from_bounds(transform=ds.transform, *warped_aoi_bounds)
    band_data = ds.read(window=aoi_window)


print(warped_aoi_bounds)


import rioxarray
rds = rioxarray.open_rasterio(signed_href)
rds = rds.isel(x=np.logical_and(
    rds.x >= warped_aoi_bounds[0],rds.x <= warped_aoi_bounds[2]),
    y=np.logical_and(rds.y >= warped_aoi_bounds[1],rds.y <= warped_aoi_bounds[3])
    )
rds.plot()
plt.show()
print(rds.x)

# cmap = ListedColormap(colormap)

# vmin = 0
# vmax = max(class_names.values())
# epsg = merged.epsg.item()

# p = merged.plot(
#     subplot_kws=dict(projection=ccrs.epsg(epsg)),
#     col="time",
#     transform=ccrs.epsg(epsg),
#     cmap=cmap,
#     vmin=vmin,
#     vmax=vmax,
#     figsize=(16, 6),
# )
# ticks = np.linspace(0.5, 10.5, 11)
# labels = [values_to_classes.get(i, "") for i in range(cmap.N)]
# p.cbar.set_ticks(ticks, labels=labels)
# p.cbar.set_label("Class")


df = merged.stack(pixel=("y", "x")).T.to_pandas()
# print(df)
df.to_csv('io_luc.csv')