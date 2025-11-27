import networkx as nx
import osmnx as ox
from queue import PriorityQueue, Queue
import heapq
import math

class SimulationGraph(nx.MultiGraph):
    def __init__(self, default_capacity, default_price, incoming_graph_data=None, multigraph_input = None, **attr):
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
        
        for node, data in self.nodes(data=True):
            if "active" not in data:
                data["active"] = True
            if "type" not in data:
                data["type"] = "road" # będziemy dodawać firmy/dostawców
            


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


    def safe_shortest_path(self, start_node : int, end_node : int, weight : str = "cost"):
        mutlidigraf = nx.MultiGraph(self)
        sim_graph_cpy = self.__class__(default_capacity = self.default_capacity, default_price = self.default_price, incoming_graph_data = mutlidigraf)

        deactivated_nodes = [node for node, data in sim_graph_cpy.nodes(data=True) if data["active"] == False]

        sim_graph_cpy.remove_nodes_from(deactivated_nodes)
        return nx.shortest_path(sim_graph_cpy, start_node, end_node, weight=weight)


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

    def display(self):
        graph = nx.MultiGraph(self)
        ox.plot_graph(graph)


    def safe_astar_path(self, start_node : int, end_node : int, weight : str = "length"):
        mutlidigraf = nx.MultiGraph(self)
        sim_graph_cpy = self.__class__(default_capacity = self.default_capacity, default_price = self.default_price, incoming_graph_data = mutlidigraf)

        deactivated_nodes = [node for node, data in sim_graph_cpy.nodes(data=True) if data["active"] == False]

        sim_graph_cpy.remove_nodes_from(deactivated_nodes)
        return nx.astar_path(sim_graph_cpy, start_node, end_node, weight=weight)


    # def astar(self, start_node : int, end_node : int, metric : str = "length"):

    #     entry_queue = []
    #     closed_set = set()

    #     heapq.heappush(entry_queue, (0.0, 0.0, start_node))
    #     while len(entry_queue) > 0:
    #         node_f, node_g, node = heapq.heappop(entry_queue)
    #         for neighbour in self.neighbors(node):
    #             if neighbour == end_node:
    #                 return "success"
    #             else:
    #                 neighbour_g = node_g + self.haversine(node, neighbour, metric)
    #                 neighbour_h = self.heuristic_distace(neighbour, end_node, metric)
    #                 neighbour_f = neighbour_g + neighbour_h

    #                 if neighbour_f > any([node[0] for node in entry_queue]):
    #                     continue

    #                 if neighbour_f > any([node[0] for node in closed_set]):
    #                     continue
    #                 else:
    #                     heapq.heappush(entry_queue, (neighbour_f, neighbour_g, neighbour))
    #         closed_set.add((node_f, node_g, node))


    def astar(self, start_node: int, end_node: int, metric: str = "length"):
        entry_queue = []
        heapq.heappush(entry_queue, (0.0, 0.0, start_node))
        
        came_from = {}
        g_score = {start_node: 0.0}

        while len(entry_queue) > 0:
            print(g_score)
            _, current_g, current_node = heapq.heappop(entry_queue)

            if current_node == end_node:
                return self.reconstruct_path(came_from, current_node)

            if current_g > g_score.get(current_node, float('inf')):
                continue

            for neighbour in self.neighbors(current_node):
                neighbour_g = current_g + self.haversine_nodes(current_node, neighbour, metric)
                
                if neighbour_g < g_score.get(neighbour, float('inf')):
                    came_from[neighbour] = current_node
                    g_score[neighbour] = neighbour_g
                    
                    neighbour_h = self.heuristic(neighbour, end_node, metric)
                    neighbour_f = neighbour_g + neighbour_h
                    
                    heapq.heappush(entry_queue, (neighbour_f, neighbour_g, neighbour))
        return None


    def reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1] 


    def heuristic(self, start_node : int, end_node : int, metric : str, mode : str = "euclidean"):
        if mode == "euclidean":
            return self.haversine_nodes(start_node, end_node, metric)
        if mode == "manhattan":
            pass
        return None


    def haversine_nodes(self, node1 : int, node2 : int, metric : str):
        if metric == "length":
            lat1 = self.nodes()[node1]["x"]
            lon1 = self.nodes()[node1]["y"]
            lat2 = self.nodes()[node2]["x"]
            lon2 = self.nodes()[node2]["y"]

            R = 6371  # promień Ziemi

            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)

            a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c * 1000
        

    def haversine_coordinates(self, lat1, lon1, lat2, lon2, metric : str):
        if metric == "length":
            R = 6371  # promień Ziemi

            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)

            a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c * 1000
        
        
    def get_nearest_node(self, lattitude : float, longitude : float):
        min_dist = float("inf")
        nearest_node = None

        for node_id, data in self.nodes(data=True):
            node_lat = data.get('y', None)
            node_lon = data.get('x', None)
            if node_lat is None or node_lon is None:
                continue

            dist = self.haversine_coordinates(lattitude, longitude, node_lat, node_lon, "length")
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id

        return nearest_node