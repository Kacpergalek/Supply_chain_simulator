import json
from pathlib import Path
import sys
import os
import time
import osmnx as ox
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from network.europe import europe_countries
from models.simluation.engine import Simulation
from network.graph_reader import GraphManager
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt
from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_random_nodes_to_disrupt
from network.network import NetworkManager
from models.agents.exporter_agent import ExporterAgent
from models.agents.agent_manager import AgentManager
from utils.graph_helper import normalize_country

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

""" time_start = time.time()
network = NetworkManager()
reader = GraphManager()


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


""" graph = network.load_seaports_graph(10, 100)
for n, data in graph.nodes(data=True):
    print(data) 

for u, v, k, data in graph.edges(data=True, keys=True):
    print(f"Start: {u}, end: {v}, key: {k}, data: {data}") """


""" graph = network.get_graph_from_file("europe")
airplane_graph = network.load_airports_graph(default_capacity=10, default_price=1000)
graph.compose(airplane_graph)
seaport_graph = network.load_seaports_graph(default_capacity=5, default_price=500)
graph.compose(seaport_graph)
graph.connect_airports_seaports(default_capacity=1000, default_price=0.5)

node1 = graph.get_nearest_node(52, 21)
node2 = graph.get_nearest_node(52.5, 13)

astar_time = time.time()
path_length = graph.astar(node1, node2)
print(f"Liczba nodów: {len(path_length)}, czas wykonywania astara: {round(time.time() - astar_time, 2)}")
print(path_length)

path_cost = graph.astar(node1, node2, metric="cost")
print(f"Liczba nodów: {len(path_cost)}, czas wykonywania astara: {round(time.time() - astar_time, 2)}")
print(path_cost) """

network = NetworkManager()
""" graph = network.get_graph_from_file("europe")
airplane_graph = network.load_airports_graph(default_capacity=10, default_price=7)
graph.compose(airplane_graph)
seaport_graph = network.load_seaports_graph(default_capacity=5, default_price=1)
graph.compose(seaport_graph)
graph.connect_airports_seaports(default_capacity=1000, default_price=0.5)

reader = GraphManager()
reader.save_pickle_file("world_.pkl", graph) """

""" graph = network.get_graph_from_file("world", road_type="")
agent_manager = AgentManager()
initialized = agent_manager.initialize_agents(graph)
material_exporters = initialized["material_exporters"]
importer_exporters = initialized["importer_exporters"]
product_importers = initialized["product_importers"]
material_paths = initialized["material_routes"]
product_paths = initialized["product_routes"]
node_to_exporter = {int(agent.node_id): agent for agent in importer_exporters + material_exporters}
product_deliveries = agent_manager.delivery_manager.initialize_deliveries(graph, node_to_exporter, product_paths, True)

find_nodes_to_disrupt(graph, product_deliveries, 50) """



""" time_start = time.time()
network = NetworkManager()
reader = GraphManager()


graph = network.create_graph(region="world")
print(f"Czas inicjalizowania grafu: {time.time() - time_start}")
consolidate_start_time = time.time()
graph.consolidate_roads(tolerance=15)



empty_graph = graph.coherence(threshold=10000)
reader.save_pickle_file("added_world_edges_motorway.pkl", empty_graph)
print(f"Consolidation time: {time.time() - consolidate_start_time}")
# load airports and seaports

reader.save_pickle_file("world_without_ports_motorway.pkl", graph) """


graph = network.get_graph_from_file("world_without_ports")
airplane_graph = network.load_airports_graph(default_capacity=1000, default_price=100)
graph.compose(airplane_graph)
seaport_graph = network.load_seaports_graph(default_capacity=500, default_price=60)
graph.compose(seaport_graph)
graph.connect_airports_seaports(default_capacity=1000, default_price=0.5)

reader = GraphManager()
reader.save_pickle_file("world_ports_motorway.pkl", graph)