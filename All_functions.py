#Functions file
#TEST1233

def calc_eucl_ugs_gini (city, EPSG, UA_data, eucl_dist, osm_tags, id):
    # import packages
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd
    # Extract city boundary(incorrect boundary is selected for Nijmegen at which_result 1)
    city_boundary = ox.geocode_to_gdf(city, which_result=1)
    if city == 'Nijmegen, the Netherlands':
        city_boundary = ox.geocode_to_gdf(city, which_result=2)

    # transform projection
    city_boundary_RD = city_boundary.to_crs(EPSG)
    city_shp_RD = UA_data.to_crs(EPSG)
    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, city_shp_RD, how='intersection')
    # select all population polygons with population greater than 0
    city_shp_pop = city_shp_cut[city_shp_cut['Pop2012'] > 0]
    if osm_tags == 'eu':
        if id == 'identifier':
            #use the definition of the Urban Atlas for UGS
            parks = city_shp_cut[city_shp_cut['code_2012'].isin(['14100', '31000'])]
        else:
            parks = city_shp_cut[city_shp_cut['CODE2012'].isin(['14100', '31000'])]
    elif osm_tags =='ua' :
        if id == 'identifier':
            #use the definition of the Urban Atlas for UGS
            parks = city_shp_cut[city_shp_cut['code_2012'].isin(['14100'])]
        else:
            parks = city_shp_cut[city_shp_cut['CODE2012'].isin(['14100'])]
    else:
        # extract osm landuse & use a buffer of 1km around the city to also extract parks just outside the city boundary
        # create a 1km to also incorporate UGS outside the city
        city_boundary_buff = city_boundary.to_crs(EPSG)
        city_boundary_buff = city_boundary_buff.buffer(1000)
        city_boundary_buff = city_boundary_buff.to_crs(city_boundary.crs)
        parks = ox.geometries_from_polygon(city_boundary_buff[0], osm_tags)
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
    if osm_tags != 0 :
        gini_table.to_csv("./output/" + city[:4] + "_" + str(eucl_dist) + "_OSM_eucl_gini_table.csv")
    else:
        gini_table.to_csv("./output/" + city[:4] + "_" + str(eucl_dist) + "_UA_eucl_gini_table.csv")
    return gini, gini_table, city_shp_pop


def calc_na_ugs_gini (city, EPSG, UA_data, dist, osm_tags, id):
    import os
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
    # Extract city boundary
    city_boundary = ox.geocode_to_gdf(city, which_result=1)
    if city == 'Nijmegen, the Netherlands':
        city_boundary = ox.geocode_to_gdf(city, which_result=2)
    # transform pop and road network and city boundary to the entered EPSG
    G_tf = ox.project_graph(G, to_crs=EPSG)
    pop_tf = UA_data.to_crs(EPSG)
    city_boundary_RD = city_boundary.to_crs(EPSG)

    #select the defintion based on if osm_tags was filled in or not
    if osm_tags == 'ua':
        if id == 'identifier':
            #use the definition of the Urban Atlas for UGS
            parks = pop_tf[pop_tf['code_2012'].isin(['14100'])]
        else:
            parks = pop_tf[pop_tf['CODE2012'].isin(['14100'])]
    elif osm_tags=='eu':
        if id == 'identifier':
            # use the definition of the Urban Atlas for UGS
            parks = pop_tf[pop_tf['code_2012'].isin(['14100', '31000'])]
        else:
            parks = pop_tf[pop_tf['CODE2012'].isin(['14100', '31000'])]
    else:
        # extract osm landuse & use a buffer of 1km around the city to also extract parks just ouside the city boundary
        city_boundary_buff = city_boundary.to_crs(EPSG)
        city_boundary_buff = city_boundary_buff.buffer(1000)
        city_boundary_buff = city_boundary_buff.to_crs(city_boundary.crs)
        parks = ox.geometries_from_polygon(city_boundary_buff[0], osm_tags)

        #use the definition of the Urban Atlas for UGS 14100= Green urban areas

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
    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, pop_tf, how='intersection')

    # select only the pop polygons
    pop_poly = city_shp_cut[city_shp_cut['Pop2012'] > 0]

    if not os.path.exists("./output/" + city[:4].lower() + "_na_buffer.shp"):
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
        na_gdf.to_file("./output/" + city[:4].lower() + "_na_buffer.shp")
    else:
        na_gdf = gpd.read_file("./output/" + city[:4].lower() + "_na_buffer.shp")
    # set same index as the pop_poly
    na_gdf = na_gdf.set_index(pop_poly.index)

    # rejoin the original pop data  & IDENT to the created buffers
    na_gdf["Pop2012"] = pop_poly.Pop2012
    na_gdf[id] = pop_poly[id]

    # follow the steps as in the euclidean buffer
    # identify the parks within the na service areaa
    park_NA_join = gpd.sjoin(parks_copy, na_gdf, how="inner", op="intersects")

    # create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_NA_join.groupby(id)["park_area"].sum()
    ## add the population column
    tot_df = pd.merge(tot_df, na_gdf[[id, "Pop2012"]], on=id, how="inner")

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
        gini_table.to_csv("./output/" + city[:4] + "_" + str(dist) + "_OSM_na_gini_table.csv")
    else:
        gini_table.to_csv("./output/" + city[:4] + "_" + str(dist) + "_UA_na_gini_table.csv")
    return gini, gini_table

