import json
import math
import os
import pickle
import random
from pathlib import Path
import pandas as pd

from input_data.agent_data.material_exporter_cities import material_exporter_cities
from models.agents.base_agent import BaseAgent
from input_data.delivery_data.courier_companies import courier_companies
from input_data.agent_data.product_importer_cities import product_importer_cities
from input_data.agent_data.importer_exporter_cities import importer_exporter_cities
from models.agents.exporter_agent import ExporterAgent
from models.agents.factory_manager import FactoryManager
from models.agents.retail_store_manager import RetailStoreManager
from models.delivery.delivery_manager import DeliveryManager

from network.simulation_graph import SimulationGraph


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c


def _is_airport_node(graph: SimulationGraph, node_id: int) -> bool:
    """
    Heuristic check whether a node represents an airport / airport-only route.

    Returns
    -------
    bool
        True if the node is interpreted as an airport, False otherwise.
    """
    data = graph.nodes[node_id]

    # 1) Direct node tags commonly used for airports
    if data.get("type") == "airport":
        return True
    else:
        return False

def find_closest_node(graph: SimulationGraph, store: pd.Series):
    """
    Find the closest non-airport graph node to a given store location.
    The distance is computed via the Haversine formula over all nodes,
    while skipping nodes that are considered airports.

    Returns
    -------
    int
        ID of the closest suitable node.
    """
    lon_c = store['geometry'].x
    lat_c = store['geometry'].y

    sorted_nodes = sorted(
        graph.nodes,
        key=lambda n: haversine_km(
            lat_c,
            lon_c,
            graph.nodes[n].get("y", 0),
            graph.nodes[n].get("x", 0),
        ),
    )

    for node_id in sorted_nodes:
        if not _is_airport_node(graph, node_id):
            return node_id

    return sorted_nodes[0]


