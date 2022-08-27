#!/bin/sh

cd /Users/gclyne/rfcx


python3 dynamic_world_tree_cover_stats.py  --start_date 2016-01-01 --end_date 2021-01-01 --shape_file  /Users/gclyne/Downloads/sumatra_shp/village_forest_boundaries_guardian.shp --time_interval year
python3 dynamic_world_tree_cover_stats.py  --start_date 2016-01-01 --end_date 2021-01-01 --shape_file  /Users/gclyne/Downloads/RFCx_GQ_Shapefiles/Tembe_Reserve_sites_Buffer1k.shp --time_interval year
python3 dynamic_world_tree_cover_stats.py  --start_date 2016-01-01 --end_date 2021-01-01 --shape_file  /Users/gclyne/Downloads/RFCx_GQ_Shapefiles/Hulu_Batang_Hari_sites_Buffer1k.shp --time_interval year
python3 dynamic_world_tree_cover_stats.py  --start_date 2016-01-01 --end_date 2021-01-01 --shape_file  /Users/gclyne/Downloads/Tembe_shp/Tembe_Reserve.shp --time_interval year

cd /