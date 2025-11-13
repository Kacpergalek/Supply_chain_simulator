import json
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt
from dashboard.dashboards_manager import DashboardsManager
from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_random_nodes_to_disrupt

reader = GraphManager()
#dash = DashboardsManager()
graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
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

find_random_nodes_to_disrupt(graph, max_depth=30)

