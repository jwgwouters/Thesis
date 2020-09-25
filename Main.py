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
Amsterdam_UA = gpd.read_file("./data/NL002L3_AMSTERDAM_013/Data/NL002L3_AMSTERDAM_013.gpkg")
London_UA = gpd.read_file("./data/UK001L3_LONDON_013/Data/UK001L3_LONDON_013.gpkg")
Paris_UA = gpd.read_file("./data/FR001L1_PARIS_013/Data/FR001L1_PARIS_013.gpkg")

Bristol_UA = gpd.read_file("./data/UK011L2_BRISTOL_UA2012_revised_021/Data/UK011L2_BRISTOL_UA2012_revised_021.gpkg")
Essen_UA = gpd.read_file("./data/DE038L1_RUHRGEBIET_013/Data/DE038L1_RUHRGEBIET_013.gpkg")
Nijmegen_UA = gpd.read_file("./data/NL013L3_NIJMEGEN_UA2012_revised_021/Data/NL013L3_NIJMEGEN_UA2012_revised_021.gpkg")


#tags
parks_tag = ['parks', 'dog_park', 'garden', 'playground', 'nature_reserve']
landuse_tag = ['grass', 'allotments', 'meadow', 'forest']

#calculate Amsterdam NA and Eucl 300m  gini for landuse tags
amst_na_300_landuse_gini, amst_na_300_landuse_gini_table = funcs.calc_na_ugs_gini("Amsterdam", 'EPSG:28992', Amsterdam_UA, 300, 'landuse', landuse_tag)
amst_eucl_300_landuse_gini, amst_eucl_300_landuse_gini_table = funcs.calc_eucl_ugs_gini("Amsterdam", 'EPSG:28992', Amsterdam_UA, 300, 'landuse', landuse_tag)

#calculate London NA and Eucl 300m  gini for landuse tags
lond_na_300_landuse_gini, lond_na_300_landuse_gini_table = funcs.calc_na_ugs_gini("London", 'EPSG:27700', London_UA, 300, 'landuse', landuse_tag)
lond_eucl_300_landuse_gini, lond_eucl_300_landuse_gini_table = funcs.calc_eucl_ugs_gini("London", 'EPSG:27700', London_UA, 300, 'landuse', landuse_tag)

#calculate Paris NA and Eucl 300m  gini for landuse tags
pari_na_300_landuse_gini, pari_na_300_landuse_gini_table = funcs.calc_na_ugs_gini("Paris", 'EPSG: 27572', Paris_UA, 300, 'landuse', landuse_tag)
pari_eucl_300_landuse_gini, pari_eucl_300_landuse_gini_table = funcs.calc_eucl_ugs_gini("Paris", 'EPSG: 27572', Paris_UA, 300, 'landuse', landuse_tag)

#calculate Bristol NA and Eucl 300m  gini for landuse tags
brist_na_800_landuse_gini, brist_na_800_landuse_gini_table = funcs.calc_na_ugs_gini("Bristol", 'EPSG:27700', Bristol_UA, 800, 'landuse', landuse_tag, 'identifier')
brist_eucl_800_landuse_gini, brist_eucl_800_landuse_gini_table = funcs.calc_eucl_ugs_gini("Bristol", 'EPSG:27700', Bristol_UA, 800, 'landuse', landuse_tag, 'identifier')

#calculate Essen NA and Eucl 300m  gini for landuse tags
ess_na_800_landuse_gini, ess_na_800_landuse_gini_table = funcs.calc_na_ugs_gini("Essen", 'EPSG:5676', Essen_UA, 800, 'landuse', landuse_tag, id="IDENT")
ess_eucl_800_landuse_gini, ess_eucl_800_landuse_gini_table = funcs.calc_eucl_ugs_gini("Essen", 'EPSG:5676', Essen_UA, 800, 'landuse', landuse_tag, id="IDENT")

#calculate Nijmegen NA and Eucl 300m  gini for landuse tags
nijm_na_800_landuse_gini, nijm_na_800_landuse_gini_table = funcs.calc_na_ugs_gini("Nijmegen", 'EPSG:28992', Nijmegen_UA, 800, 'landuse', landuse_tag, 'identifier')
nijm_eucl_800_landuse_gini, nijm_eucl_800_landuse_gini_table = funcs.calc_eucl_ugs_gini("Nijmegen", 'EPSG:28992', Nijmegen_UA, 800, 'landuse', landuse_tag, id= 'identifier')


#Plot & save the gini graphs per city
funcs.plot_graph_gini(brist_eucl_800_landuse_gini_table, "Bristol landuse Euclidean 800m", brist_na_800_landuse_gini_table, "Bristol landuse Network Analysis 800m",
                      filename='brist_na_eucl_800_gini_landuse')

funcs.plot_graph_gini(ess_eucl_800_landuse_gini_table, "Essen landuse Euclidean 800m", ess_na_800_landuse_gini_table, "Essen landuse Network Analysis 800m",
                      filename='ess_na_eucl_800_gini_landuse')

funcs.plot_graph_gini(nijm_eucl_800_landuse_gini_table, "Nijmegen landuse Euclidean 800m", nijm_na_800_landuse_gini_table, "Nijmegen landuse Network Analysis 800m",
                      filename='nijm_na_eucl_800_gini_landuse')

#save gini tables (need to incorporate into function)
nijm_eucl_800_landuse_gini_table.to_csv("./output/nijmegen_800_eucl_gini_table.csv")
nijm_na_800_landuse_gini_table.to_csv("./output/nijmegen_800_na_gini_table.csv")

ess_eucl_800_landuse_gini_table.to_csv("./output/essen_800_eucl_gini_table.csv")
ess_na_800_landuse_gini_table.to_csv("./output/essen_800_na_gini_table.csv")

brist_eucl_800_landuse_gini_table.to_csv("./output/bristol_800_eucl_gini_table.csv")
brist_na_800_landuse_gini_table.to_csv("./output/bristol_800_na_gini_table.csv")



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
