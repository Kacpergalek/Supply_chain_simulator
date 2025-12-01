import networkx as nx
import osmnx as ox
import sys
import os
from unidecode import unidecode
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from network.simulation_graph import SimulationGraph
from network.graph_reader import GraphManager
from network.countries import europe_countries

class NetworkManager():
    def __init__(self, folder : str = "network_data"):
        self.graph_manager = GraphManager(folder=folder)


    def create_graph(self, region : str = "Europe", road_type : str = "motorway"):
        if region == "Europe":
            full_graph = self.get_graph_from_file(europe_countries[0], road_type=road_type)
            for country in europe_countries[1:]:
                graph = self.get_graph_from_file(country, road_type=road_type)
                full_graph.compose(graph)
        return full_graph


    def get_graph_from_file(self, country : str, road_type : str = "motorway") -> SimulationGraph:
        file_path = f"{unidecode(country).lower().replace(" ", "_")}_{road_type}.pkl"
        sim_graph = self.graph_manager.load_pickle_graph(file_path)
        if sim_graph is not None:
            for node, data in sim_graph.nodes(data=True):
                if "country" not in data:
                    data["country"] = unidecode(country).lower().replace(" ", "_")
        return sim_graph
