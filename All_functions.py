#Functions file
#TEST1233
#function that creates population, boundary, roads and UA_data saves
def create_folders(cities, methods):
    import os
    ##Create a folder for every method and within every method create extra folder for maps
    ##creating data/output folders
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists('output'): os.makedirs('output')
    #create folder for buffers
    if not os.path.exists('output/buffers'): os.makedirs('output/buffers')

    #create folder per city and method
    for i in range(len(cities)):
        if not os.path.exists('output/'+ cities[i][:4].lower()): os.makedirs('output/'+ cities[i][:4].lower())
        if not os.path.exists('output/'+ cities[i][:4].lower()+"/interdata"): os.makedirs('output/'+ cities[i][:4].lower()+"/interdata")
        for j in range(len(methods)):
            if not os.path.exists('output/' + cities[i][:4].lower()+'/'+methods[j]): os.makedirs('output/' + cities[i][:4].lower()+'/'+methods[j])
            #create maps folder
            if not os.path.exists('output/' + cities[i][:4].lower() + '/' + methods[j]+'/maps'): os.makedirs('output/' + cities[i][:4].lower() + '/' + methods[j]+'/maps')

#function that creates population, boundary, roads and UA_data saves
def preprocessing(city,epsg, UA_data_path):
    ##load data
    import pandas as pd
    import geopandas as gpd
    import osmnx as ox

    UA_data = gpd.read_file(UA_data_path)
    city_abr = city[0:4].lower()
    network_type= 'all'
    filepath= './output/'+city_abr+'/interdata/'+city_abr

    #POP data
    #create city boundary
    city_boundary = ox.geocode_to_gdf(city, which_result=1)
    if city == 'Nijmegen, the Netherlands':
        city_boundary = ox.geocode_to_gdf(city, which_result=2)
    #select pop polygons & tranform and clip to boundary
    pop_poly = UA_data[UA_data['Pop2012'] > 0]

    #tranform both pop, roads and boundary
    pop_tf = pop_poly.to_crs(epsg)
    boundary_tf = city_boundary.to_crs(epsg)
    ua_data_tf = UA_data.to_crs(epsg)
    pop_clp = gpd.clip(pop_tf,boundary_tf, keep_geom_type=True)

    #Road network
    # create buffer around city boundary(this way also roads just outside the city will be selected
    city_bnd_tf = city_boundary.to_crs(epsg)
    city_bnd_bff_tf = city_bnd_tf.buffer(800)
    city_bnd_bff = city_bnd_bff_tf.to_crs(city_boundary.crs)

    ntw = ox.graph_from_polygon(city_bnd_bff.geometry[0], network_type=network_type, simplify=False)
    nodes, edges = ox.utils_graph.graph_to_gdfs(ntw)
    ntw_tf = ox.project_graph(ntw, to_crs=epsg)
    nodes_tf = nodes.to_crs(epsg)
    edges_tf = edges.to_crs(epsg)
    #clip the UA data by the same buffer
    ua_clp = gpd.clip(ua_data_tf,boundary_tf, keep_geom_type=True)

    #create save for pop,boundary and total UA data
    #possible to convert these to geopackage instead of shape file
    ox.save_graphml(ntw_tf, filepath=filepath+"_road_ntw.graphml")
    pop_clp.to_file(filepath+'_pop_data.shp')
    boundary_tf.to_file(filepath+'_city_boundary.shp')
    city_bnd_bff.to_file(filepath+'_city_boundary_bff.shp')
    ua_clp.to_file(filepath+'_UA_data.shp')
    nodes_tf.to_file(filepath+'_road_nodes.shp')
    edges_tf.to_file(filepath+'_road_edges.shp')

