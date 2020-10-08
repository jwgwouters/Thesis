#Functions file
#

def calc_eucl_ugs_gini (city, EPSG, UA_data, eucl_dist, osm_tags, id):
    # import packages
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd
    # Extract city boundary
    city_boundary = ox.geocode_to_gdf(city)
    # transform projection
    city_boundary_RD = city_boundary.to_crs(EPSG)
    city_shp_RD = UA_data.to_crs(EPSG)
    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, city_shp_RD, how='intersection')
    # select all population polygons with population greater than 0
    city_shp_pop = city_shp_cut[city_shp_cut['Pop2012'] > 0]
    if osm_tags != 0:
        # extract osm landuse & use a buffer of 1km around the city to also extract parks just ouside the city boundary
        parks = ox.geometries_from_place(city, osm_tags, buffer_dist=1000)
    else:
        #use the definition of the Urban Atlas for UGS
        parks = city_shp_cut[city_shp_cut['code_2012'].isin(['14100'])]
    # convert the green spaces to RD new
    parks_RD = parks.to_crs(EPSG)
    # perform unary union to combine overlapping park polygons and then explode the multipolygon into separate polygons
    parks_copy = parks_RD.copy()
    geom = parks_copy.geometry.unary_union
    parks_copy = gpd.GeoDataFrame(geometry=[geom], crs=EPSG)
    parks_copy = parks_copy.explode().reset_index(drop=True)

    # only keep relevant columns
    # parks_RD_clean = parks_RD[[ftprnt_type, "geometry"]].copy()
    parks_copy["park_area"] = parks_copy.area
    pop_buffer = gpd.GeoDataFrame(city_shp_pop, geometry=city_shp_pop.buffer(eucl_dist)).copy()
    # only keep relevant columns
    pop_buffer_clean = pop_buffer[[id, "Pop2012", "geometry"]]
    # identify the parks within the buffers
    park_buffer_join = gpd.sjoin(parks_copy, pop_buffer_clean, how="inner", op="intersects")
    # create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_buffer_join.groupby(id)["park_area"].sum()
    ## add the population column
    tot_df = pd.merge(tot_df, pop_buffer_clean[[id, "Pop2012"]], on=id, how="inner")
    # Calculate the gini
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
    gini_table.to_csv("./output/" + city + "_eucl_gini_table.csv")
    return gini, gini_table, city_shp_pop


