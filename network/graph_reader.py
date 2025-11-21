import os
import pickle
import sys
from pathlib import Path

import networkx as nx
import osmnx as ox
import json
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from network.simulation_graph import SimulationGraph


class GraphManager():
    def __init__(self, folder="network_data"):
        self.folder = folder


    def load_pickle_graph(self, pickle_file_name) -> SimulationGraph:
        # project_root = os.path.abspath("..")
        # if project_root not in sys.path:
        #     sys.path.append(project_root)

        path = Path(__file__).parent.parent
        json_file_name = pickle_file_name.split(".")[0] + ".json"
        try:
            json_path = os.path.join(path, self.folder, json_file_name)
            with open(json_path, "r") as json_file:
                attributes = json.load(json_file)
        except Exception as e:
            print(f"Error loading json file: {e}")
            attributes = {
                "default_capacity" : 1000,
                "default_price" : 0.5
            }

        try:
            pickle_path = os.path.join(path, self.folder, pickle_file_name)
            with open(pickle_path, "rb") as pickle_file:
                graph = pickle.load(pickle_file)
            sim_graph = SimulationGraph(incoming_graph_data = graph, 
                                            default_capacity=attributes["default_capacity"], 
                                            default_price=attributes["default_price"])
        except Exception as e:
            print(f"Error loading pickle: {e}")
            return None
        return sim_graph
        
    

    def save_pickle_file(self, file_name, graph):
        if isinstance(graph, SimulationGraph):
            attributes = graph.get_additional_attributes()
            json_file_name = file_name.split(".")[0] + ".json"
            with open(f"../{self.folder}/{json_file_name}", "w") as json_file:
                json.dump(attributes, json_file, indent=4)
            with open(f"../{self.folder}/{file_name}", "wb") as pickle_file:
                pickle.dump(nx.MultiDiGraph(graph), pickle_file)
        else:
            with open(f"../{self.folder}/{file_name}", "wb") as pickle_file:
                pickle.dump(graph, pickle_file)


    def save_graphml_file(self, file_name, graph):
        if isinstance(graph, SimulationGraph):
            ox.save_graphml(nx.MultiDiGraph(graph), f"../{self.folder}/{file_name}")
        else: 
            ox.save_graphml(graph, f"../{self.folder}/{file_name}")
