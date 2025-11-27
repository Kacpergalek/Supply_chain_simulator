import random
from itertools import product
from pathlib import Path

import pandas as pd

from models.agents.base_agent import BaseAgent
from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery
from models.delivery.product import Product
from network.simulation_graph import SimulationGraph
from utils.find_exporter import find_exporter_by_node_id


class DeliveryManager:
    def __init__(self):
        self.categories = []
        self.furniture = []
        self.technology = []
        self.office_supplies = []

        self.tags_furniture = ["furniture", "bed", "kitchen", "lighting", "interior_decoration", "bathroom_furnishing"]
        self.tags_technology = ["electronics", "computer", "mobile_phone", "hifi", "photo", "video_games"]
        self.tags_office = ["office_supplies", "stationery", "copyshop", "printer_ink"]

        self.deliveries = []

    def read_csv(self, filepath: str, columns: list[str]):
        df = pd.read_csv(filepath, encoding='cp1252')
        return df[columns]

    def sort_products(self):
        path = Path(__file__).parent.parent.parent / "input"
        columns = ["Product ID", "Category", "Sub-Category", "Product Name", "Sales", "Quantity"]
        products_df = pd.DataFrame(self.read_csv(f"{path}/products.csv", columns))
        self.categories = list(set([row["Category"] for index, row in products_df.iterrows()]))

        for index, row in products_df.iterrows():
            product = Product(row["Product ID"], row["Product Name"], row["Category"], row["Sub-Category"],
                              row["Sales"], row["Quantity"])
            if row["Category"] == "Furniture":
                self.furniture.append(product)
            elif row["Category"] == "Technology":
                self.technology.append(product)
            else:
                self.office_supplies.append(product)

    def initialize_deliveries(self, network: SimulationGraph, exporters: list[ExporterAgent], agent_data: list[dict]):
        self.sort_products()
        for agent_dict in agent_data:
            agent = find_exporter_by_node_id(exporters, agent_dict['exporter_node'])
            products = self.initialize_products(agent)
            delivery = Delivery(len(self.deliveries), agent_dict['exporter_node'], agent_dict['importer_node'],
                                agent_dict['path'],
                                agent_dict['total_distance_km'], agent_dict['estimated_cost'],
                                agent_dict['estimated_lead_time_days'], products)
            delivery.capacity = delivery.find_minimum_capacity(network)
            self.deliveries.append(delivery)
        return self.deliveries

    def initialize_products(self, exporter: ExporterAgent):
        if exporter.store_category in self.tags_furniture:
            products = random.sample(self.furniture, 10)
        elif exporter.store_category in self.tags_technology:
            products = random.sample(self.technology, 10)
        else:
            products = random.sample(self.office_supplies, 10)
        return products