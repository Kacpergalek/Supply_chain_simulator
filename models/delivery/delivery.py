import numpy as np

from models.agents.exporter_agent import ExporterAgent
from models.delivery.product import Product
from network.simulation_graph import SimulationGraph
# from utils.find_exporter import find_exporter_by_node_id


class Delivery:
    """
        Parameters
        ----------
        delivery_id : int
            Unique identifier of the delivery within the simulation.
        start_node_id : int
            ID of the node where the delivery starts (exporter).
        end_node_id : int
            ID of the node where the delivery ends (importer).
        route : list[int]
            Ordered list of node IDs representing the path.
        length : float
            Total route distance in kilometers.
        cost : float
            Estimated cost of transporting the parcel along the route.
        lead_time : float
            Estimated lead time in days.
        parcel : list[tuple[Product, int]]
            A list of `(product, quantity)` pairs.
        disrupted : bool, optional
            Flag indicating whether the delivery is currently disrupted.
    """
    def __init__(self, delivery_id: int, start_node_id: int, end_node_id: int, route: list[int], length: float,
                 cost: float, lead_time: float, parcel: list[tuple[Product, int]], disrupted: bool = False,
                 is_product: bool = True):
        self.delivery_id = delivery_id

        self.start_node_id = start_node_id
        self.end_node_id = end_node_id

        self.route = route
        self.length = length
        self.cost = cost
        self.lead_time = lead_time
        self.capacity = 0
        self.disrupted = disrupted

        self.is_product = is_product
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
            "disrupted": self.disrupted,
            "is_product": self.is_product
        }

    def find_parcel_retail_price(self) -> float:
        retail_price = 0
        for product, quantity in self.parcel:
            retail_price += product.retail_price * quantity
        return retail_price

    def find_parcel_shipping_cost(self) -> float:
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
        # TODO courier companies prices
        parcel_price = 0
        for product, quantity in self.parcel:
            parcel_price += (shipping_prices[product.subcategory] / 30)
        return parcel_price

    def find_minimum_capacity(self, network: SimulationGraph) -> float:
        minimum_capacity = np.inf
        for i in range(len(self.route) - 1):
            if network.edges[self.route[i], self.route[i + 1], 0]['capacity'] < minimum_capacity:
                minimum_capacity = network.edges[self.route[i], self.route[i + 1], 0]['capacity']
        return minimum_capacity

    def reset_delivery(self) -> None:
        """
        - Clears `route` and sets capacity, length, cost and lead time to zero.
        - Does not modify `parcel`, `start_node_id`, `end_node_id` or `disrupted`.
        """
        self.route = []
        self.capacity = 0
        self.length = 0
        self.cost = 0
        self.lead_time = 0

    def update_delivery(self, node_to_exporter: dict[int, ExporterAgent], network: SimulationGraph) -> None:
        """
        Updates `route`, `capacity`, `length`, `cost` and `lead_time` in-place based on
        the cheapest path to `end_node_id`.

        Parameters
        ----------
        node_to_exporter: dict[str, ExporterAgent]
            Exporter agents used to locate the exporter whose node matches `start_node_id`.
        network : SimulationGraph
            Directed simulation graph providing distances, costs and capacities.
        """
        exporter = node_to_exporter[self.start_node_id]
        graph_undirected = SimulationGraph(default_capacity=network.default_capacity,
                                           default_price=network.default_price,
                                           incoming_graph_data=network)
        path = exporter.find_cheapest_path(graph_undirected, self.end_node_id)
        self.route = path['path']
        self.capacity = self.find_minimum_capacity(network)
        self.length = path['total_distance_km']
        self.cost = path['estimated_cost']
        self.lead_time = path['estimated_lead_time_days']