def park_extract(city,UA_data, EPSG, id):
    #Function that extracts and saves both UA(urban green space and forest) and OSM(based on tags) parks
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd

    osm_base_tags = {'amenity': ['grave_yard'],
                     'landuse': ['allotments', 'cemetery', 'grass', 'forest', 'recreation_ground', 'village_green'],
                     'leisure': ['common', 'dog_park', 'garden', 'nature_reserve', 'park', 'playground'],
                     'natural': ['wood'], 'tourism': ['zoo', 'picnic_site']}
    osm_adj_tags = {'landuse': ['allotments', 'grass', 'forest', 'recreation_ground', 'village_green'],
                    'leisure': ['common', 'dog_park', 'garden', 'nature_reserve', 'park', 'playground'],
                    'natural': ['wood'], 'tourism': ['picnic_site']}
    city_abr = city[0:4].lower()
    city_boundary = gpd.read_file('./output/'+city_abr+'/interdata/'+city_abr+'_city_boundary.shp')
    city_boundary_bff = gpd.read_file('./output/'+city_abr+'/interdata/'+city_abr+'_city_boundary_bff.shp')
    #load ua data
    ua_data = gpd.read_file('./output/'+city_abr+'/interdata/'+city_abr+'_ua_data.shp')
    # select UA parks, extract OSM parks
    if id == 'identifier':
        ua_parks = ua_data[ua_data['code_2012'].isin(['14100', '31000'])]
    else:
        ua_parks = ua_data[ua_data['CODE2012'].isin(['14100', '31000'])]

    ## function for the osm extraction, every extraction
    def osm_extract(city, EPSG, tags):
        osm_parks = ox.geometries_from_place(city, tags, buffer_dist=2000)
        osm_parks = osm_parks.to_crs(EPSG)
        # select only polygons and multipolygons
        osm_sel = osm_parks[osm_parks.type.isin(['Polygon', 'MultiPolygon'])]
        # remove overlapping OSM parks seperate the multipolygons, set new index
        osm_parks_0 = osm_sel.copy()
        geom = osm_parks_0.geometry.unary_union
        osm_parks_1 = gpd.GeoDataFrame(geometry=[geom], crs=EPSG)
        osm_parks_1 = osm_parks_1.explode().reset_index(drop=True)
        # clip UA data and OSM data by the buffer
        boundary_buff = city_boundary.buffer(1000)
        osm_parks_clip = gpd.clip(osm_parks_1, boundary_buff)
        # remove small and long UGSs via a minus buffer of 10 meters
        osm_parks_min = osm_parks_clip.buffer(-10)
        osm_parks_min = osm_parks_min[~(osm_parks_min.is_empty | osm_parks_min.isna())]
        osm_parks_fin = osm_parks_min.buffer(10)
        # same but for the osm parks
        osm_parks_buff = osm_parks_fin.buffer(4.5)
        osm_parks_uu = osm_parks_buff.unary_union
        osm_parks_uu = osm_parks_uu.buffer(-4.5)
        osm_parks_ovl = gpd.GeoDataFrame(geometry=[osm_parks_uu], crs=EPSG)
        osm_parks_ovl = osm_parks_ovl.explode().reset_index(drop=True)
        osm_parks_ovl['park_area'] = (osm_parks_ovl.area / 10000)
        return osm_parks_ovl

    # merge close by ugss sperated by eg roads
    # create small buffer around ugs
    # merge overlapping ugss
    # create buffer of 4.5 meters(width of half a two lane road), merge the polygons and remove the 4.5 meters
    # (can make a function out of this)
    ua_parks_buff = ua_parks.buffer(4.5)
    ua_parks_uu = ua_parks_buff.unary_union
    ua_parks_uu = ua_parks_uu.buffer(-4.5)
    ua_parks_ovl = gpd.GeoDataFrame(geometry=[ua_parks_uu], crs=EPSG)
    ua_parks_ovl = ua_parks_ovl.explode().reset_index(drop=True)
    ua_parks_ovl['park_area'] = (ua_parks_ovl.area / 10000)

    ## enact the OSM function
    osm_base = osm_extract(city, EPSG, osm_base_tags)
    osm_adj = osm_extract(city, EPSG, osm_adj_tags)

    ##remove areas <0.25
    osm_base_025 = osm_base[osm_base['park_area'] >= 0.25]
    osm_adj_025 = osm_adj[osm_adj['park_area'] >= 0.25]
    ua_parks_025 = ua_parks_ovl[ua_parks_ovl['park_area'] >= 0.25]

    ##save to file
    osm_adj_025.to_file('./output/'+city_abr+'/interdata/'+city_abr+'_osm_adj_parks.shp')
    osm_base_025.to_file('./output/'+city_abr+'/interdata/'+city_abr+'_osm_base_parks.shp')
    ua_parks_025.to_file('./output/'+city_abr+'/interdata/'+city_abr+'_ua_parks.shp')

    # calculate the percentage per size(0.25,1,5 ha)
    tot_ct_area = (city_boundary.area / 10000)
    sizes = [0.25, 1, 5]
    pc_df = pd.DataFrame({'Minimum park size (in ha)': ['0.25', '1', '5']})
    pc_df.set_index('Minimum park size (in ha)')

    def perc_calc(sizes, parks, tot_ct_area):
        percs = []
        for i in range(len(sizes)):
            #add column with park area in ha
            percs.append((float(parks[parks['park_area'] >= i].sum()) / float(tot_ct_area)) * 100)
        return percs

    pc_df['ua_parks_perc'] = perc_calc(sizes, ua_parks_ovl, tot_ct_area)
    pc_df['osm_base'] = perc_calc(sizes, osm_base, tot_ct_area)
    pc_df['osm_adj'] = perc_calc(sizes, osm_adj, tot_ct_area)
    pc_df.to_csv('./output/'+city_abr+'/interdata/'+city_abr+'_parks_perc.csv')
    pc_df.to_excel('./output/'+city_abr+'/interdata/'+city_abr+'_parks_perc.xlsx')



