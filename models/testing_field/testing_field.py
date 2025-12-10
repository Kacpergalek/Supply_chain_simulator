import json
from pathlib import Path
import sys
import os
import time
import osmnx as ox
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from network.europe import europe_countries
from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt
from dashboard.dashboards_manager import DashboardsManager
from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_random_nodes_to_disrupt
from network.network import NetworkManager
from models.agents.exporter_agent import ExporterAgent

# reader = GraphManager()
# dash = DashboardsManager()
# graph = reader.load_pickle_graph("europe_motorway.pkl")
# for u, v, d in graph.edges(data=True):
#     print(d)
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

# sim = Simulation()
# sim.inject_parameters(15, "day")
# sim.run()

time_start = time.time()
network = NetworkManager()
reader = GraphManager()

""" 
graph = network.create_graph()
# graph = network.get_graph_from_file("consolidated_europe")  
print(f"Czas inicjalizowania grafu: {time.time() - time_start}")
consolidate_start_time = time.time()
graph.consolidate_roads(tolerance=15)

reader.save_pickle_file("consolidated_europe_motorway.pkl", graph)


empty_graph = graph.coherence(threshold=10000)
reader.save_pickle_file("added_edges_motorway.pkl", empty_graph)

reader.save_pickle_file("europe_motorway.pkl", graph)
print(f"Consolidation time: {time.time() - consolidate_start_time}") """



""" graph = reader.load_pickle_graph("europe_motorway.pkl")
print(f"Czas inicjalizowania grafu: {time.time() - time_start}")
node1 = graph.get_nearest_node(52, 21)
node2 = graph.get_nearest_node(52.5, 13)

astar_time = time.time()
path = graph.astar(node1, node2)
print(f"Liczba nodów: {len(path)}, czas wykonywania astara: {round(time.time() - astar_time, 2)}")
# graph.get_road_length(node1, node2)
# coords = (51.20, 51.10, 15.05, 14.90)
# expo_agent = ExporterAgent(1, node1)
# path = expo_agent.find_cheapest_path(graph, node2)
europe = graph.get_border_polygon()
airports_graph = ox.graph_from_polygon(europe, custom_filter=filter)
print(len(list(airports_graph.nodes()))) """


graph = network.load_airports_graph(10, 100)
for n, data in graph.nodes(data=True):
    print(data) 

for u, v, k, data in graph.edges(data=True, keys=True):
    print(f"Start: {u}, end: {v}, key: {k}, data: {data}")
