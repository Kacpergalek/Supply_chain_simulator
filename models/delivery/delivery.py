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

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "route": self.route,
            "length": self.length,
            "cost": self.cost,
            "capacity": self.capacity,
            "disrupted": self.disrupted
        }

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
        if path is None:
            return
        self.route = path['path']
        minimum_capacity = np.inf

        for i in range(len(self.route) - 1):
            self.length += network.edges[self.route[i], self.route[i + 1], 0]['length']
            self.cost += network.edges[self.route[i], self.route[i + 1], 0]['cost']
            if network.edges[self.route[i], self.route[i + 1], 0]['capacity'] < minimum_capacity:
                minimum_capacity = network.edges[self.route[i], self.route[i + 1], 0]['capacity']
        self.capacity = minimum_capacity