# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#program to extract network data


#importing libraries
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox
import pandas as pd
import mapclassify
import All_functions as funcs


##creating data/output folders
if not os.path.exists('data'): os.makedirs('data')
if not os.path.exists('output'): os.makedirs('output')

#place of extraction
city= 'Maastricht, The Netherlands'
projection = 'EPSG:28992'

## Read shapefile(not possible to create direct download link, since there is a need to login for access)
city_shp = gpd.read_file('./data/NL505L1_MAASTRICHT/Shapefiles/NL505L1_MAASTRICHT_UA2012.shp')

#tags
parks_tag = ['parks', 'dog_park', 'garden', 'playground', 'nature_reserve']
landuse_tag = ['grass', 'allotments', 'meadow', 'forest']

## calculate the euclidean distance gini for maastricht and parks
maastr_eucl_200_gini, maastr_eucl_200_gini_table = funcs.calc_eucl_ugs_gini("Maastricht", 'EPSG:28992', city_shp, 200, 'leisure', parks_tag)
maastr_eucl_300_gini, maastr_eucl_300_gini_table = funcs.calc_eucl_ugs_gini("Maastricht", 'EPSG:28992', city_shp, 300, 'leisure', parks_tag)
maastr_eucl_1000_gini, maastr_eucl_1000_gini_table = funcs.calc_eucl_ugs_gini("Maastricht", 'EPSG:28992', city_shp, 1000, 'leisure', parks_tag)

#plot the gini and save to file
funcs.plot_graph_gini(maastr_eucl_200_gini_table, "Maastricht Euclidean 200m", maastr_eucl_300_gini_table, "Maastricht Euclidean 300m",
                maastr_eucl_1000_gini_table, "Maastricht Euclidean 1000m", "maastricht_gini")


#Network analysis






## Create a map to show the park area acces per pop polygon.
# need to join the ginitable back to the pop polygons
## add park_area to city_shp based on ident
## diverentiate between 300/500
city_park_area = city_shp_RD.merge( right=tot_df, left_on=['IDENT'], right_on=['IDENT'], how="inner")
base_map = city_shp_cut.plot(color="grey")

pop_sort.plot(ax = base_map, column= "green_per_pop", cmap='RdYlGn', scheme="quantiles")

fig, ax = plt.subplots()
ax.set_aspect('equal')
city_shp_RD.plot(ax=ax, color="grey")
city_park_area.plot(ax=ax, column= "park_area", cmap='RdYlGn', scheme="quantiles")
plt.show()

city_park_area.to_file("./output/city_park_area.shp")
parks_RD_clean.to_file("./output/parks_RD.shp")