class AgentManager:
    """
    Responsibilities
    ----------------
    - Initialize:
        * material exporters (raw material providers),
        * importer-exporters (intermediate factories),
        * product importers (retail-side receivers).
    - Attach agents to the underlying network by choosing nearest nodes.
    - Precompute cheapest routes between exporters and importers.
    - Expose metadata needed by the simulation (agents and their routes).

    Attributes
    ----------
    material_exporters : list[ExporterAgent]
        Agents exporting raw materials to importer-exporters.
    importer_exporters : list[ExporterAgent]
        Agents that both import raw materials and export finished products.
    product_importers : list[BaseAgent]
        Downstream agents receiving finished products.
    delivery_manager : DeliveryManager
        Used to construct deliveries for initialized routes.
    retail_store_manager : RetailStoreManager
        Manages store locations and categories (note: 'retial' typo kept for compatibility).
    factory_manager : FactoryManager
        Manages factory locations and categories.
    product_manager
        Reference to product manager from `RetailStoreManager` used to assign
        product assortments to exporters.
    stores : dict
        Mapping: city -> store metadata (geometry, name, category).
    factories : dict
        Mapping: city -> factory metadata (geometry, name, category).
    """
    def __init__(self):
        self.material_routes = []
        self.product_routes = []
        self.material_exporters = []
        self.importer_exporters = []
        self.product_importers = []
        self.delivery_manager = DeliveryManager()
        self.retail_store_manager = RetailStoreManager()
        self.factory_manager = FactoryManager()
        self.stores = self.retail_store_manager.stores
        self.factories = self.factory_manager.factories
        self.index = 0

    def initialize_agents(self, graph: SimulationGraph) -> dict[str, list]:
        """
        Initialize all agent types, attach them to the network and compute routes.

        Returns
        -------
        dict[str, list]
            Dictionary containing:
            - "material_exporters" : list[ExporterAgent]
            - "importer_exporters" : list[ExporterAgent]
            - "product_importers" : list[BaseAgent]
            - "material_routes"   : list[dict]
            - "product_routes"    : list[dict]
        """
        if len(self.stores) == 0:
            self.stores = self.retail_store_manager.make_city_dict()
        if len(self.factories) == 0:
            self.factories = self.factory_manager.make_city_dict()
        self.importer_exporters = self.initialize_exporters(graph, importer_exporter_cities)
        self.material_exporters  = self.initialize_exporters(graph, material_exporter_cities)
        self.product_importers = self.initialize_product_importers(graph)
        self.material_routes = self.initialize_routes(graph, self.material_exporters, self.importer_exporters)
        self.product_routes = self.initialize_routes(graph, self.importer_exporters, self.product_importers)
        initialized = {"material_exporters": self.material_exporters, "importer_exporters": self.importer_exporters,
                       "product_importers": self.product_importers, "material_routes": self.material_routes,
                       "product_routes": self.product_routes}
        # self.save_agent_data("material_exporters.json", material_exporters)
        # self.save_agent_data("importer_exporters.json", importer_exporters)
        # self.save_agent_data("product_importers.json", product_importers)
        # self.save_agent_data("material_routes.json", material_routes)
        # self.save_agent_data("product_routes.json", product_routes)
        # for exp in self.importer_exporters:
        #     print(exp.to_dict())
        return initialized

    def initialize_exporters(self, graph: SimulationGraph, exporter_cities: list[str]) -> list[ExporterAgent]:
        """
        Create exporter agents for a given list of cities.

        Returns
        -------
        list[ExporterAgent]
            Initialized exporter agents with assigned locations, products
            and courier companies.
        """
        exporters = []
        for city in exporter_cities:
            store = self.stores[city]
            closest_node = find_closest_node(graph, store)
            agent_id = self.index
            self.index += 1
            courier_company = random.choice(list(courier_companies))
            products = self.retail_store_manager.product_manager.initialize_products(store['store_category'])
            finances = random.randrange(1000, 5000)
            exporter = ExporterAgent(agent_id=agent_id, node_id=closest_node, store_name=store['store_name'],
                                     store_category=store['store_category'], city=city, courier_company=courier_company,
                                     products=products, finances=finances)
            exporters.append(exporter)
        return exporters

    def initialize_product_importers(self, graph: SimulationGraph) -> list[BaseAgent]:
        """
        Create product importer agents assigned to the nearest graph node.

        Returns
        -------
        list[BaseAgent]
            List of product importer agents.
        """
        for city in product_importer_cities:
            store = self.stores[city]
            closest_node = find_closest_node(graph, store)
            agent_id = self.index
            self.index += 1
            country = city.split(",")[1]
            importer = BaseAgent(agent_id=agent_id, node_id=closest_node, country=country)
            self.product_importers.append(importer)
        return self.product_importers

    def initialize_routes(self, graph: SimulationGraph, exporters: list[ExporterAgent], importers: list[BaseAgent]) -> list[dict]:
        """
        Compute cheapest routes between exporter and importer pairs.

        Parameters
        ----------
        graph : SimulationGraph
            Directed network graph containing capacities and prices.
        exporters : list[ExporterAgent]
            Source agents for shipments.
        importers : list[BaseAgent]
            Destination agents for shipments.

        Returns
        -------
        list[dict]
            A list of route metadata dictionaries, each containing:
            - agent_id, exporter_node, importer_node, path, total_distance_km,
              estimated_cost, estimated_lead_time_days, etc. (as returned by
              `ExporterAgent.find_cheapest_path`).
        """
        results = []

        # graph_undirected = SimulationGraph(default_capacity=graph.default_capacity,
        #                                    default_price=graph.default_price,
        #                                    incoming_graph_data=graph)

        for _, (exp, imp) in enumerate(zip(exporters, importers), start=0):
            # print(exp)
            try:
                params = {
                    "default_unit_cost": courier_companies[exp.courier_company]
                }
                result = exp.find_cheapest_path(
                    graph, dest_node=imp.node_id, params=params)
                results.append({
                    "agent_id": exp.agent_id,
                    "exporter_node": exp.node_id,
                    "importer_node": imp.node_id,
                    **result
                })
                # print(f"✅ Agent {i}: {exp_node} → {imp_node} | dystans: {result['total_distance_km']:.2f} km | koszt: {result['estimated_cost']:.2f}")
            except Exception as e:
                print(f"❌ {exp.node_id} → {imp.node_id} | błąd: {e}")

        data = {
            "exporter_node": [r["exporter_node"] for r in results],
            "importer_node": [r["importer_node"] for r in results],
            "results": results
        }
        self.save_paths_to_pkl(data)

        return results

    def save_paths_to_pkl(self, data: dict):
        path = Path(__file__).parent.parent.parent / "input_data" / "network_data" / "paths.pkl"
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def save_agent_data(self, file_name: str, data) -> None:
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data/agents")
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        full_path = os.path.join(data_path, file_name)
        if not isinstance(data[0], dict):
            with open(full_path, "w", encoding="utf-8") as json_file:
                json.dump([d.to_dict() for d in data], json_file, indent=4, ensure_ascii=False)
        else:
            with open(full_path, "w", encoding="utf-8") as json_file:
                json.dump([d for d in data], json_file, indent=4, ensure_ascii=False)

    def load_exporters(self, file_name: str) -> list[ExporterAgent]:
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data/agents")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Folder: {data_path} does not exist.")
        full_path = os.path.join(data_path, file_name)
        agent_list = []
        with open(full_path, "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"Json loading error: {str(e)}")
                return agent_list
        for o in data:
            try:
                agent = ExporterAgent(o["agent_id"], int(o["node_id"]), o["store_name"], o["store_category"],
                                      o["city"], o["courier_company"], o["products"])
                agent_list.append(agent)
            except TypeError as e:
                print(f"Error while deserializing delivery object: {str(e)}")
        return agent_list

    def load_importers(self, file_name: str) -> list[BaseAgent]:
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data/agents")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Folder: {data_path} does not exist.")
        full_path = os.path.join(data_path, file_name)
        agent_list = []
        with open(full_path, "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"Json loading error: {str(e)}")
                return agent_list
        for o in data:
            try:
                agent = BaseAgent(o["agent_id"], int(o["node_id"]), o["country"])
                agent_list.append(agent)
            except TypeError as e:
                print(f"Error while deserializing delivery object: {str(e)}")
        return agent_list

    def load_routes(self, file_name: str) -> list[dict]:
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data/agents")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Folder: {data_path} does not exist.")
        full_path = os.path.join(data_path, file_name)
        with open(full_path, "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"Json loading error: {str(e)}")
        return data