def calc_eucl_ugs_gini (city, EPSG, UA_data, min_size, eucl_dist, name, id):
    # import packages
    import osmnx as ox
    import geopandas as gpd
    import pandas as pd
    import os
    city_abr = city[0:4].lower()
    output_filepath = "./output/"+city_abr+"/euclidean/"
    # Extract city boundary(incorrect boundary is selected for Nijmegen at which_result 1)
    city_boundary = gpd.read_file('./output/' + city_abr + '/interdata/' + city_abr + '_city_boundary.shp')
    #load the ua_data
    ua_data = gpd.read_file('./output/' + city_abr + '/interdata/' + city_abr + '_ua_data.shp')
    nm_l = name.lower()

    # run parks extraction function if first time
    if not os.path.exists('./output/'+city_abr+'/interdata/'+city_abr+'_'+nm_l+'_parks.shp'):
        park_extract(city, UA_data,EPSG,id)
    # cut the data by the city boundary
    city_shp_cut = gpd.overlay(city_boundary, ua_data, how='intersection')
    # select all population polygons with population greater than 0
    city_shp_pop = city_shp_cut[city_shp_cut['Pop2012'] > 0]
    parks_copy = gpd.read_file('./output/'+city_abr+'/interdata/'+city_abr+'_'+name.lower()+'_parks.shp')
    #select only parks of certain size
    parks_sel = parks_copy[parks_copy['park_area']>=min_size]

    pop_buffer = gpd.GeoDataFrame(city_shp_pop, geometry=city_shp_pop.buffer(eucl_dist)).copy()
    pop_buffer.to_file("./output/buffers/" + city_abr + '_' + str(eucl_dist) + "_eucl_buffer.shp")
    # only keep relevant columns
    pop_buffer_clean = pop_buffer[[id, "Pop2012", "geometry"]]
    # identify the parks within the buffers
    park_buffer_join = gpd.sjoin(parks_sel, pop_buffer_clean, how="inner", op="intersects")
    # create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_buffer_join.groupby(id)["park_area"].sum()
    ### link it on left and turn nan value into 0
    ## add the population column
    tot_df = pd.merge(tot_df, pop_buffer_clean[[id, "Pop2012"]], on=id, how="right")
    ### link it on left and turn nan value into 0
    tot_df['park_area'] = tot_df['park_area'].fillna(0)

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
    gini_table["Gini"] = gini
    gini_table.to_csv(output_filepath+city_abr+"_eucl_" + str(eucl_dist) + "_" + str(min_size) +'_' +name+ "_gini_table.csv")
    gini_table.to_excel(output_filepath+city_abr+ "_eucl_" + str(eucl_dist) + "_" + str(min_size) +'_' +name+ "_gini_table.xlsx")
    return gini