def calc_na_ugs_gini (city, EPSG, UA_data, dist, osm_tags, id):
    import geopandas as gpd
    import networkx as nx
    import osmnx as ox
    import numpy as np
    import pandas as pd
    from descartes import PolygonPatch
    from shapely.geometry import Point, LineString, Polygon

    network_type = 'all'
    trip_times = [(dist / 100)]
    travel_speed = 6  # walking speed in km/hour

    # download streetnetwork
    G = ox.graph_from_place(city, network_type=network_type)
    # transform pop and road network to the entered EPSG
    G_tf = ox.project_graph(G, to_crs=EPSG)
    pop_tf = UA_data.to_crs(EPSG)
    #select the defintion based on if osm_tags was filled in or not
    if osm_tags != 0:
        # extract osm landuse & use a buffer of 1km around the city to also extract parks just ouside the city boundary
        parks = ox.geometries_from_place(city, osm_tags, buffer_dist=1000)
    else:
        #use the definition of the Urban Atlas for UGS 14100= Green urban areas
        parks = pop_tf[pop_tf['code_2012'].isin(['14100'])]
    #convert parks to entered EPSG
    parks_RD = parks.to_crs(EPSG)
    # perform unary union to combine overlapping park polygons and then explode the multipolygon into separate polygons
    parks_copy = parks_RD.copy()
    geom = parks_copy.geometry.unary_union
    parks_copy = gpd.GeoDataFrame(geometry=[geom], crs=EPSG)
    parks_copy = parks_copy.explode().reset_index(drop=True)

    # only keep relevant columns
    # parks_RD_clean = parks_RD[[ftprnt_type, "geometry"]].copy()
    parks_copy["park_area"] = parks_copy.area

    # Extract city boundary
    city_boundary = ox.geocode_to_gdf(city)
    city_boundary_RD = city_boundary.to_crs(EPSG)

    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, pop_tf, how='intersection')

    # select only the pop polygons
    pop_poly = city_shp_cut[city_shp_cut['Pop2012'] > 0]

    # create a tuple with the x an y coordinates of the pop polygon centroids
    coords_cen = np.vstack([pop_poly.centroid.x, pop_poly.centroid.y]).T
    coords_cen_tp = tuple(map(tuple, coords_cen))

    # add an edge attribute for time in minutes required to traverse each edge
    meters_per_minute = travel_speed * 1000 / 60  # km per hour to m per minute
    for u, v, k, data in G.edges(data=True, keys=True):
        data['time'] = data['length'] / meters_per_minute
    print("starting NA poly generation")

    def make_iso_polys(G, center_node, edge_buff=25, node_buff=50, infill=False, ):
        isochrone_polys = []
        for trip_time in sorted(trip_times, reverse=True):
            subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')

            node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
            nodes_gdf = gpd.GeoDataFrame({'id': list(subgraph.nodes)}, geometry=node_points)
            nodes_gdf = nodes_gdf.set_index('id')

            edge_lines = []
            for n_fr, n_to in subgraph.edges():
                f = nodes_gdf.loc[n_fr].geometry
                t = nodes_gdf.loc[n_to].geometry
                edge_lookup = G.get_edge_data(n_fr, n_to)[0].get('geometry', LineString([f, t]))
                edge_lines.append(edge_lookup)

            n = nodes_gdf.buffer(node_buff).geometry
            e = gpd.GeoSeries(edge_lines).buffer(edge_buff).geometry
            all_gs = list(n) + list(e)
            new_iso = gpd.GeoSeries(all_gs).unary_union

            # try to fill in surrounded areas so shapes will appear solid and blocks without white space inside them
            if infill:
                new_iso = Polygon(new_iso.exterior)
            isochrone_polys.append(new_iso)
        return isochrone_polys

    def iterate_multiple_coords(the_coordinates):
        poly_list = []
        count = 0
        for i in the_coordinates:
            count = count + 1
            # method is euclidean since epgs is unprojected
            centre_node = ox.get_nearest_node(G_tf, (i[1], i[0]), method='euclidean')
            # print("starting" + str(i)) # to check
            # add an edge attribute for time in minutes required to traverse each edge
            for u, v, k, data in G_tf.edges(data=True, keys=True):
                data['time'] = data['length'] / meters_per_minute
            # make the polygons
            isochrone_polys_iter = make_iso_polys(G_tf,
                                                  centre_node,
                                                  edge_buff=25,
                                                  node_buff=0,
                                                  infill=False)
            # add a progress notification
            if count == round((0.1 * len(the_coordinates))):
                print("10% complete")
            if count == round((0.25 * len(the_coordinates))):
                print("25% complete")
            if count == round((0.5 * len(the_coordinates))):
                print("50% complete")
            if count == round((0.75 * len(the_coordinates))):
                print("75% complete")
            if count == round((0.9 * len(the_coordinates))):
                print("90% complete")
            # print("done " + str([i])) # to check
            poly_list.append(isochrone_polys_iter)
            # print("appended " + str([i])) # to check
        return (poly_list)

    # create the na service areas
    pop_na_poly = iterate_multiple_coords(coords_cen_tp)
    print("Finish NA poly generation, starting Gini calculation")
    # create a save command an if statement so if only the tags change it doens't recalculate the buffers

    ## turn shapely geometries list file to geodataframe
    na_gdf = gpd.GeoDataFrame()
    for i in range(len(pop_na_poly)):
        na_gdf = na_gdf.append(gpd.GeoDataFrame(geometry=pop_na_poly[i], crs=EPSG))

    # set same index as the pop_poly
    na_gdf = na_gdf.set_index(pop_poly.index)

    # rejoin the original pop data  & IDENT to the created buffers
    na_gdf["Pop2012"] = pop_poly.Pop2012
    na_gdf[id] = pop_poly[id]

    # follow the steps as in the euclidean buffer
    # identify the parks within the na service areaa
    park_NA_join = gpd.sjoin(parks_copy, na_gdf, how="inner", op="intersects")

    # create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_NA_join.groupby("IDENT")["park_area"].sum()
    ## add the population column
    tot_df = pd.merge(tot_df, na_gdf[["IDENT", "Pop2012"]], on="IDENT", how="inner")

    # Calculate the gini
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
    if osm_tags != 0 :
        gini_table.to_csv("./output/" + city + "_OSM_na_gini_table.csv")
    else:
        gini_table.to_csv("./output/" + city + "_UA_na_gini_table.csv")
    return gini, gini_table

def plot_graph_gini(data1, label1, data2,label2, data3,label3, data4,label4,  filename):
    import matplotlib.pyplot as plt
    x_base = [0, 1]
    y_base = [0, 1]
    plt.plot(x_base, y_base, label="Perfect Gini", linewidth=2, linestyle='--', color="blue")
    plt.plot(data1["cum_sum_pop_frctn"], data1["cum_sum_green_frctn"],
             label=label1, linewidth=2, color="red")
    if data2!=0:
        plt.plot(data2["cum_sum_pop_frctn"], data2["cum_sum_green_frctn"],
             label=label2, linewidth=2, color="yellow")
    if data3 !=0:
        plt.plot(data3["cum_sum_pop_frctn"], data3["cum_sum_green_frctn"],
             label=label3, linewidth=2, color="green")
    if data4 !=0:
        plt.plot(data4["cum_sum_pop_frctn"], data4["cum_sum_green_frctn"],
             label=label4, linewidth=2, color="blue")
    plt.xlabel("Cumulative share of population")
    plt.ylabel("Cumulative share of greenspace")
    plt.title("Gini coefficient")
    plt.legend()
    plt.savefig('./output/'+filename)
    plt.show()
