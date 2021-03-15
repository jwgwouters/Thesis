#program to extract network data

#importing libraries
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox
import pandas as pd
import mapclassify
import All_functions as funcs

brist_epsg = 'EPSG:27700'
ess_epsg = 'EPSG:5676'
nijm_epsg = 'EPSG:28992'
cities = ['Bristol, United Kingdom', "Essen, Germany", "Nijmegen, the Netherlands"]

## Read shapefile(not possible to create direct download link, since there is a need to login for access)
Bristol_UA = gpd.read_file("./data/UK011L2_BRISTOL_UA2012_revised_021/Data/UK011L2_BRISTOL_UA2012_revised_021.gpkg")
Essen_UA = gpd.read_file("./data/DE038L1_RUHRGEBIET_013/Data/DE038L1_RUHRGEBIET_013.gpkg")
Nijmegen_UA = gpd.read_file("./data/NL013L3_NIJMEGEN_UA2012_revised_021/Data/NL013L3_NIJMEGEN_UA2012_revised_021.gpkg")

#create folders for data and output per method per city
funcs.create_folders(cities, methods = ['network', 'euclidean', 'nearest'])

#create intermediate data necessary for the use in the differnt methods (such as road networks, city boundaries)
funcs.preprocessing(cities[0],brist_epsg, "./data/UK011L2_BRISTOL_UA2012_revised_021/Data/UK011L2_BRISTOL_UA2012_revised_021.gpkg")
funcs.preprocessing(cities[1],ess_epsg, "./data/DE038L1_RUHRGEBIET_013/Data/DE038L1_RUHRGEBIET_013.gpkg")
funcs.preprocessing(cities[2],nijm_epsg, "./data/NL013L3_NIJMEGEN_UA2012_revised_021/Data/NL013L3_NIJMEGEN_UA2012_revised_021.gpkg")

#park extract
funcs.park_extract('Bristol, United Kingdom',Bristol_UA, brist_epsg,'identifier' )
funcs.park_extract("Nijmegen, the Netherlands",Nijmegen_UA, nijm_epsg,'identifier' )



##Bristol
#euclidean
brist_UA_eucl = funcs.execute_eucl('Bristol, United Kingdom', brist_epsg, Bristol_UA,'UA')
brist_OSM_base_eucl = funcs.execute_eucl('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_base')
brist_OSM_adj_eucl = funcs.execute_eucl('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_adj')
#network
brist_UA_na = funcs.execute_na('Bristol, United Kingdom', brist_epsg, Bristol_UA,'UA')
brist_OSM_base_na = funcs.execute_na('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_base')
brist_OSM_adj_na = funcs.execute_na('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_adj')
#nearest
brist_UA_near = funcs.execute_nearest('Bristol, United Kingdom', brist_epsg, Bristol_UA,'UA')
brist_OSM_base_near = funcs.execute_nearest('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_base')
brist_OSM_adj_near = funcs.execute_nearest('Bristol, United Kingdom', brist_epsg, Bristol_UA,'OSM_adj')



##Nijmegen
#euclidean
nijm_eucl_UA = funcs.execute_eucl("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'UA')
nijm_eucl_OSM_base = funcs.execute_eucl("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_base')
nijm_eucl_OSM_adj = funcs.execute_eucl("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_adj')
#network
nijm_na_UA = funcs.execute_na("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'UA')
nijm_na_OSM_base = funcs.execute_na("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_base')
nijm_na_OSM_adj = funcs.execute_na("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_adj')
#nearest
nijm_nearest_UA = funcs.execute_nearest("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'UA')
nijm_nearest_OSM_base = funcs.execute_nearest("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_base')
nijm_nearest_OSM_adj = funcs.execute_nearest("Nijmegen, the Netherlands", nijm_epsg, Nijmegen_UA, 'OSM_adj')


##execute the mann whintey function for Nijmegen
funcs.execute_MW()
##execute the Moran's I function for Nijmegen
funcs.execute_MI()


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

#




