import random
from pathlib import Path
import pandas as pd

from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery
from models.delivery.product import Product
from network.simulation_graph import SimulationGraph
from utils.find_exporter import find_exporter_by_node_id


def read_csv(filepath: str, columns: list[str]):
    df = pd.read_csv(filepath, encoding='cp1252')
    return df[columns]


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

    def sort_products(self):
        path = Path(__file__).parent.parent.parent / "input_data"
        columns = ["Product ID", "Category", "Sub-Category", "Product Name", "Sales", "Quantity"]
        products_df = pd.DataFrame(read_csv(f"{path}/products.csv", columns))
        products_df.drop_duplicates(subset=['Product ID'], inplace=True)
        self.categories = list(set([row["Category"] for index, row in products_df.iterrows()]))

        for index, row in products_df.iterrows():
            product = Product(row["Product ID"], row["Product Name"], row["Category"], row["Sub-Category"],
                              row["Sales"] / row["Quantity"])
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
            parcel = self.initialize_parcel([inv[0] for inv in agent.inventory])
            delivery = Delivery(len(self.deliveries), agent_dict['exporter_node'], agent_dict['importer_node'],
                                agent_dict['path'], agent_dict['total_distance_km'], agent_dict['estimated_cost'],
                                agent_dict['estimated_lead_time_days'], parcel)
            delivery.capacity = delivery.find_minimum_capacity(network)
            agent.delivery = delivery
            self.deliveries.append(delivery)
        return self.deliveries

    def initialize_products(self, store_category: str) -> list[Product]:
        if store_category in self.tags_furniture:
            products = random.sample(self.furniture, 100)
        elif store_category in self.tags_technology:
            products = random.sample(self.technology, 100)
        else:
            products = random.sample(self.office_supplies, 100)
        return products

    def initialize_parcel(self, products: list[Product]) -> list[tuple[Product, int]]:
        path = Path(__file__).parent.parent.parent / "input_data"
        columns = ["Product ID", "Quantity"]
        products_df = pd.DataFrame(read_csv(f"{path}/products.csv", columns))
        products_df = products_df.groupby("Product ID").sum().reset_index()
        parcel = []
        for product in products:
            quantity = products_df[products_df["Product ID"] == product.product_id]["Quantity"].item()
            parcel.append((product, quantity))
        return parcel


if __name__ == "__main__":
    path = Path(__file__).parent.parent.parent / "input_data"
    columns = ["Product ID", "Quantity"]
    products_df = pd.DataFrame(read_csv(f"{path}/products.csv", columns))
    # print(products_df[products_df["Product ID"] == "FUR-BO-10000112"])
    df = products_df.groupby("Product ID").sum().reset_index()
    print(df)
    print(df["Product ID"])