def na_analysis(city,name,distance, epsg, size, ident):
    import geopandas as gpd
    import pandas as pd
    import osmnx as ox
    import networkx as nx
    import os
    from shapely.geometry import Point, LineString, Polygon

    UA_data = gpd.read_file('./output/' + city[0:4].lower() + '_pop_polys.shp')
    parks = gpd.read_file('./output/' + city[0:4].lower() + '_' + name + '_parks.shp')
    pop = UA_data[UA_data['Pop2012'] > 0]
    city_abr = city[0:4].lower()
    network_type = 'all'
    trip_times = [(distance / 100)]
    travel_speed = 6  # walking speed in km/hour

    # extract  network and nodes
    # download streetnetwork
    # Extract city boundary
    city_boundary = gpd.read_file('./output/' + city_abr + '/' + city_abr + '_city_boundary.shp')

    # create buffer around city boundary
    city_bnd_tf = city_boundary.to_crs(epsg)
    city_bnd_bff_tf = city_bnd_tf.buffer(600)
    city_bnd_bff = city_bnd_bff_tf.to_crs('EPSG:4326')

    # select on parks of given size
    parks_sel = parks[parks['park_area'] >= size]

    # extract road network, nodes, edges from buffered city boundary
    ##CREATE A SAVE FOR THE NETWORK
    if not os.path.exists("./output/"+city_abr+"/"+city_abr+"_ntw.graphml"):
        ntw = ox.graph_from_polygon(city_bnd_bff.geometry[0], network_type=network_type, simplify=False)
        ox.save_graphml(ntw, filepath="./output/"+city_abr+"/"+city_abr+"_ntw.graphml")
    else:
        ntw = ox.load_graphml(filepath="./output/"+city_abr+"/"+city_abr+"_ntw.graphml")
    nodes, edges = ox.utils_graph.graph_to_gdfs(ntw)

    # tf to crs
    ntw_tf = ox.project_graph(ntw, to_crs=epsg)
    nodes_tf = nodes.to_crs(parks.crs)
    edges_tf = edges.to_crs(parks.crs)

    y = {}
    ##create a dictionary with per pop_poly all the nodes
    ## in format {pop_poly_id :[node_id,node_id,..]}
    for i in range(len(pop)):
        # check for intersect of park i with the nodes
        x = 0
        dist = 0
        while x == 0:  # create loop to test if mask contains nodes if not buffer will be created
            bff = pop[i:(i + 1)].buffer(dist)
            mask = nodes_tf.intersects(bff.geometry.iloc[0])
            if mask.any():
                nodes_int = nodes_tf.loc[mask]
                y.update({pop.iloc[i, 6]: list(nodes_int.osmid)})
                x = 1
            else:
                dist += 3

    if not os.path.exists("./output/buffers/" + city_abr+'_'+str(distance)+"_na_buffer.shp"):

        # add an edge attribute for time in minutes required to traverse each edge
        meters_per_minute = travel_speed * 1000 / 60  # km per hour to m per minute
        for u, v, k, data in ntw_tf.edges(data=True, keys=True):
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

        def iterate_node_dict(node_dict):
            poly_list = []
            full_gdf = gpd.GeoDataFrame()
            count = 0
            for key, value in node_dict.items():
                count = count + 1
                for j in value:
                    # method is euclidean since epgs is unprojected
                    # centre_node = ox.get_nearest_node(ntw_tf, (i[1], i[0]), method='euclidean')
                    # print("starting" + str(i)) # to check
                    # add an edge attribute for time in minutes required to traverse each edge
                    for u, v, k, data in ntw_tf.edges(data=True, keys=True):
                        data['time'] = data['length'] / meters_per_minute
                    # make the polygons
                    isochrone_polys_iter = make_iso_polys(ntw_tf,
                                                          j,
                                                          edge_buff=25,
                                                          node_buff=0,
                                                          infill=False)
                    # add a progress notification
                    if count == round((0.1 * len(y))):
                        print("10% complete")
                    if count == round((0.25 * len(y))):
                        print("25% complete")
                    if count == round((0.5 * len(y))):
                        print("50% complete")
                    if count == round((0.75 * len(y))):
                        print("75% complete")
                    if count == round((0.9 * len(y))):
                        print("90% complete")
                    # print("done " + str([i])) # to check
                    d = {'identifier': [key], 'geometry': isochrone_polys_iter}
                    x = gpd.GeoDataFrame(d, crs=epsg)
                    full_gdf = full_gdf.append(x)

                    # poly_list.append(isochrone_polys_iter)
                    # print("appended " + str([i])) # to check
            return (full_gdf)

        pop_na_poly = iterate_node_dict(y)
        pop_na_poly = pop_na_poly.to_crs(epsg)
        # merge the pop polys based on identifier
        z = pop_na_poly.dissolve(by='identifier')
        ##fill in the polygons
        #MIGTH NOT WORK!!
        line = z.exterior
        na_buffer = gpd.GeoDataFrame()
        for i in range(len(line)):
            f = Polygon(line.iloc[i])
            f_gs = gpd.GeoSeries(f)
            d1 = {'identifier': [z.index[i]]}
            d2 = gpd.GeoDataFrame(d1, geometry=f_gs, crs=pop.crs)
            na_buffer = na_buffer.append(d2)

        # join the population data to the buffers
        pop_buffer = na_buffer.merge(pop[['Pop2012', 'identifier']], how='left', left_on='identifier', right_on=ident)
        pop_buffer_tf = pop_buffer.set_crs(pop.crs)


        ##CREATE IF
        # create a save of the file
        pop_buffer_tf.to_file("./output/buffers/" + city[:4].lower() + '_' + str(distance) + "_na_buffer.shp")
    else:
        pop_buffer_tf = gpd.read_file("./output/buffers/" + city[:4].lower() + '_' + str(distance) + "_na_buffer.shp")

    # follow the steps as in the euclidean buffer
    # identify the parks within the na service areaa
    park_NA_join = gpd.sjoin(parks_sel, pop_buffer_tf, how="inner", op='intersects')

    # create new dataframe with the total park area per ident(unique pop polygon id)
    tot_df = park_NA_join.groupby(ident)["park_area"].sum()
    ## add the population column
    # tot_df = pd.merge(tot_df, na_gdf[[id, "Pop2012"]], on=id, how="inner")
    ## add the population column
    tot_df = pd.merge(tot_df, pop_buffer_tf[[ident, "Pop2012"]], left_on=ident, right_on='identifier', how="right")
    ### link it on left and turn nan value into 0
    tot_df['park_area'] = tot_df['park_area'].fillna(0)
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
    gini_table["Gini"] = gini
    gini_table.to_csv("./output/" + city_abr + '/network/' + city_abr + "_na_" + str(distance) + "_" + str(
        size) + '_' + name + "_gini_table.csv")
    ## relink the data to the na_pop_buffers
    # join accessibility csv with the population polygons
    pop_data = gpd.read_file('./output/' + city_abr + '/' + city_abr + '_pop_data.shp')
    total_pop_shp = pop_data.merge(right=gini_table, left_on=[ident], right_on=[ident],
                                        how="inner")
    total_pop_shp.to_file("./output/" + city_abr + '/network/' + city_abr + "_na_" + str(distance) + "_" + str(
        size) + '_' + name + "_tot_data.csv")
    return gini

