import pandas as pd
import networkx as nx


nodes = pd.read_csv("../data/nodes.csv")
edges = pd.read_csv("../data/edges.csv")


G = nx.DiGraph()


for _, row in nodes.iterrows():
    G.add_node(row['id'], name=row['name'], country=row['country'], type=row['type'], lat=row['lat'], lon=row['lon'])


for _, row in edges.iterrows():
    G.add_edge(row['source_id'], row['target_id'], transport=row['transport_type'],
               distance=row['distance_km'], capacity=row['capacity'], lead_time=row['base_lead_time'])

print("Graf gotowy. Liczba węzłów:", G.number_of_nodes())
print("Liczba krawędzi:", G.number_of_edges())
