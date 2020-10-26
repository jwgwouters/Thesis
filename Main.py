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


## Read shapefile(not possible to create direct download link, since there is a need to login for access)
Bristol_UA = gpd.read_file("./data/UK011L2_BRISTOL_UA2012_revised_021/Data/UK011L2_BRISTOL_UA2012_revised_021.gpkg")
Essen_UA = gpd.read_file("./data/DE038L1_RUHRGEBIET_013/Data/DE038L1_RUHRGEBIET_013.gpkg")
Nijmegen_UA = gpd.read_file("./data/NL013L3_NIJMEGEN_UA2012_revised_021/Data/NL013L3_NIJMEGEN_UA2012_revised_021.gpkg")

#The distance of the euclidean & network service areas and the used epsg per city
distance = 800
brist_epsg = 'EPSG:27700'
ess_epsg = 'EPSG:5676'
nijm_epsg = 'EPSG:28992'

#the osm tags used
#parks_tag = ['parks', 'dog_park', 'garden', 'playground', 'nature_reserve']
#landuse_tag = ['grass', 'allotments', 'meadow', 'forest']
tags = {'landuse':['grass','allotments', 'meadow', 'forest']}

##BRISTOL
#calculate Bristol NA and Eucl 800m  gini for osm landuse tags
brist_na_800_OSM_gini, brist_na_800_OSM_gini_table = funcs.calc_na_ugs_gini(city="Bristol, United Kingdom", EPSG=brist_epsg, UA_data=Bristol_UA,dist= distance,osm_tags= tags, id='identifier')
brist_eucl_800_OSM_gini, brist_eucl_800_OSM_gini_table, brist_pop = funcs.calc_eucl_ugs_gini("Bristol, United Kingdom", brist_epsg, Bristol_UA, distance, osm_tags=tags, id='identifier')

#calculate Bristol NA and Eucl 800m  gini for UA UGS definition
brist_na_800_UA_gini, brist_na_800_UA_gini_table = funcs.calc_na_ugs_gini("Bristol, United Kingdom", brist_epsg, Bristol_UA, distance, osm_tags=0, id='identifier')
brist_eucl_800_UA_gini, brist_eucl_800_UA_gini_table, brist_pop = funcs.calc_eucl_ugs_gini("Bristol, United Kingdom", brist_epsg, Bristol_UA, distance, osm_tags=0, id='identifier')


##ESSEN
#calculate Essen NA and Eucl 800m  gini for landuse tags
ess_na_800_OSM_gini, ess_na_800_OSM_gini_table = funcs.calc_na_ugs_gini("Essen, Germany", ess_epsg, Essen_UA, distance, osm_tags= tags, id="IDENT")
ess_eucl_800_OSM_gini, ess_eucl_800_OSM_gini_table, ess_pop = funcs.calc_eucl_ugs_gini("Essen, Germany", ess_epsg, Essen_UA, distance, osm_tags= tags, id="IDENT")

#calculate Essen NA and Eucl 800m  gini for UA UGS definition
ess_na_800_UA_gini, ess_na_800_UA_gini_table = funcs.calc_na_ugs_gini("Essen, Germany", ess_epsg, Essen_UA, distance,  osm_tags=0, id="IDENT")
ess_eucl_800_UA_gini, ess_eucl_800_UA_gini_table, ess_pop = funcs.calc_eucl_ugs_gini("Essen, Germany", ess_epsg, Essen_UA, distance, osm_tags=0, id="IDENT")


