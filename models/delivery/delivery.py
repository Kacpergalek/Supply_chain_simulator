import numpy as np


class Delivery:
    def __init__(self, delivery_id: int, start_node_id: int, end_node_id: int):
        self.delivery_id = delivery_id
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.route = []
        self.length = 0
        self.cost = 0
        self.capacity = 0
        self.disrupted = False

    def reset_delivery(self):
        self.route = 0
        self.length = 0
        self.cost = 0

    def update_delivery(self, exporters, network):
        exporter = None
        for e in exporters:
            if e.node_id == self.start_node_id:
                exporter = e
        path = exporter.find_cheapest_path(network, self.end_node_id)  # TODO nie działa
        self.route = path['path']
        minimum_capacity = np.inf

        for i in range(len(self.route)):
            self.length += network.edges[self.route[i], self.route[i + 1]].length
            self.cost += network.edges[self.route[i], self.route[i + 1]].cost
            if network.edges[self.route[i], self.route[i + 1]].capacity < minimum_capacity:
                minimum_capacity = network.edges[self.route[i], self.route[i + 1]].capacity
        self.capacity = minimum_capacity