def plot_graph_gini(data1, label1, data2,label2, data3,label3, data4,label4,  filename):
    import matplotlib.pyplot as plt
    x_base = [0, 1]
    y_base = [0, 1]
    plt.plot(x_base, y_base, label="Perfect Gini", linewidth=2, linestyle='--', color="blue")
    plt.plot(data1["cum_sum_pop_frctn"], data1["cum_sum_green_frctn"],
             label=label1, linewidth=2, color="orchid")
    if label2!=0:
        plt.plot(data2["cum_sum_pop_frctn"], data2["cum_sum_green_frctn"],
             label=label2, linewidth=2, color="orange")
    if label3 !=0:
        plt.plot(data3["cum_sum_pop_frctn"], data3["cum_sum_green_frctn"],
             label=label3, linewidth=2, color="springgreen")
    if label4 !=0:
        plt.plot(data4["cum_sum_pop_frctn"], data4["cum_sum_green_frctn"],
             label=label4, linewidth=2, color="darkcyan")
    plt.xlabel("Cumulative share of population")
    plt.ylabel("Cumulative share of greenspace")
    plt.title("Gini coefficient")
    plt.legend()
    plt.savefig('./output/'+filename)
    plt.show()

def histo_area_UGS (city, csv_eucl_path, csv_na_path,  datasetname, filename ):
    import matplotlib.pyplot as plt
    import pandas as pd
    # load the data
    hist_data_eucl = pd.read_csv(csv_eucl_path)
    hist_data_na = pd.read_csv(csv_na_path)
    # transform the park area per pp_polygon m2 to ha
    hist_data_eucl['park_area'] = hist_data_eucl['park_area'] / 10000
    hist_data_na['park_area'] = hist_data_na['park_area'] / 10000
    # plot the histogram, use the population as weights
    plt.hist(x=hist_data_eucl['park_area'], weights=hist_data_eucl['Pop2012'],
             bins=75, color='green', alpha=0.5, label='Euclidean')
    plt.hist(x=hist_data_na['park_area'], weights=hist_data_na['Pop2012'],
             bins=75, color='blue', alpha=0.5, label='Network')
    plt.axvline(hist_data_eucl['park_area'].mean(), color='green', linestyle='dashed',
                linewidth=1, label='Euclidean mean')
    plt.axvline(x=hist_data_na['park_area'].mean(), color='blue', linestyle='dashed',
                linewidth=1, label='Network mean')
    min_ylim, max_ylim = plt.ylim()
    plt.text(hist_data_eucl['park_area'].mean() * 1.1, max_ylim * 0.7,
             'Euclidean mean: {:.2f}'.format(hist_data_eucl['park_area'].mean()))
    plt.text(hist_data_na['park_area'].mean() * 1.1, max_ylim * 0.9,
             'Network mean: {:.2f}'.format(hist_data_na['park_area'].mean()))
    plt.legend()
    plt.title("Amount of hectares of UGS per population in "+ city + ' of the '+ datasetname+ " dataset for both the Euclidean and the Network method")
    plt.savefig('./output/'+filename)
    plt.show()

