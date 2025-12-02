import networkx as nx
import osmnx as ox
import sys
import os
from unidecode import unidecode
import numpy as np
from sklearn.neighbors import BallTree
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