##NIJMEGEN
#calculate Nijmegen NA and Eucl 800m  gini for landuse tags
nijm_na_800_OSM_gini, nijm_na_800_OSM_gini_table = funcs.calc_na_ugs_gini("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, distance, osm_tags= tags, id='identifier')
nijm_eucl_800_OSM_gini, nijm_eucl_800_OSM_gini_table, nijm_pop = funcs.calc_eucl_ugs_gini("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, distance, osm_tags= tags, id= 'identifier')

#calculate Nijmegen NA and Eucl 800m  gini for UA UGS definition
nijm_na_800_UA_gini, nijm_na_800_UA_gini_table = funcs.calc_na_ugs_gini("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, distance, osm_tags = 0, id='identifier')
nijm_eucl_800_UA_gini, nijm_eucl_800_UA_gini_table, nijm_pop = funcs.calc_eucl_ugs_gini("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, distance, osm_tags=0, id='identifier')



##Visualizations
#Plot & save the gini graphs per city the different methods and 2 selected definitions
funcs.plot_graph_gini(brist_eucl_800_OSM_gini_table, "Bristol OSM Euclidean 800m",
                      brist_na_800_OSM_gini_table, "Bristol OSM Network Analysis 800m",
                      brist_eucl_800_UA_gini_table, "Bristol UA Euclidean 800m",
                      brist_na_800_UA_gini_table, "Bristol UA Network Analysis 800m",
                      filename='brist_na_eucl_800_UA_OSM_gini_landuse')

funcs.plot_graph_gini(ess_eucl_800_OSM_gini_table, "Essen OSM Euclidean 800m",
                      ess_na_800_OSM_gini_table, "Essen OSM Network Analysis 800m",
                      ess_eucl_800_UA_gini_table, "Essen UA Euclidean 800m",
                      ess_na_800_UA_gini_table, "Essen UA Network Analysis 800m",
                      filename='ess_na_eucl_800_UA_OSM_gini_landuse')

funcs.plot_graph_gini(nijm_eucl_800_OSM_gini_table, "Nijmegen OSM Euclidean 800m",
                      nijm_na_800_OSM_gini_table, "Nijmegen OSM Network Analysis 800m",
                      nijm_eucl_800_UA_gini_table,"Nijmegen UA Euclidean 800m",
                      nijm_na_800_UA_gini_table, "Nijmegen UA Network Analysis 800m",
                      filename='nijm_na_eucl_800_UA_OSM_gini_landuse')

## Plot the histograms of the distribution of the ha UGS per population per dataset
#Nijmegen UA and OSM histograms
funcs.histo_area_UGS(city= "Nijmegen", csv_eucl_path='./output/Nijmegen_800_UA_eucl_gini_table.csv', csv_na_path='./output/Nijmegen_800_UA_na_gini_table.csv',
                     datasetname='UA' , filename='Nijmegen_UA_histogram')
funcs.histo_area_UGS(city= "Nijmegen", csv_eucl_path='./output/Nijmegen_800_OSM_eucl_gini_table.csv', csv_na_path='./output/Nijmegen_800_OSM_na_gini_table.csv',
                     datasetname='OSM' , filename='Nijmegen_OSM_histogram')
plt.cla()
#Bristol UA and OSM histograms
funcs.histo_area_UGS(city= "Bristol", csv_eucl_path='./output/Bristol_800_UA_eucl_gini_table.csv', csv_na_path='./output/Bristol_800_UA_na_gini_table.csv',
                     datasetname='UA' , filename='Bristol_UA_histogram')
funcs.histo_area_UGS(city= "Bristol", csv_eucl_path='./output/Bristol_800_OSM_eucl_gini_table.csv', csv_na_path='./output/Bristol_800_OSM_na_gini_table.csv',
                     datasetname='OSM' , filename='Bristol_OSM_histogram')

#Essen UA and OSM histograms
funcs.histo_area_UGS(city= "Essen", csv_eucl_path='./output/Essen_800_UA_eucl_gini_table.csv', csv_na_path='./output/Essen_800_UA_na_gini_table.csv',
                     datasetname='UA' , filename='Essen_UA_histogram')
funcs.histo_area_UGS(city= "Essen", csv_eucl_path='./output/Essen_800_OSM_eucl_gini_table.csv', csv_na_path='./output/Essen_800_OSM_na_gini_table.csv',
                     datasetname='OSM' , filename='Essen_OSM_histogram')

##Maps of total area and difference in area per method and dataset

#Nijmegen
funcs.maps_green_per_poly(city='Nijmegen',dataset='UA',UA_data=Nijmegen_UA, EPSG=nijm_epsg, na_gini_csv=nijm_na_800_UA_gini_table,
                            eucl_gini_csv=nijm_eucl_800_UA_gini_table, id='identifier')
funcs.maps_green_per_poly(city='Nijmegen',dataset='OSM',UA_data=Nijmegen_UA, EPSG=nijm_epsg, na_gini_csv=nijm_na_800_OSM_gini_table,
                            eucl_gini_csv=nijm_eucl_800_OSM_gini_table, id='identifier')
#Essen
funcs.maps_green_per_poly('Essen','UA',Essen_UA, ess_epsg, ess_na_800_UA_gini_table,
                            ess_eucl_800_UA_gini_table, 'IDENT')
funcs.maps_green_per_poly('Essen','OSM',Essen_UA, ess_epsg, ess_na_800_OSM_gini_table,
                            ess_eucl_800_OSM_gini_table, 'IDENT')

#Bristol
funcs.maps_green_per_poly('Bristol','UA',Bristol_UA, brist_epsg, brist_na_800_UA_gini_table,
                            brist_eucl_800_UA_gini_table, 'identifier')
funcs.maps_green_per_poly('Bristol','OSM',Bristol_UA, brist_epsg, brist_na_800_OSM_gini_table,
                            brist_eucl_800_OSM_gini_table, 'identifier')

