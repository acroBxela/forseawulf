import pandas as pd
import geopandas as gpd
import networkx as nx
import json
from networkx.readwrite import json_graph


def gdf_to_nx_graph(gdf, neighbors_col='neighbors'):
    G = nx.Graph()
    gdf = gdf.drop(columns=['geometry'])
    for idx, row in gdf.iterrows():
        node_id = idx  # or use any unique identifier
        G.add_node(node_id, **row.to_dict())
    for idx, row in gdf.iterrows():
        node_id = idx  # or use any unique identifier
        
        neighbors = row[neighbors_col].split(",")
        for neighbor in neighbors:
            if not G.has_edge(node_id, int(neighbor)):
                G.add_edge(node_id, int(neighbor))
    return G

gdf = gpd.read_file("adj.geojson")
gdf['AREA'] = gdf.geometry.area

G = gdf_to_nx_graph(gdf, neighbors_col='neighbors')
print(G)
json_graph = json_graph.adjacency_data(G)

with open('networkx_json_graph.json', 'w') as outfile:
    json.dump(json_graph, outfile)
