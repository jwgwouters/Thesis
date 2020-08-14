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


##creating data/output folders
if not os.path.exists('data'): os.makedirs('data')
if not os.path.exists('output'): os.makedirs('output')

#place of extraction
city= 'Maastricht, The Netherlands'
projection = 'EPSG:28992'

## Read shapefile
city_shp = gpd.read_file('./data/NL505L1_MAASTRICHT/Shapefiles/NL505L1_MAASTRICHT_UA2012.shp')

#creates outline of municipality
city_boundary = ox.gdf_from_place(city)

#extracts the road network including the intersection nodes
roads_city = ox.graph_from_place(city, network_type='walk')
nodes, city_roads = ox.graph_to_gdfs(roads_city)

#transform projection
#to RD New
city_boundary_RD = city_boundary.to_crs(projection)
city_shp_RD = city_shp.to_crs(projection)
city_roads_RD = city_roads.to_crs(projection)

#intersect roads and landuse by city boundary
city_shp_cut = gpd.overlay(city_boundary_RD, city_shp_RD, how= 'intersection')

#city_roads_cut = gpd.overlay(city_boundary_RD, city_roads_RD, how= 'intersection')
city_roads_cut = gpd.sjoin(city_roads_RD, city_boundary_RD, op='intersects')

#select all population polygons with population greater than 0
city_shp_pop = city_shp_cut[city_shp_cut['Pop2012'] > 0]

#extract osm landuse
#tags = { "landuse" : ['grass', 'allotments', 'meadow', 'forest']} NEEDS TO BE EXPANDED/MADE A MORE ACCURATE TO REPRESENT GREEN SPACE
parks_landuse_tags = ['grass', 'allotments', 'meadow', 'forest']
x = ox.footprints_from_place("Maastricht", footprint_type='landuse')

#only select relevant green space tags from the landuse extraction
parks = x[x['landuse'].isin(parks_landuse_tags)]

#convert the green spaces to RD new
parks_RD = parks.to_crs(projection)

#only keep relevant columns
parks_RD_clean = parks_RD[["landuse", "geometry"]].copy()
parks_RD_clean["park_area"]= parks_RD_clean.area


#create euclidean buffer around the population polygons
#this way the original data stays the same
pop_buffer = gpd.GeoDataFrame(city_shp_pop, geometry = city_shp_pop.buffer(300))

#only keep relevant columns
pop_buffer_clean = pop_buffer[["IDENT", "Pop2012", "geometry"]]

## only keep parks that intersect with buffer
parks_ints_buff = parks_RD[parks_RD.intersects(pop_buffer.geometry)]

buffer_park_join = gpd.sjoin(pop_buffer_clean, parks_RD_clean, how="inner", op="intersects")
park_buffer_join = gpd.sjoin(parks_RD_clean, pop_buffer_clean, how="inner", op="intersects")

#create new dataframe with the total park area per ident(unique pop polygon id)
tot_df = park_buffer_join.groupby("IDENT")["park_area"].sum()

## add the population column
tot_df = pd.merge(tot_df, pop_buffer_clean[["IDENT", "Pop2012"]], on="IDENT", how="inner")

## calculate the Gini

