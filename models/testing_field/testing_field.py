import json
import os
import pickle
from pathlib import Path

# import numpy as np

# from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager

# path = Path(__file__).parent.parent.parent
# with open(f'{path}/network_data/poland_motorway_trunk_primary.pkl', "rb") as pickle_file:
#     graph = pickle.load(pickle_file)
# print(graph)
reader = GraphManager()
graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
# print(graph.nodes[1418295070], graph.nodes[1418295070].get("x", None))
# print(graph.edges.values())
# simulation = Simulation(10, 'day', graph)
# simulation.run()

# for node in graph.nodes:
#     print(node, graph.nodes[node])

i = 0
nodes_for_disruption = []
for node in graph.nodes:
    nodes_for_disruption.append(node)
    i += 1
    if i > 10:
        break

path = Path(__file__).parent.parent.parent
print(f"Path: {path}")
# with open('data.json', 'w') as f:
#     json.dump(nodes_for_disruption, f, indent=4)

# print(graph.edges[nodes_for_disruption[0], nodes_for_disruption[1], 0])