##function without multiple park nodes options
def nearest_single(city, ua_data,min_size, epsg, name):
    import geopandas as gpd
    import osmnx as ox
    import numpy as np
    import networkx as nx
    import pandas as pd

    ##variables
    network_type = 'all'
    city_abr = city[0:4].lower()
    output_filepath = "/output/"+city_abr+"/nearest/"


    #load the correct park ### change to load the specific parks
    parks = gpd.read_file('./output/' + city[0:4].lower() + '_'+name+ '_parks.shp')

    #Set a minimum size for the parks
    parks_min = parks[parks['park_area']>=min_size]

    #create city boundary
    city_boundary = ox.geocode_to_gdf(city, which_result=1)
    if city == 'Nijmegen, the Netherlands':
            city_boundary = ox.geocode_to_gdf(city, which_result=2)
    #extract road network# not from place but from city boundary
    #city_rds = ox.graph_from_place(city, network_type=network_type, simplify=False, retain_all=False)

    city_rds = ox.graph_from_polygon(city_boundary.geometry.iloc[0],network_type=network_type, simplify=False, retain_all=False)

    #select pop polygons & tranform and clip to boundary
    pop_poly = ua_data[ua_data['Pop2012'] > 0]

    #tranform both pop, roads and boundary
    pop_tf = pop_poly.to_crs(epsg)
    boundary_tf = city_boundary.to_crs(epsg)
    rds_tf = ox.project_graph(city_rds, to_crs=epsg)
    pop_clp = gpd.clip(pop_tf,boundary_tf, keep_geom_type=True)

    #remove weakly linked areas
    rds_tf_s = ox.utils_graph.get_largest_component(rds_tf,strongly=True)
    # extract Nodes
    nodes, edges = ox.utils_graph.graph_to_gdfs(rds_tf_s)

    #create starting nodes per pop polygon
    pop_nodes = ox.distance.get_nearest_nodes(rds_tf_s, list(pop_clp.centroid.x), list(pop_clp.centroid.y), method='kdtree')

    # recreate for with above incorporated
    # replace the park node selection part
    min_dist = []
    for i in range(len(pop_clp)):
        ##create buffer per pop poly, if ds_lis is na then increase the distance of the buffer
        v = 1
        dst_lis = []
        z = 0
        bff_dst = 0
        while v == 1:
            # create a check to see if at least something intersects with the buffer, otherwise increase the buffer by 500
            bff_dst += 500
            # create buffer
            # pop_bffs = gpd.GeoDataFrame(pop_points, geometry=pop_points.buffer(bff_dst)).copy()
            bff = pop_clp.buffer(bff_dst)
            # pop_bff = gpd.GeoDataFrame(pop_points.iloc[0], geometry=pop_points.buffer(bff_dst)).copy()
            # check intersect
            parks_int = parks_min.geometry.intersects(bff.iloc[i])
            if parks_int.any():
                z = parks_int
                v = 2
            else:
                bff_dst += 1000
        parks_sl = parks_min.loc[z]
        park_nn = ox.get_nearest_nodes(rds_tf_s, parks_sl.centroid.x, parks_sl.centroid.y, method='kdtree')
        pop_nn = pop_nodes[i]
        for j in range(len(park_nn)):
            x5 = nx.shortest_path_length(rds_tf_s, pop_nn, park_nn[j], weight='length')
            dst_lis.append(x5)
        # create a list where the min distance is appended to
        min_dist.append(min(dst_lis))

    # add the min distance list to the pop clp dataframe
    pop_clp['min_dist'] = min_dist
    # save to file
    pop_clp.to_file(output_filepath + city_abr + '_' + name + '_nearest.shp')
    #read file
    pop_clp= gpd.read_file(output_filepath + city_abr + '_' + name + '_nearest.shp')
    if 'IDENT' in pop_clp.columns:
        id = 'IDENT'
    else:
        id = 'identifier'

    # create dataframe with all relevant data
    tot_df = pd.DataFrame()
    tot_df[id] = pop_clp[id]
    tot_df['Pop2012'] = pop_clp['Pop2012']
    tot_df['min_dist'] = pop_clp['min_dist']

    # calculate the Gini
    gini_table = tot_df
    gini_table["pop_frctn"] = tot_df["Pop2012"] / (tot_df["Pop2012"].sum())
    gini_table["nearest_dist_frctn"] = tot_df['min_dist'] / tot_df['min_dist'].sum()
    gini_table = gini_table.sort_values(["nearest_dist_frctn"])
    gini_table["cum_sum_pop_frctn"] = gini_table["pop_frctn"].cumsum()
    gini_table["cum_sum_near_frctn"] = gini_table["nearest_dist_frctn"].cumsum()
    gini_table["prev_cs_g_f"] = gini_table["cum_sum_near_frctn"].shift(1)
    gini_table["prev_cs_g_f"] = gini_table["prev_cs_g_f"].fillna(0)
    gini_table["area"] = ((gini_table["cum_sum_near_frctn"] + gini_table["prev_cs_g_f"]) * 0.5) * gini_table[
        "pop_frctn"]
    b = gini_table["area"].sum()
    a = 0.5 - b
    gini = a / (a + b)
    gini_table["Gini"] = gini
    gini_table.to_csv(output_filepath+ city_abr + "_near_" + str(min_size) +'_' +name+ "_gini_table.csv")
    return gini, gini_table

