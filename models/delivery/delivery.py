import numpy as np

from models.agents.exporter_agent import ExporterAgent
from network.simulation_graph import SimulationGraph


class Delivery:
    def __init__(self, delivery_id: int, start_node_id: int, end_node_id: int, route: list[int], length: float,
                 cost: float, lead_time: float, capacity : int = 0, disrupted : bool = False):
        self.delivery_id = delivery_id
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.route = route
        self.length = length
        self.cost = cost
        self.lead_time = lead_time
        self.capacity = capacity
        self.disrupted = disrupted

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "route": self.route,
            "length": self.length,
            "cost": self.cost,
            "lead_time": self.lead_time,
            "capacity": self.capacity,
            "disrupted": self.disrupted
        }

    def find_minimum_capacity(self, network: SimulationGraph):
        minimum_capacity = np.inf
        for i in range(len(self.route) - 1):
            if network.edges[self.route[i], self.route[i + 1], 0]['capacity'] < minimum_capacity:
                minimum_capacity = network.edges[self.route[i], self.route[i + 1], 0]['capacity']
        return minimum_capacity

    def reset_delivery(self):
        self.route = 0
        self.length = 0
        self.cost = 0
        self.lead_time = 0

    def update_delivery(self, exporters: list[ExporterAgent], network: SimulationGraph):
        exporter = None
        for e in exporters:
            if e.node_id == self.start_node_id:
                exporter = e
        path = exporter.find_cheapest_path(network, self.end_node_id)
        if path is None:
            return
        self.route = path['path']
        self.capacity = self.find_minimum_capacity(network)
        self.length = path['total_distance_km']
        self.cost = path['estimated_cost']
        self.lead_time = path['estimated_lead_time_days']