import networkx as nx
import osmnx as ox

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
