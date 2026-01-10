import random
from pathlib import Path
import pandas as pd

from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery
from models.delivery.product import Product
from models.delivery.product_manager import ProductManager
from models.delivery.raw_material import RawMaterial
from network.simulation_graph import SimulationGraph
from utils.find_delivery import find_delivery_by_starting_node_id
# from utils.find_exporter import find_exporter_by_node_id
from utils.get_dataframe_from_csv import get_dataframe_from_csv


class DeliveryManager:
    """
        - Generates deliveries between exporters and importers based on precomputed
          paths and network information.
        - Builds product parcels for product deliveries using inventory and CSV-based
          demand quantities.
        - Derives batches of raw materials from existing product parcels (e.g. for
          upstream factory deliveries).

        Attributes
        ----------
        product_manager : ProductManager
            Used to load and categorize products.
        deliveries : list[Delivery]
            All deliveries that have been initialized in the current simulation.
        """
    def __init__(self):
        self.product_manager = ProductManager()
        self.deliveries = []


    def initialize_deliveries(self, network: SimulationGraph, node_to_exporter: dict[int, ExporterAgent],
                              paths: list[dict], product_delivery: bool) -> list[Delivery]:
        """
        Parameters
        ----------
        network : SimulationGraph
            The transportation network used to determine edge capacities.
        node_to_exporter :  dict[str, ExporterAgent]
            Exporter agents participating in the simulation.
        paths : list[dict]
            Precomputed path descriptions. Each dict is expected to include:
            - 'exporter_node': int
            - 'importer_node': int
            - 'path': list[int]
            - 'total_distance_km': float
            - 'estimated_cost': float
            - 'estimated_lead_time_days': float
        product_delivery : bool
            If True, create product deliveries
            If False, create raw material deliveries (corresponding product delivery must exist already)

        Returns
        -------
        list[Delivery]
            The list of all deliveries initialized (including any existing ones).
        """
        self.product_manager.sort_products()
        deliveries = []
        for agent_dict in paths:
            agent = node_to_exporter[agent_dict['exporter_node']]

            number_of_products = random.randrange(int(agent_dict['total_distance_km'] / 10.0),
                                                  int(agent_dict['total_distance_km'] / 5.0))
            if product_delivery:
                parcel = self.initialize_parcel([inv[0] for inv in agent.inventory], number_of_products)
            else:

                p_delivery = find_delivery_by_starting_node_id(self.deliveries, agent_dict['importer_node'])
                parcel = self.initialize_raw_material_batch(p_delivery.parcel)
            delivery = Delivery(len(self.deliveries), agent_dict['exporter_node'], agent_dict['importer_node'],
                                agent_dict['path'], agent_dict['total_distance_km'], agent_dict['estimated_cost'],
                                agent_dict['estimated_lead_time_days'], parcel, False, product_delivery)
            delivery.capacity = delivery.find_minimum_capacity(network)
            agent.delivery = delivery
            self.deliveries.append(delivery)
            deliveries.append(delivery)
        return deliveries

    def initialize_parcel(self, products: list[Product], number_of_products: int) -> list[tuple[Product, int]]:
        """
        Parameters
        ----------
        products : list[Product]
            Candidate products (usually from an exporter's inventory).
        number_of_products : int
            Desired number of distinct product types in the parcel (will be capped if necessary).

        Returns
        -------
        list[tuple[Product, int]]
            A list of `(product, quantity)` pairs representing the parcel.
        """
        path = Path(__file__).parent.parent.parent / "input_data"
        columns = ["Product ID", "Quantity"]
        products_df = pd.DataFrame(get_dataframe_from_csv(f"{path}/products.csv", columns))
        products_df = products_df.groupby("Product ID").sum().reset_index()
        products2_df = pd.DataFrame(get_dataframe_from_csv(f"{path}/products2.csv", columns))
        products2_df = products2_df.groupby("Product ID").sum().reset_index()
        products_df = pd.concat([products_df, products2_df])
        parcel = []
        if number_of_products > len(products):
            number_of_products = len(products)
        products = random.sample(products, number_of_products)
        for product in products:
            quantity = products_df[products_df["Product ID"] == product.product_id]["Quantity"].item()
            parcel.append((product, quantity))
        return parcel

    def initialize_raw_material_batch(self, parcel: list[tuple[Product, int]]) -> list[tuple[RawMaterial, float]]:
        """
        Parameters
        ----------
        parcel : list[tuple[Product, int]]
            A list of `(product, quantity)` pairs representing a finished
            product parcel.

        Returns
        -------
        list[tuple[RawMaterial, float]]
            A list of `(raw_material, quantity_kg)` pairs representing the
            upstream raw material batch.
        """
        batch = []
        for product, quantity in parcel:
            m_name = product.name + "_raw_material"
            m_category = product.category + "_raw_material"
            m_price = product.retail_price * 0.1
            material = RawMaterial(product.product_id, m_name, m_category, m_price)
            qty_kg = quantity * 0.2
            batch.append((material, qty_kg))
        return batch