def execute_eucl(city, epsg, ua_data, name):
    import pandas as pd
    import All_functions as funcs
    sizes = [0.25, 1, 5]
    distances = [300, 800]
    names = ["UA", "OSM_base", "OSM_adj"]
    city_abr = city[0:4].lower()
    # check id of column in pop
    if 'IDENT' in ua_data.columns:
        id = 'IDENT'
    else:
        id = 'identifier'
    # create pandas dataframe with all the ginis per size
    gini_df = pd.DataFrame({'Minimum park size (in ha)': ['0.25', '1', '5']})

    for i in range(len(name)):
        for j in range(len(distances)):
            for k in range(len(sizes)):
                city_eucl_025_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[k], distances[j], names[i], id)
                city_eucl_1_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[k], distances[j], names[i], id)
                city_eucl_5_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[k], distances[j], names[i], id)
            gini_df[city[0:4].lower() + '_eucl_' + names[i] + '_'+str(distances[j])] = [city_eucl_025_300_gini, city_eucl_1_300_gini,
                                                                     city_eucl_5_300_gini]
            gini_df.to_csv("./output/" + city_abr + "/euclidean/" + names[i] +'_'+str(distances[j])+ "_gini_table_eucl.csv")
            gini_df.to_excel("./output/" + city_abr + "/euclidean/" + names[i] +'_'+str(distances[j])+ "_gini_table_eucl.xlsx")
    #
    # # 300m
    # city_eucl_025_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[0], distances[0], name, id)
    # city_eucl_1_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[1], distances[0], name, id)
    # city_eucl_5_300_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[2], distances[0], name, id)
    # # 800m
    # city_eucl_025_800_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[0], distances[1], name, id)
    # city_eucl_1_800_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[1], distances[1], name, id)
    # city_eucl_5_800_gini = funcs.calc_eucl_ugs_gini(city, epsg, ua_data, sizes[2], distances[1], name, id)
    # gini_df[city[0:4].lower()+'_eucl_' + name + '_300'] = [city_eucl_025_300_gini, city_eucl_1_300_gini, city_eucl_5_300_gini]
    # gini_df[city[0:4].lower()+'_eucl_' + name + '_800'] = [city_eucl_025_800_gini, city_eucl_1_800_gini, city_eucl_5_800_gini]
    # gini_df.to_csv("/output/"+city_abr+"/euclidean/"+name+"all_gini_table_eucl.csv")
    # gini_df.to_excel("/output/"+city_abr+"/euclidean/"+name+"all_gini_table_eucl.xlxs")
    return gini_df


