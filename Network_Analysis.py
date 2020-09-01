## redo Network analysis

#imports
import matplotlib.pyplot as plt
import osmnx as ox
import geopandas as gpd
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Point, LineString, Polygon



#start data
city = "Maastricht"
UA_data = gpd.read_file('./data/NL505L1_MAASTRICHT/Shapefiles/NL505L1_MAASTRICHT_UA2012.shp')
EPSG = 'EPSG:28992'

# Extract city boundary and road network
city_boundary = ox.geocode_to_gdf(city, buffer_dist= 500)
roads_city = ox.graph_from_place(city, retain_all= True, network_type='all', buffer_dist=500, which_result=2)
nodes, city_roads = ox.graph_to_gdfs(roads_city)

#select pop polygons
city_shp_pop = UA_data[UA_data['Pop2012'] > 0]

#extract park_data
parks_landuse_tags = ['grass', 'allotments', 'meadow', 'forest']
x = ox.footprints_from_place("Maastricht", footprint_type='landuse')
# only select relevant green space tags from the landuse extraction
parks = x[x['landuse'].isin(parks_landuse_tags)]
# only keep relevant columns
parks_clean = parks[["landuse", "geometry"]].copy()
parks_clean["park_area"] = parks_clean.area

#transform to similar projection
projection = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
#projection = 'EPSG:28992'

city_shp_pop_tf = city_shp_pop.to_crs(projection)
parks_clean_tf = parks_clean.to_crs(projection)
roads_city_tf = ox.project_graph(roads_city, to_crs=projection)

#project to projected crs to create accurate centroids

#create centroid nodes per pop polygon and park
city_shp_pop_cen = city_shp_pop_tf.centroid
parks_clean_cen = parks_clean_tf.centroid
city_shp_pop_cen_1 = city_shp_pop_cen[0:1]

#re-project back



#find nears roadnetwork node per park and pop polygon
city_shp_pop_cen["nearest_node"] = ox.get_nearest_node(roads_city, city_shp_pop_cen_1)
city_shp_pop_nn = ox.get_nearest_nodes(roads_city, city_shp_pop.centroid.x, city_shp_pop.centroid.y)
parks_clean_cen["nearest_node"] = ox.get_nearest_nodes(roads_city, parks_clean_cen.x, parks_clean_cen.y)
parks_nn = ox.get_nearest_nodes(roads_city, parks_clean_cen.centroid.x, parks_clean_cen.centroid.y)
parks_clean_cen["nearest_node"] = ox.get_nearest_nodes(roads_city, parks_clean_cen.centroid.x, parks_clean_cen.centroid.y)
parks_clean_cen["nearest_node"] =
parks_nn_list = parks_nn.tolist()

parks_clean_cen.to_crs(projection)

#get nodes from isochrome
pop_cen_nodes = nx.ego_graph(roads_city, city_shp_pop.nearest_node, radius=300)

#transform to gdf

#see if there is overlap between the pop_cen_nodes and the park_road_nodes (find a way to join the data)
#use intersect to see which points overlap
park_na_join = gpd.sjoin(parks_clean_cen["nearest_node"], city_shp_pop_cen["nearest_node"], how="inner", op="intersects")

#then do the same as for the euclidean distance





#per centroid and park find nearest road node
for i in city_shp_pop_cen:
    city_shp_pop["node"] =ox.get_nearest_node(roads_city, city_shp_pop_cen[i])

pop_nodes = ox.get_nearest_nodes(roads_city, city_shp_pop.centroid.x, city_shp_pop.centroid.y)
park_nodes = ox.get_nearest_nodes(roads_city, parks_clean_cen.x, parks_clean_cen.y)



#all nodes reached by pop polygon within certain distance
pop_nodes_reached = nx.single_source_shortest_path(roads_city, pop_nodes,cutoff=300)


#check if found node corresponds with a park node

#add park node to the



##Retry isochrone

place = 'Maastricht'
network_type = 'all'
UA_data = gpd.read_file('./data/NL505L1_MAASTRICHT/Shapefiles/NL505L1_MAASTRICHT_UA2012.shp')
projection = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

#other
#trip_time = 3
#travel_speed = 6

#get road network
roads_grph = ox.graph_from_place(place, network_type=network_type)
roads_grph = ox.project_graph(roads_grph, to_crs=projection)

# add an edge attribute for time in minutes required to traverse each edge
#meters_per_minute = travel_speed * 1000 / 60 #km per hour to m per minute
#for u, v, k, data in roads_grph.edges(data=True, keys=True):
 #   data['time'] = data['length'] / meters_per_minute




#select pop polygons
pop = UA_data[UA_data['Pop2012'] > 0]

#get correct EPGS
pop_tf = pop.to_crs(projection)
pop_tf = ox.project_gdf(pop_tf)
x, y = pop_tf.geometry[0:1].unary_union.centroid.xy

#pop_nn = ox.get_nearest_nodes(roads_grph, pop_tf.centroid.x,pop_tf.centroid.y)
pop_nn_1 =ox.get_nearest_node(roads_grph,(y[0], x[0]))

subgraph = nx.ego_graph(roads_grph, pop_nn_1, radius= 700, distance= "length")

ox.plot_graph(subgraph)

def make_iso_polys(G, edge_buff=25, node_buff=50, infill=False):
    isochrone_polys = []
    subgraph = nx.ego_graph(G, pop_nn_1, radius=700, distance='length')

    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame({'id': list(subgraph.nodes())}, geometry=node_points)
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


iso_poly = make_iso_polys(roads_grph)

iso_poly[0:1].plot()

fig, ax = ox.plot_graph(roads_grph, show=False, close=False, edge_color='#999999', edge_alpha=0.2,
                        node_size=0, bgcolor='k')

for polygon in iso_poly:
    patch = PolygonPatch(polygon, fc= "red",ec='none', alpha=0.6, zorder=-1)
    ax.add_patch(patch)
plt.show()

iso_poly.to_file("'./output/iso_poly.shp")

iso_poly




















