import networkx as nx
import osmnx as ox
from queue import PriorityQueue, Queue
from scipy.spatial import cKDTree
import heapq
import math
import numpy as np 
from shapely import Polygon
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.graph_helper import haversine_coordinates
from network.transport_types import MinimalCostType
class SimulationGraph(nx.MultiGraph):
    def __init__(self, default_capacity, default_price, incoming_graph_data=None, multigraph_input = None, type : str = "road", **attr):
        super().__init__(incoming_graph_data, multigraph_input, **attr)
        self.default_capacity = default_capacity
        self.default_price = default_price
        for u, v, key, data in self.edges(data=True, keys=True):
            if "capacity" not in data:
                data["capacity"] = self.default_capacity
            if "cost" not in data:
                data["cost"] = data["length"]/1000 * self.default_price
            if "flow" not in data:
                data["flow"] = 0
            if "type" not in data:
                data["type"] = type
            if "max_capacity" not in data:
                data["max_capacity"] = self.default_capacity
        
        for node, data in self.nodes(data=True):
            if "active" not in data:
                data["active"] = True
            if "type" not in data:
                data["type"] = type # będziemy dodawać firmy/dostawców
            


    @classmethod
    def from_osmnx(cls, place, default_capacity=1000, default_price=0.5, network_type="drive", custom_filter='["highway"~"motorway"]', **kwargs):
        graph = ox.graph_from_place(place, network_type=network_type, custom_filter=custom_filter, **kwargs)
        graph = graph.to_undirected()
        return cls(default_capacity, default_price, incoming_graph_data=graph)
    

    def remove_edges_attribute(self, attributes: list):
        for u, v, key, data in self.edges(data=True, keys=True):
            for attribute in attributes:
                data.pop(attribute, None)
        
    

    def set_capacity(self, capacity, osmids=None, path=None):
        if path is not None:
            for u, v in zip(path[:-1], path[1:]):
                for key in self[u][v]:
                    self[u][v][key]["capacity"] = capacity
        elif osmids is not None:
            for u, v, key, data in self.edges(data=True, keys=True):
                edge_osmids = data.get("osmid")
                if (isinstance(edge_osmids, list) and any(edge_osmid in osmids for edge_osmid in edge_osmids)) or (isinstance(edge_osmids, int) and edge_osmids in osmids):
                    data["capacity"] = capacity
        
    
    def set_price(self, price, osmids=None, path=None):
        if path is not None:
            for u, v in zip(path[:-1], path[1:]):
                for key in self[u][v]:
                    self[u][v][key]["cost"] = price
        elif osmids is not None:
            for u, v, key, data in self.edges(data=True, keys=True):
                edge_osmids = data.get("osmid")
                if (isinstance(edge_osmids, list) and any(edge_osmid in osmids for edge_osmid in edge_osmids)) or (isinstance(edge_osmids, int) and edge_osmids in osmids):
                    data["cost"] = price


    def deactivate_nodes(self, nodes : list[int]):
        for node, data in self.nodes(data=True):
            if node in nodes:
                data["active"] = False


    def activate_nodes(self, nodes : list[int]):
        for node, data in self.nodes(data=True):
            if node in nodes:
                data["active"] = True


    def safe_shortest_path(self, start_node : int | str, end_node : int | str, weight : str = "cost"):
        active_sim_graph = self.get_active_graph()
        return nx.shortest_path(active_sim_graph, start_node, end_node, weight=weight)


    def send_goods(self, amount, path=None, osmids=None):
        if path is not None:
            for u, v in zip(path[:-1], path[1:]):
                for key in self[u][v]:
                    self[u][v][key]["flow"] += amount
        elif osmids is not None:
            for u, v, key, data in self.edges(data=True, keys=True):
                edge_osmids = data.get("osmid")
                if (isinstance(edge_osmids, list) and any(edge_osmid in osmids for edge_osmid in edge_osmids)) or (isinstance(edge_osmids, int) and edge_osmids in osmids):
                    data["flow"] += amount


    def reduce_capacity(self, capacity=1, path=None, osmids=None):
        if path is not None:
            for u, v in zip(path[:-1], path[1:]):
                for key in self[u][v]:
                    self[u][v][key]["capacity"] -= capacity
        elif osmids is not None:
            for u, v, key, data in self.edges(data=True, keys=True):
                edge_osmids = data.get("osmid")
                if (isinstance(edge_osmids, list) and any(edge_osmid in osmids for edge_osmid in edge_osmids)) or (isinstance(edge_osmids, int) and edge_osmids in osmids):
                    data["capacity"] -= capacity


    def get_additional_attributes(self):
        return {
            "default_capacity" : self.default_capacity,
            "default_price" : self.default_price
        }
    
    
    def compose(self, graph):
        att1 = self.get_additional_attributes()
        multigraph2 = nx.MultiGraph(graph)

        self.add_nodes_from(multigraph2.nodes(data=True))
        self.add_edges_from(multigraph2.edges(keys=True, data=True))

        # mutligraph1 = nx.MultiGraph(self)
        # composed_graph = nx.compose(mutligraph1, multigraph2)
        # self = self.__class__(default_capacity = att1["default_capacity"], default_price = att1["default_price"], incoming_graph_data = composed_graph)
        return self

    def display(self, coordinates : tuple = None):
        graph = nx.MultiGraph(self)

        if coordinates == None:
            ox.plot_graph(graph)
        else:
            north = coordinates[0]
            south = coordinates[1]
            east = coordinates[2]
            west = coordinates[3] 
            sub_graph = ox.truncate.truncate_graph_bbox(graph, (north, south, east, west))
            ox.plot_graph(sub_graph)


    def safe_astar_path(self, start_node : int | str, end_node : int | str, weight : str = "length"):
        active_sim_graph = self.get_active_graph()
        return nx.astar_path(active_sim_graph, start_node, end_node, weight=weight)


    def get_active_graph(self):
        mutligraf = nx.MultiGraph(self)
        sim_graph_cpy = self.__class__(default_capacity = self.default_capacity, default_price = self.default_price, incoming_graph_data = mutligraf)

        deactivated_nodes = [node for node, data in sim_graph_cpy.nodes(data=True) if data["active"] == False]

        sim_graph_cpy.remove_nodes_from(deactivated_nodes)
        return sim_graph_cpy
    

    def reconstruct_path(self, came_from : dict, current : int):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1] 


    def astar(self, start_node: int, end_node: int, metric: str = "length"):
        active_sim_graph = self.get_active_graph()
        entry_queue = []
        heapq.heappush(entry_queue, (0.0, 0.0, start_node))
        
        came_from = {}
        g_score = {start_node: 0.0}

        while len(entry_queue) > 0:
            # print(g_score)
            _, current_g, current_node = heapq.heappop(entry_queue)

            if current_node == end_node:
                return self.reconstruct_path(came_from, current_node)

            # if current_g > g_score.get(current_node, float('inf')):
            #     continue

            for neighbour in self.neighbors(current_node):
                neighbour_g = current_g + self.haversine_nodes(current_node, neighbour, metric)
                
                if neighbour_g < g_score.get(neighbour, float('inf')):
                    came_from[neighbour] = current_node
                    g_score[neighbour] = neighbour_g
                    
                    neighbour_h = self.heuristic(neighbour, end_node, metric)
                    neighbour_f = neighbour_g + neighbour_h
                    
                    heapq.heappush(entry_queue, (neighbour_f, neighbour_g, neighbour))
        return None


    # def get_road_length(self, node_start : int, node_end : int, metric : str = "length"):
    #     if metric == "length":
    #         edges = list(self[node_start][node_end].values())
    #         print(edges)


    def heuristic(self, start_node : int | str, end_node : int | str, metric : str, mode : str = "euclidean"):
        if mode == "euclidean":
            return self.haversine_nodes(start_node, end_node, metric)
        if mode == "manhattan":
            pass
        return None


    def haversine_nodes(self, node1 : int | str, node2 : int | str, metric : str):
        if ((self.nodes()[node1]["type"] == "seaport" and self.nodes()[node2]["type"] == "seaport") or \
            (self.nodes()[node1]["type"] == "airport" and self.nodes()[node2]["type"] == "airport")) and \
            (metric in ("length", "cost")):
            min_metric = float("inf")
            for k, data in self[node1][node2].items():
                value = data.get(metric, float("inf"))
                if value < min_metric:
                    min_metric = value
            return min_metric
        
        lon1 = self.nodes()[node1]["x"]
        lat1 = self.nodes()[node1]["y"]
        lon2 = self.nodes()[node2]["x"]
        lat2 = self.nodes()[node2]["y"]

        R = 6371  # promień Ziemi

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if metric == "length":
            return R * c * 1000
        
        if metric == "cost":
            min_road_cost = float(MinimalCostType.ROAD.value)
            return min_road_cost * R * c
        return None


        
        
    def get_nearest_node(self, lattitude : float = None, longitude : float = None, node : int | str = None):
        min_dist = float("inf")
        nearest_node = None
        if longitude is None and lattitude is None and node is not None:
            lattitude = self.nodes(data=True)[node]["y"]
            longitude = self.nodes(data=True)[node]["x"]

        for node_id, data in self.nodes(data=True):
            node_lat = data.get('y', None)
            node_lon = data.get('x', None)
            if node_lat is None or node_lon is None or node_id == node or data["type"] in ("airport", "seaport"):
                continue

            dist = haversine_coordinates(lattitude, longitude, node_lat, node_lon, "length")
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id

        return nearest_node
    

    def consolidate_roads(self, tolerance : int = 15):
        G_proj = ox.project_graph(nx.MultiGraph(self))

        G_clean = ox.consolidate_intersections(
            G_proj, 
            tolerance=tolerance, 
            rebuild_graph=True, 
            dead_ends=False 
        )

        print(f"Liczba węzłów przed: {len(self.nodes)}")
        print(f"Liczba węzłów po: {len(G_clean.nodes)}")
        G_final = ox.project_graph(G_clean, to_crs="EPSG:4326")

        self.clear()
        self.graph.update(G_final.graph)
        self.add_nodes_from(G_final.nodes(data=True))
        self.add_edges_from(G_final.edges(data=True, keys=True))
    

    def coherence(self, threshold: float = 100, type : str = "country"):
        G_proj = ox.project_graph(nx.MultiGraph(self))

        empty_graph = nx.MultiGraph()
        empty_graph.graph = G_proj.graph.copy()
        
        end_nodes = [n for n, d in G_proj.degree() if d == 1]
        all_nodes = list(G_proj.nodes())
        
        if not end_nodes:
            print("Brak wiszących węzłów do naprawy.")
            return

        node_coords = np.array([[G_proj.nodes[n]['x'], G_proj.nodes[n]['y']] for n in all_nodes])
        tree = cKDTree(node_coords)
        
        count_fixed = 0
        visited_nodes = set()
        for node in end_nodes:
            node_pos = [G_proj.nodes[node]['x'], G_proj.nodes[node]['y']]

            idxs = tree.query_ball_point(node_pos, threshold, workers=-1)            
            nearest_node, distance = self.get_nearest_index(G_proj, idxs, node, type)

            if nearest_node is not None and not G_proj.has_edge(node, nearest_node) and node not in visited_nodes and nearest_node not in visited_nodes:
                
                edges = list(G_proj.edges(node, data=True)) or list(G_proj.in_edges(node, data=True))
                ref_data = edges[0][2] if edges else {}

                new_edge_data = {
                    'length': distance,
                    'highway': ref_data.get('highway', 'motorway'),
                    'oneway': False,
                    'maxspeed': ref_data.get('maxspeed', '50')
                }
                
                G_proj.add_edge(node, nearest_node, **new_edge_data)

                empty_graph.add_node(node, **G_proj.nodes[node])
                empty_graph.add_node(nearest_node, **G_proj.nodes[nearest_node])
                empty_graph.add_edge(node, nearest_node, **new_edge_data)
                
                count_fixed += 1
                visited_nodes.add(nearest_node)

            visited_nodes.add(node)

        print(f"Naprawiono (połączono) {count_fixed} przerwanych dróg.")

        G_final = ox.project_graph(G_proj, to_crs="EPSG:4326")
        self.clear()
        self.add_nodes_from(G_final.nodes(data=True))
        self.add_edges_from(G_final.edges(keys=True, data=True))
        self.graph.update(G_final.graph)
        final_empty = ox.project_graph(empty_graph, to_crs="EPSG:4326")
        final_empty.graph.update(empty_graph.graph)
        return final_empty
    

    def get_nearest_index(self, G_proj : nx.MultiGraph, indexes : list, node : int | str, type : str):
        all_nodes = list(G_proj.nodes())
        shortest_distance = float("inf")
        closest_node = None
        for idx in indexes:
            nearest_node = all_nodes[idx]
            data_node = G_proj.nodes(data=True)[node]
            data_nearest_node = G_proj.nodes(data=True)[nearest_node]

            country_a = data_node.get(type)
            country_b = data_nearest_node.get(type)
            node_dist = self.haversine_nodes(node, nearest_node, "length")
            if country_a and country_b and country_a != country_b and shortest_distance > node_dist:
                shortest_distance = node_dist
                closest_node = all_nodes[idx]
        
        return (closest_node, shortest_distance)
    

    def get_border_polygon(self):
        nodes_gdf = ox.graph_to_gdfs(nx.MultiGraph(self), edges=False)
        min_x, min_y, max_x, max_y = nodes_gdf.total_bounds

        graph_area = Polygon([(min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y)])
        return graph_area
    

    def connect_airports_seaports(self, default_capacity : int, default_price : float):
        for source_node, source_data in self.nodes(data=True):
            if source_data.get("type") in ("airport", "seaport"):
                nearest_node = self.get_nearest_node(node=source_node)
                length = self.haversine_nodes(source_node, nearest_node, "length")   
                edge_data = {
                    "length" : length,
                    "capacity" : default_capacity,
                    "cost" : default_price, 
                    "added_artificially" : True,
                    "flow" : 0,
                    "type" : "road"
                }

                self.add_edge(source_node, nearest_node, **edge_data)