def maps_green_per_poly (city,dataset, UA_data, EPSG, osm_tags, na_gini_csv, eucl_gini_csv, id):
    import matplotlib.pyplot as plt
    import contextily as ctx
    import osmnx as ox
    import geopandas as gpd
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    ## Create a map to show the park area acces per pop polygon.
    pop_tf = UA_data.to_crs(EPSG)
    # extract city boundary and convert to correct epsg
    city_boundary = ox.geocode_to_gdf(city)
    city_boundary_RD = city_boundary.to_crs(EPSG)
    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary_RD, pop_tf, how='intersection')

    ##extract the park areas of UA or OSM
    if osm_tags == 'ua':
        if id == 'identifier':
            #use the definition of the Urban Atlas for UGS
            parks = pop_tf[pop_tf['code_2012'].isin(['14100'])]
        else:
            parks = pop_tf[pop_tf['CODE2012'].isin(['14100'])]
    elif osm_tags=='eu':
        if id == 'identifier':
            # use the definition of the Urban Atlas for UGS
            parks = pop_tf[pop_tf['code_2012'].isin(['14100', '31000'])]
        else:
            parks = pop_tf[pop_tf['CODE2012'].isin(['14100', '31000'])]
    else:
        # extract osm landuse & use a buffer of 1km around the city to also extract parks just ouside the city boundary
        city_boundary_buff = city_boundary.to_crs(EPSG)
        city_boundary_buff = city_boundary_buff.buffer(1000)
        city_boundary_buff = city_boundary_buff.to_crs(city_boundary.crs)
        parks = ox.geometries_from_polygon(city_boundary_buff[0], osm_tags)
    # convert the green spaces to RD new
    parks_RD = parks.to_crs(EPSG)
    # clip parks to boundary of
    parks_cut = gpd.clip(parks_RD,city_boundary_RD)
    # perform unary union to combine overlapping park polygons and then explode the multipolygon into separate polygons
    parks_copy = parks_cut.copy()
    geom = parks_copy.geometry.unary_union
    parks_copy = gpd.GeoDataFrame(geometry=[geom], crs=EPSG)
    parks_copy = parks_copy.explode().reset_index(drop=True)
    parks_copy['UGS'] = 'parks'

    # select only the pop polygons
    pop_poly = city_shp_cut[city_shp_cut['Pop2012'] > 0]
    # merge the park table and the pop polys and create new column with UGS/person
    na_park_area = pop_poly.merge(right=na_gini_csv, left_on=[id], right_on=[id], how="inner")
    na_park_area['park_area'] = na_park_area['park_area'] / 10000
    eucl_park_area = pop_poly.merge(right=eucl_gini_csv, left_on=[id], right_on=[id], how="inner")
    eucl_park_area['park_area'] = eucl_park_area['park_area'] / 10000

    ## difference between the two
    eucl_park_area['diff_green_per_person_eucl_na'] = eucl_park_area['park_area'] - na_park_area['park_area']

    ##create map which visualizes network
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    parks_copy.plot(ax=ax, color='darkgreen', legend=True, label='UGS')
    na_park_area.plot(ax=ax, column='park_area', scheme="user_defined",
                              classification_kwds=dict(bins=[10, 25, 50, 75, 100]),
                              cmap='cividis', alpha=0.7, legend=True, legend_kwds={'title': "Legend"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(city + ' Network UGS total park area(in ha) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_' + dataset + '_park_area_pop_na.png', dpi=500)

    ##euclidean plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    parks_copy.plot(ax=ax, column='parks_1', color='darkgreen', legend=True, zorder=1, label='UGS')
    eucl_park_area.plot(ax=ax, column='park_area', scheme="user_defined",
                                classification_kwds=dict(bins=[10, 25, 50, 75, 100]),
                                cmap='cividis', alpha=0.7, legend=True, legend_kwds={'title': "Legend"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(city + ' Euclidean UGS total park area (in ha) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_' + dataset + '_park_area_pop_eucl.png', dpi=500)

    # difference plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    parks_copy.plot(ax=ax, column='parks_1', color='darkgreen', legend=True, zorder=1, label='UGS')
    eucl_park_area.plot(ax=ax, column='diff_green_per_person_eucl_na', cmap='RdBu', alpha=0.7, legend=True,
                                cax=cax, legend_kwds={'label': "Difference between Euclidean and Network method in ha"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(
        city + ' difference in UGS total area(in ha) \n per method(Euclidean(+), Network(-)) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_' + dataset + '_park_area_diff.png', dpi=500)


