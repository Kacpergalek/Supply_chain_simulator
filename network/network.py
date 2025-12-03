import networkx as nx
import osmnx as ox
import sys
import os
from unidecode import unidecode
import pandas as pd
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from network.simulation_graph import SimulationGraph
from network.graph_reader import GraphManager
from network.europe import europe_countries
from network.europe import top_europe_airports_iata
from utils.graph_helper import haversine_coordinates

class NetworkManager():
    def __init__(self, folder : str = "network_data"):
        self.graph_manager = GraphManager(folder=folder)


    def create_graph(self, region : str = "Europe", road_type : str = "motorway") -> SimulationGraph:
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
    
    def add_infrastructure(self, graph : SimulationGraph, type : str):
        pass


    def load_airports_graph(self, default_capacity : int, default_price : float, airports_filename : str = "airports.dat", routes_filename : str = "routes.dat"):
        crs="EPSG:4326"
        path = Path(__file__).parent.parent
        folder_path = os.path.join(path, "simulation_data", "airports")
        airports_path = os.path.join(folder_path, airports_filename)

        airports_cols = ["ID", "Name", "City", "Country", "IATA", "ICAO", "Lat", "Lon", "Alt", "Timezone", "DST", "Tz", "Type", "Source"]

        df_airports = pd.read_csv(airports_path, names=airports_cols, header=None)
        df_top_airports = df_airports[df_airports["IATA"].isin(top_europe_airports_iata)].copy()

        graph = nx.MultiGraph()
        graph.graph["crs"] = crs
        coords_map = {}
        for i, row in df_top_airports.iterrows():
            iata = row["IATA"]
            node_data = {
                "y" : row["Lat"],
                "x" : row["Lon"],
                "country" : row["Country"],
                "active" : True,
                "type" : str(row["Type"]).lower()
            }
            graph.add_node(iata, **node_data)
            coords_map[iata] = (row["Lat"], row["Lon"])


        routes_path = os.path.join(folder_path, routes_filename)

        routes_cols = ["Airline", "AirlineID", "Source", "SourceID", "Dest", "DestID", "Codeshare", "Stops", "Eq"]
        df_routes = pd.read_csv(routes_path, header=None, names=routes_cols)

        df_top_routes = df_routes[df_routes["Source"].isin(top_europe_airports_iata) & df_routes["Dest"].isin(top_europe_airports_iata)]
        df_top_routes = df_top_routes.drop_duplicates(subset=["Source", "Dest", "Airline"])

        routes = set()
        for i, row in df_top_routes.iterrows():
            aita_source = row["Source"]
            aita_dest = row["Dest"]
            if (aita_source, aita_dest) in routes:
                continue

            routes.add((aita_source, aita_dest))
            
            coords_source = coords_map.get(aita_source)
            coords_dest = coords_map.get(aita_dest)
            if coords_source and coords_dest:
                length = haversine_coordinates(coords_source[0], coords_source[1], coords_dest[0], coords_dest[1], metric="length")
                
                edge_data = {
                    "airline" : row["Airline"],
                    "length" : length,
                    "capacity" : default_capacity,
                    "cost" : length/1000 * default_price,
                    "flow" : 0
                }
                graph.add_edge(aita_source, aita_dest, **edge_data)

        return SimulationGraph(default_capacity, default_price, incoming_graph_data=graph)
