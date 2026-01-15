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


time_start = time.time()
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
reader.save_pickle_file("world_without_ports_motorway.pkl", graph)
airplane_graph = network.load_airports_graph(default_capacity=10, default_price=10)
graph.compose(airplane_graph)
seaport_graph = network.load_seaports_graph(default_capacity=5, default_price=1)
graph.compose(seaport_graph)
graph.connect_airports_seaports(default_capacity=1000, default_price=0.5)

reader.save_pickle_file("world_ports_motorway.pkl", graph)