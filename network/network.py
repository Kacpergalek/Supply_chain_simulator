import networkx as nx
import sys
import os

import numpy as np
from sklearn.neighbors import BallTree
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
    def __init__(self, folder : str = "input_data/network_data"):
        self.graph_manager = GraphManager(folder=folder)


    def create_graph(self, region : str = "Europe", road_type : str = "motorway") -> SimulationGraph:
        if region == "Europe":
            full_graph = self.get_graph_from_file(europe_countries[0], road_type=road_type)
            for country in europe_countries[1:]:
                graph = self.get_graph_from_file(country, road_type=road_type)
                full_graph = full_graph.compose(graph)
        return full_graph


    def get_graph_from_file(self, country : str, road_type : str = "motorway") -> SimulationGraph:
        file_path = f"{unidecode(country).lower().replace(" ", "_")}_{road_type}.pkl"
        sim_graph = self.graph_manager.load_pickle_graph(file_path)
        if sim_graph is not None:
            for node, data in sim_graph.nodes(data=True):
                if "country" not in data:
                    data["country"] = unidecode(country).lower().replace(" ", "_")
        sim_graph = self.merge_graph_components(sim_graph, max_dist_km=70)
        return sim_graph

    def add_infrastructure(self, graph : SimulationGraph, type : str):
        pass


    def load_airports_graph(self, default_capacity : int, default_price : float, airports_filename : str = "airports.dat", routes_filename : str = "routes.dat"):
        crs="EPSG:4326"
        path = Path(__file__).parent.parent
        folder_path = os.path.join(path, "input_data", "simulation_data", "airports")
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

    def merge_graph_components(self, graph: SimulationGraph, max_dist_km: float = 50.0) -> SimulationGraph:
        # 1. Get all weakly connected components (directed graph needs weakly connected)
        # Sort them by size (number of nodes), largest first.
        components = sorted(nx.connected_components(graph), key=len, reverse=True)
        print(f"Found {len(components)} connected components.")

        if len(components) < 2:
            return graph

        # The largest component is our "Main" graph.
        main_component_nodes = list(components[0])

        # 2. Build a BallTree for the main component to allow fast spatial searching
        # Extract lat/lon. OSMnx stores them as y (lat) and x (lon).
        # BallTree expects radians for haversine distance.
        main_coords = np.array([[np.deg2rad(graph.nodes[n]['y']), np.deg2rad(graph.nodes[n]['x'])]
                                for n in main_component_nodes])

        # Metric 'haversine' takes inputs in radians and returns distance in radians
        tree = BallTree(main_coords, metric='haversine')

        earth_radius_km = 6371.0
        max_dist_rad = max_dist_km / earth_radius_km

        # 3. Iterate through the smaller components (disconnected parts)
        links_created = 0

        for comp_nodes in components[1:]:
            # Find "dead ends" in this component.
            # In a directed graph, we look for total degree <= 1 or specifically out_degree=0 / in_degree=0.
            # Using total degree <= 2 allows for nodes at the very tip of a road.
            candidates = [n for n in comp_nodes if graph.degree[n] <= 1]

            # If the component is a ring/loop, it has no dead ends. In that case, use all nodes.
            if not candidates:
                candidates = list(comp_nodes)

            # Extract coordinates for candidates
            cand_coords = np.array([[np.deg2rad(graph.nodes[n]['y']), np.deg2rad(graph.nodes[n]['x'])]
                                    for n in candidates])

            # Query the tree for the nearest node in the main component
            # query_radius returns indices and distances
            indices, distances = tree.query_radius(cand_coords, r=max_dist_rad, return_distance=True, sort_results=True)

            best_link = None
            min_dist = float('inf')

            # Check results to find the absolute closest valid connection for this entire component
            for i, (idx_list, dist_list) in enumerate(zip(indices, distances)):
                if len(dist_list) > 0:
                    # dist_list[0] is the closest because we sorted results
                    if dist_list[0] < min_dist:
                        min_dist = dist_list[0]
                        source_node = candidates[i]
                        target_node = main_component_nodes[idx_list[0]]
                        best_link = (source_node, target_node)

            # If a link was found within range, add it to the graph
            if best_link:
                u, v = best_link
                dist_km = min_dist * earth_radius_km
                dist_m = dist_km * 1000

                # Add bidirectional edge (motorway connection)
                # We add 'artificial_link' tag so we can identify these later if needed
                graph.add_edge(u, v, length=dist_m, type="artificial_connection")
                graph.add_edge(v, u, length=dist_m, type="artificial_connection")

                print(f"Connected component (size {len(comp_nodes)}) to main graph. Dist: {dist_km:.2f}km")
                links_created += 1
            else:
                print(f"Could not connect component (size {len(comp_nodes)}) - closest node > {max_dist_km}km")

        print(f"Merge complete. Created {links_created} new connections.")
        return graph