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


##ESSEN
#euclidean
esse_UA_eucl = funcs.execute_eucl("Essen, Germany", ess_epsg, Essen_UA,'UA')
esse_OSM_base_eucl = funcs.execute_eucl("Essen, Germany", ess_epsg, Essen_UA,'OSM_base')
esse_OSM_adj_eucl = funcs.execute_eucl("Essen, Germany", ess_epsg, Essen_UA,'OSM_adj')
#network
esse_UA_na = funcs.execute_na("Essen, Germany", ess_epsg, Essen_UA,'UA')
esse_OSM_base_na = funcs.execute_na("Essen, Germany", ess_epsg, Essen_UA,'OSM_base')
esse_OSM_adj_na = funcs.execute_na("Essen, Germany", ess_epsg, Essen_UA,'OSM_adj')
#nearest
esse_UA_near = funcs.execute_nearest("Essen, Germany", ess_epsg, Essen_UA,'UA')
esse_OSM_base_near = funcs.execute_nearest("Essen, Germany", ess_epsg, Essen_UA,'OSM_base')
esse_OSM_adj_near = funcs.execute_nearest("Essen, Germany", ess_epsg, Essen_UA,'OSM_adj')



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

#local Morans I
#turn into seperate function
distances = [300,800]
sizes = [0.25,1,5]
names = ["UA", "OSM_base", "OSM_adj"]
method= ["euclidean", "na", "near"]
city = 'Nijmegen, the Netherlands'

for k in range(len(names)):
    for i in range(len(distances)):
        for j in range(len(sizes)):
            funcs.moran_bv_plots(city, method[0], distances[i], sizes[j], names[k], "identifier")


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
#OSM, 300m
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',0.25 ,300,nijm_na_025_300_OSM_gini_table,
                            nijm_eucl_025_300_OSM_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',1 ,300,nijm_na_1_300_OSM_gini_table,
                            nijm_eucl_1_300_OSM_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',5,300,nijm_na_5_300_OSM_gini_table,
                            nijm_eucl_5_300_OSM_gini_table, id='identifier')
#OSM, 800m
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',0.25, 800,nijm_na_025_800_OSM_gini_table,
                            nijm_eucl_025_800_OSM_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',1, 800,nijm_na_1_800_OSM_gini_table,
                            nijm_eucl_1_800_OSM_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','OSM',Nijmegen_UA, nijm_epsg,'OSM',5, 800,nijm_na_5_800_OSM_gini_table,
                            nijm_eucl_5_800_OSM_gini_table, id='identifier')

#UA, 300m
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',0.25 ,300,nijm_na_025_300_UA_gini_table,
                            nijm_eucl_025_300_UA_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',1 ,300,nijm_na_1_300_UA_gini_table,
                            nijm_eucl_1_300_UA_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',5,300,nijm_na_5_300_UA_gini_table,
                            nijm_eucl_5_300_UA_gini_table, id='identifier')
#UA, 800m
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',0.25, 800,nijm_na_025_800_UA_gini_table,
                            nijm_eucl_025_800_UA_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',1, 800,nijm_na_1_800_UA_gini_table,
                            nijm_eucl_1_800_UA_gini_table, id='identifier')
funcs.maps_green_per_poly('Nijmegen','UA',Nijmegen_UA, nijm_epsg,'UA',5, 800,nijm_na_5_800_UA_gini_table,
                            nijm_eucl_5_800_UA_gini_table, id='identifier')






