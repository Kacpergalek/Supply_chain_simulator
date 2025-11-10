import json
from pathlib import Path

from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt

reader = GraphManager()
graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
# print(graph.nodes[1418295070], graph.nodes[1418295070].get("x", None))
# simulation = Simulation(10, 'day', graph)
# simulation.run()

find_nodes_to_disrupt(graph)