def execute_na(city, epsg, ua_data, name):
    import pandas as pd
    import All_functions as funcs
    sizes = [0.25, 1, 5]
    distances = [300, 800]
    city_abr = city[0:4].lower()
    # check id of column in pop
    if 'IDENT' in ua_data.columns:
        id = 'IDENT'
    else:
        id = 'identifier'
    # create pandas dataframe with all the ginis per size
    gini_df = pd.DataFrame({'Minimum park size (in ha)': ['0.25', '1', '5']})

    # 300m
    city_na_025_300_gini = funcs.na_analysis(city,name,distances[0],epsg,sizes[0],id)
    city_na_1_300_gini = funcs.na_analysis(city,name,distances[0],epsg,sizes[1],id)
    city_na_5_300_gini = funcs.na_analysis(city,name,distances[0],epsg,sizes[2],id)
    funcs.na_analysis(city,name,distances[0],epsg,sizes[0],id)
    # 800m
    city_na_025_800_gini = funcs.na_analysis(city,name,distances[1],epsg,sizes[0],id)
    city_na_1_800_gini = funcs.na_analysis(city,name,distances[1],epsg,sizes[1],id)
    city_na_5_800_gini = funcs.na_analysis(city,name,distances[1],epsg,sizes[2],id)
    gini_df[city[0:4].lower()+'_eucl_' + name + '_300'] = [city_na_025_300_gini, city_na_1_300_gini, city_na_5_300_gini]
    gini_df[city[0:4].lower()+'_eucl_' + name + '_800'] = [city_na_025_800_gini, city_na_1_800_gini, city_na_5_800_gini]
    gini_df.to_csv("./output/"+city_abr+"/network/"+name+"_all_gini_table_na.csv")
    gini_df.to_excel("./output/"+city_abr+"/network/"+name+"_all_gini_table_na.xlsx")
    return gini_df


def execute_nearest(city, epsg, ua_data, name):
    import pandas as pd
    import All_functions as funcs
    city_abr = city[0:4].lower()
    sizes= [0.25, 1, 5]
    gini_df = pd.DataFrame({'Minimum park size (in ha)': ['0.25', '1', '5']})
    city_near_025_gini,city_near_025_table  = funcs.nearest_single(city, ua_data, sizes[0], epsg, name)
    city_near_1_gini,city_near_1_table = funcs.nearest_single(city, ua_data, sizes[1], epsg, name)
    city_near_5_gini,city_near_5_table = funcs.nearest_single(city, ua_data, sizes[2], epsg, name)
    gini_df[city[0:4].lower()+'_near_' + name] = [city_near_025_gini, city_near_1_gini, city_near_5_gini]
    gini_df.to_csv("./output/"+city_abr+"/nearest/"+name+"all_gini_table_near.csv")
    return gini_df

