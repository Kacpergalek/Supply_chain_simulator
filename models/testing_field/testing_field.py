import json
from pathlib import Path
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from network.countries import europe_countries
from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt
from dashboard.dashboards_manager import DashboardsManager
from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_random_nodes_to_disrupt
from network.network import NetworkManager

# reader = GraphManager()
#dash = DashboardsManager()
# graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
# for node in graph.nodes:
#     print(node)
# print(graph.nodes[1418295070], graph.nodes[1418295070].get("x", None))
# print(graph.nodes[1418295070].get("active", None))
# simulation = Simulation(10, 'day', graph)
# simulation.run()

#find_nodes_to_disrupt(graph)
#dash.get_stats()

# nodes = bfs_limited(graph, 1418295070, max_depth=10)
# print(len(nodes))


# graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
# self.network = SimulationGraph(default_capacity=graph.default_capacity,
#                                    default_price=graph.default_price,
#                                    incoming_graph_data=graph)
# find_random_nodes_to_disrupt(graph, max_depth=30)



# time_start = time.time()
# reader = GraphManager()
# map = {}
# for country in europe_countries:
#     graph = reader.load_pickle_graph(f"{country}_motorway.pkl")
#     if graph:
#         map[country] = graph
# print(f"Czas inicjalizowania grafu: {time.time() - time_start}")
# print(list(map.keys()))

sim = Simulation()
sim.inject_parameters(15, "day")
sim.run()

# time_start = time.time()
# network = NetworkManager()
# graph = network.create_graph()
# print(f"Czas inicjalizowania grafu: {time.time() - time_start}")

# node1 = graph.get_nearest_node(47, 16)
# node2 = graph.get_nearest_node(52, 6.5)
# path = graph.astar(node1, node2)
# print(len(path))
