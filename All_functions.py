#Functions file
#

def calc_eucl_ugs_gini (city, EPSG, UA_data, eucl_dist):
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd
    #Extract city boundary
    city_boundary = ox.geocode_to_gdf(city)
    # transform projection
    city_boundary_RD = city_boundary.to_crs(EPSG)
    city_shp_RD = UA_data.to_crs(EPSG)
    #cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, city_shp_RD, how='intersection')
    # select all population polygons with population greater than 0
    city_shp_pop = city_shp_cut[city_shp_cut['Pop2012'] > 0]
    # extract osm landuse
    # tags = { "landuse" : ['grass', 'allotments', 'meadow', 'forest']} NEEDS TO BE EXPANDED/MADE A MORE ACCURATE TO REPRESENT GREEN SPACE
    parks_landuse_tags = ['grass', 'allotments', 'meadow', 'forest']
    x = ox.footprints_from_place("Maastricht", footprint_type='landuse')
    # only select relevant green space tags from the landuse extraction
    parks = x[x['landuse'].isin(parks_landuse_tags)]
    # convert the green spaces to RD new
    parks_RD = parks.to_crs(EPSG)
    # only keep relevant columns
    parks_RD_clean = parks_RD[["landuse", "geometry"]].copy()
    parks_RD_clean["park_area"] = parks_RD_clean.area
    pop_buffer = gpd.GeoDataFrame(city_shp_pop, geometry=city_shp_pop.buffer(eucl_dist)).copy()
    # only keep relevant columns
    pop_buffer_clean = pop_buffer[["IDENT", "Pop2012", "geometry"]]
    # identify the parks within the buffers
    park_buffer_join = gpd.sjoin(parks_RD_clean, pop_buffer_clean, how="inner", op="intersects")
    #create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_buffer_join.groupby("IDENT")["park_area"].sum()
    ## add the population column
    tot_df = pd.merge(tot_df, pop_buffer_clean[["IDENT", "Pop2012"]], on="IDENT", how="inner")
    #Calculate the gini
    gini_table = tot_df
    gini_table["pop_frctn"] = tot_df["Pop2012"] / (tot_df["Pop2012"].sum())
    gini_table["green_frctn"] = tot_df["park_area"] / tot_df["park_area"].sum()
    gini_table = gini_table.sort_values(["green_frctn"])
    gini_table["cum_sum_pop_frctn"] = gini_table["pop_frctn"].cumsum()
    gini_table["cum_sum_green_frctn"] = gini_table["green_frctn"].cumsum()
    gini_table["prev_cs_g_f"] = gini_table["cum_sum_green_frctn"].shift(1)
    gini_table["prev_cs_g_f"] = gini_table["prev_cs_g_f"].fillna(0)
    gini_table["area"] = ((gini_table["cum_sum_green_frctn"] + gini_table["prev_cs_g_f"]) * 0.5) * gini_table[
        "pop_frctn"]
    b = gini_table["area"].sum()
    a = 0.5 - b
    gini = a / (a + b)
    return gini, gini_table


def calc_netwanly_ugs_gini (city, EPGS, UA_data, dist):
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd
    # Extract city boundary and road network
    city_boundary = ox.geocode_to_gdf(city, buffer_dist= 500)
    roads_city = ox.graph_from_place(city, retain_all= True, network_type='walk', buffer_dist=500, which_result=2)
    nodes, city_roads = ox.graph_to_gdfs(roads_city)






def plot_graph_gini(data1, label1, data2,label2, data3, label3, filename):
    import matplotlib.pyplot as plt
    x_base = [0, 1]
    y_base = [0, 1]
    plt.plot(x_base, y_base, label="Perfect Gini", linewidth=2, linestyle='--', color="blue")
    plt.plot(data1["cum_sum_pop_frctn"], data1["cum_sum_green_frctn"],
             label=label1, linewidth=2, color="red")
    plt.plot(data2["cum_sum_pop_frctn"], data2["cum_sum_green_frctn"],
             label=label2, linewidth=2, color="yellow")
    plt.plot(data3["cum_sum_pop_frctn"], data3["cum_sum_green_frctn"],
             label=label3, linewidth=2, color="green")
    plt.xlabel("Cumulative share of population")
    plt.ylabel("Cumulative share of greenspace")
    plt.title("Gini coefficient")
    plt.legend()
    plt.savefig('./output/'+filename)
    plt.show()
