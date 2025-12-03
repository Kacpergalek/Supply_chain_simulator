import numpy as np

from models.agents.exporter_agent import ExporterAgent
from models.delivery.product import Product
from network.simulation_graph import SimulationGraph


class Delivery:
    def __init__(self, delivery_id: int, start_node_id: int, end_node_id: int, route: list[int], length: float,
                 cost: float, lead_time: float, parcel: list[tuple[Product, int]], disrupted: bool = False):
        self.delivery_id = delivery_id

        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.route = route

        self.length = length
        self.cost = cost
        self.lead_time = lead_time

        self.capacity = 0
        self.disrupted = disrupted
        self.parcel = parcel

    def to_dict(self) -> dict:
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

    def find_retail_price(self) -> float:
        retail_price = 0
        for product, quantity in self.parcel:
            retail_price += product.retail_price * quantity
        return retail_price * 1.2

    def find_parcel_cost(self) -> float:
        shipping_prices = {
            # --- HEAVY / BULKY (Furniture & Large Equipment) ---
            'Bookcases': 90.00,
            'Tables': 85.00,
            'Copiers': 75.00,
            'Chairs': 55.00,
            'Machines': 45.00,  # Printers, shredders, etc.
            'Furnishings': 30.00,  # Lamps, rugs, decor

            # --- MEDIUM (Boxed items, Electronics) ---
            'Storage': 22.00,  # Bins/organizers (bulky volume)
            'Appliances': 20.00,  # Small office appliances
            'Phones': 12.00,  # High value, tracked shipping
            'Paper': 12.00,  # Heavy by weight (ream density)
            'Art': 12.00,  # Fragile handling

            # --- LIGHT (Small parcels) ---
            'Accessories': 9.50,  # Keyboards, mice, USBs
            'Binders': 8.00,
            'Supplies': 6.50,  # Pens, staplers, misc
            'Labels': 4.50,
            'Envelopes': 4.00,
            'Fasteners': 3.50  # Paperclips, staples (very light)
        }
        parcel_price = 0
        for product, quantity in self.parcel:
            parcel_price += shipping_prices[product.subcategory] * quantity
        return parcel_price

    def find_minimum_capacity(self, network: SimulationGraph) -> float:
        minimum_capacity = np.inf
        for i in range(len(self.route) - 1):
            if network.edges[self.route[i], self.route[i + 1], 0]['capacity'] < minimum_capacity:
                minimum_capacity = network.edges[self.route[i], self.route[i + 1], 0]['capacity']
        return minimum_capacity

    def reset_delivery(self) -> None:
        self.route = 0
        self.length = 0
        self.cost = 0
        self.lead_time = 0

    def update_delivery(self, exporters: list[ExporterAgent], network: SimulationGraph) -> None:
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