def moran_bv_plots(city,method, distance, size, name, ident):
    import os
    import geopandas as gpd
    import pandas as pd
    import matplotlib.pyplot as plt
    from libpysal.weights.contiguity import Queen
    from esda.moran import Moran,Moran_Local, Moran_BV, Moran_Local_BV
    from splot.esda import plot_moran_bv_simulation, plot_moran_bv
    from splot.esda import plot_local_autocorrelation

    city_abr = city[0:4].lower()
    filepath = "./output/"+city_abr+"/euclidean/"
    gini_csv = pd.read_csv(filepath+city_abr+ "_eucl_" + str(distance) + "_" + str(size) +'_' +name+ "_gini_table.csv")
    Nijmegen_UA = gpd.read_file(
        "./data/NL013L3_NIJMEGEN_UA2012_revised_021/Data/NL013L3_NIJMEGEN_UA2012_revised_021.gpkg")
    pop_data = gpd.read_file('./output/' + city_abr + '/interdata/' + city_abr + '_pop_data.shp')
    city_boundary = gpd.read_file('./output/' + city_abr + '/interdata/' + city_abr + '_city_boundary.shp')
    post_data = gpd.read_file("./data/PC5_2015/CBS_PC5_2015_v2.shp")

    # join accessibility csv with the population polygons
    pop_park_area = pop_data.merge(right=gini_csv, left_on=[ident], right_on=[ident], how="inner")

    # cut & save postal data to the Nijmegen extent
    # check intersect with city_boundary
    post_nijm = gpd.overlay(post_data, city_boundary, how='intersection')
    if not os.path.exists('./output/' + city_abr + '/interdata/nijm_post_data.shp'):
        post_nijm.to_file('./output/' + city_abr + '/interdata/nijm_post_data.shp')
    ##calculate the average accessibility to the postal code data of Nijmegen
    # create new column
    post_nijm.loc[:, 'average_park_area'] = 0
    # create loop
    for i in range(len(post_nijm)):
        mask = pop_park_area.intersects(post_nijm.geometry.iloc[i])
        pop_buurt = pop_park_area.loc[mask]
        # calculate the average of these
        mean_pop = pop_buurt.park_area.mean()
        # add mean to buurt
        post_nijm.iloc[i, -1:] = mean_pop
    #create a full dataframe with everything
    full_df = pd.DataFrame(
        columns=['Method', 'Size', 'Distance', 'Variable', 'MoransI', ])

    # the chosen socio-econ variables
    variables = ["INW_014", "INW_65PL", "WOZWONING"]
    for i in range(len(variables)):
        # drop rows containing secret or lacking data
        drop_numbs = [-99999999, -99999998, -99999997, -99997]
        # choose a variable
        post_nijm_pp = post_nijm[~post_nijm[variables[i]].isin(drop_numbs)]
        # remove nan_values average park area
        post_nijm_drp = post_nijm_pp.dropna(subset=['average_park_area'])
        ##Morans I
        y = post_nijm_drp['average_park_area'].values
        # CHOSE VARIABLE FOR X
        x = post_nijm_drp[variables[i]].values
        w = Queen.from_dataframe(post_nijm)
        w.transform = 'r'
        # calculate moransI
        w = Queen.from_dataframe(post_nijm_drp)
        moran = Moran(y, w)
        moran.I
        moran.p_sim
        # calculate bivariable MoransI
        moran = Moran(y, w)
        moran_bv = Moran_BV(y, x, w)
        moran_loc = Moran_Local(y, w)
        moran_loc_bv = Moran_Local_BV(y, x, w)
        # map visualization
        plot_local_autocorrelation(moran_loc_bv, post_nijm_drp, variables[i])
        plt.suptitle(method+' '+name+ ' '+str(distance)+'m '+str(size)+'ha '+ variables[i].lower())
        plt.savefig(filepath+method+'_'+name+'_'+str(distance)+'_'+str(size)+'_'+ variables[i].lower()+'.png')



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

def maps_green_per_poly (city,dataset, UA_data, EPSG, name,min_size,dist, na_gini_csv, eucl_gini_csv, id):
    import os
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

    if name == 'UA':
        parks_copy = gpd.read_file('./output/' + city[0:4].lower() + '_' + name.lower() + '_parks.shp')
    if name == 'OSM':
        parks_copy = gpd.read_file('./output/' + city[0:4].lower() + '_' + name.lower() + '_parks.shp')

    # select parks based on size
    parks_sel = parks_copy[parks_copy['park_area'] >= min_size]

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
    parks_sel.plot(ax=ax, color='darkgreen', legend=True, label='UGS')
    na_park_area.plot(ax=ax, column='park_area', scheme="user_defined",
                              classification_kwds=dict(bins=[10, 25, 50, 75, 100,]),
                              cmap='Pastel2', alpha=0.7, legend=True, legend_kwds={'title': "Legend"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(city + ' Network UGS(min'+str(min_size)+' ha) total park area(in ha) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_'+dataset+'_'+str(dist)+'_'+str(min_size)+'_park_area_pop_na.png', dpi=500)

    ##euclidean plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    parks_sel.plot(ax=ax, color='darkgreen', legend=True, zorder=1, label='UGS')
    eucl_park_area.plot(ax=ax, column='park_area', scheme="user_defined",
                                classification_kwds=dict(bins=[10, 25, 50, 75, 100,]),
                                cmap='Pastel2', alpha=0.7, legend=True, legend_kwds={'title': "Legend"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(city + ' Euclidean UGS(min'+str(min_size)+' ha) total park area (in ha) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_'+dataset+'_'+str(dist)+'_'+str(min_size)+'_park_area_pop_eucl.png', dpi=500)

    # difference plot
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    parks_sel.plot(ax=ax, color='darkgreen', legend=True, zorder=1, label='UGS')
    eucl_park_area.plot(ax=ax, column='diff_green_per_person_eucl_na', cmap='RdBu', alpha=0.7, legend=True,
                                cax=cax, legend_kwds={'label': "Difference between Euclidean and Network method in ha"})
    ctx.add_basemap(ax, zoom=14, crs=parks_copy.crs, source=ctx.providers.Stamen.TonerLite)
    ax.set_title(
        city + ' difference in UGS total area(in ha) \n per method(Euclidean(+), Network(-)) for dataset ' + dataset)
    ax.axis('off')
    plt.savefig('./output/' + city[:4] + '_'+dataset+'_'+str(dist)+'_'+str(min_size)+'_park_area_diff.png', dpi=500)


