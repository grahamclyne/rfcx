DYNAMIC WORLD TREE COVER ANALYSIS 


files included:

dynamic_world_tree_cover_stats.py: generates yearly/monthly csv file of tree cover percentage from Dynamic World dataset
    start_date: beginning of time period 
    end_date: end of time period
    shape_file: shape file to be used to determine region of interest
    time_interval: needs to be one of: month, year

visualize_tree_cover.py: generates html image of mode composition of date range provided using Dynamic World
    start_date: beginning of time period 
    end_date: end of time period
    shape_file: shape file to be used to determine region of interest

before_after.py: generates html image of tree_cover change from before_period to after_period
    start_period: beginning of time period, to one year after this date
    end_period: end of time period, to one year after this date (should be at least one year after the start_period)
    shape_file: shape file to be used to determine region of interest



to run: 

using python 3.9

install virtualenv if not already installed:

    python3 -m pip install --user virtualenv

create and activate virtual environment:

    python3 -m venv env
    source env/bin/activate

install required files: 

    python3 -m pip install -r requirements.txt

to use gee, you will be prompted to authenticate via google acount with browser
to use command-line authentication, see https://developers.google.com/earth-engine/guides/command_line

example usages: 
    python3 dynamic_world_tree_cover_stats.py  --start_date 2016-01-01 --end_date 2021-01-01 --shape_file  /Users/gclyne/Downloads/sumatra_shp/village_forest_boundaries_guardian.shp --time_interval year
    python before_after.py --start_period 2020-01-01 --end_period 2021-01-01 --shape_file /Users/gclyne/Downloads/RFCx_GQ_Shapefiles/Hulu_Batang_Hari_sites_Buffer1k.shp
    python3 visualize_tree_cover.py --start_date 2020-01-01 --end_date 2021-01-01 --shape_file /Users/gclyne/Downloads/sumatra_shp/village_forest_boundaries_guardian.shp

to close virtual environment:

    deactivate
