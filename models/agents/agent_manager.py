import math
import pickle
import random
from pathlib import Path

import osmnx as ox
import pandas as pd
import geopandas as gpd

from models.agents.base_agent import BaseAgent
from models.agents.courier_companies import courier_companies
from models.agents.importer_cities import importer_cities
from models.agents.exporter_cities import exporter_cities
from models.agents.europe_top_cities import europe_top_cities
from models.agents.exporter_agent import ExporterAgent

from network.simulation_graph import SimulationGraph
from utils.find_delivery import find_delivery_by_agent


class AgentManager:
    def __init__(self):
        self.cities = europe_top_cities
        self.stores = {}
        self.cols_of_interest = ['name', 'shop', 'geometry']
        self.tags_furniture = {
            "shop": ["furniture", "bed", "kitchen", "lighting", "interior_decoration", "bathroom_furnishing"]
        }
        self.tags_technology = {
            "shop": ["electronics", "computer", "mobile_phone", "hifi", "photo", "video_games"]
        }
        self.tags_office = {
            "shop": ["office_supplies", "stationery", "copyshop", "printer_ink"]
        }
        self.furniture = []
        self.technology = []
        self.office_supplies = []

        self.furniture_df = gpd.GeoDataFrame()
        self.technology_df = gpd.GeoDataFrame()
        self.office_supplies_df = gpd.GeoDataFrame()

        self.exporters = []
        self.importers = []


    def initialize_stores(self) -> None:
        for country in self.cities:
            for city in self.cities[country]:
                print(f"Querying: {city}...")

                try:
                    gdf_f = ox.features.features_from_place(city, self.tags_furniture)
                    gdf_f = gdf_f[self.cols_of_interest].dropna()
                    gdf_f['city'] = city
                    self.furniture_df = pd.concat([self.furniture_df, gdf_f], ignore_index=True)

                    gdf_t = ox.features.features_from_place(city, self.tags_technology)
                    gdf_t = gdf_t[self.cols_of_interest].dropna()
                    gdf_t['city'] = city
                    self.technology_df = pd.concat([self.technology_df, gdf_t], ignore_index=True)

                    gdf_o = ox.features.features_from_place(city, self.tags_office)
                    gdf_o = gdf_o[self.cols_of_interest].dropna()
                    gdf_o['city'] = city
                    self.office_supplies_df = pd.concat([self.office_supplies_df, gdf_o], ignore_index=True)

                except Exception as e:
                    print(f"   > Polygon not found for '{city}'")

    def save_to_pickle(self, filename: str) -> None:
        path = Path(__file__).parent.parent.parent / "parameters"

        if filename == "furniture":
            self.furniture_df.to_pickle(f"{path}/stores_furniture.pkl")
        elif filename == "technology":
            self.technology_df.to_pickle(f"{path}/stores_technology.pkl")
        elif filename == "office_supplies":
            self.office_supplies_df.to_pickle(f"{path}/stores_office_supplies.pkl")

    def load_from_pickle(self, filename: str) -> pd.DataFrame:
        path = Path(__file__).parent.parent.parent / "parameters"
        if not path.exists():
            self.initialize_stores()
            self.save_to_pickle(filename)
        with open(f"{path}/stores_{filename}.pkl", 'rb') as f:
            return pickle.load(f)

    def make_city_dict(self) -> None:
        furniture_stores = self.load_from_pickle("furniture")
        stores = furniture_stores[furniture_stores['geometry'].type == 'Point']
        technology_stores = self.load_from_pickle("technology")
        stores = pd.concat([stores, technology_stores[technology_stores['geometry'].type == 'Point']])
        office_stores = self.load_from_pickle("office_supplies")
        stores = pd.concat([stores, office_stores[office_stores['geometry'].type == 'Point']])

        for city in stores['city'].unique():
            store = stores[stores['city'] == city].sample()
            store_dict = {"geometry": store['geometry'].item(),
                          "store_name" : store['name'].item(), "store_category" : store['shop'].item()}
            self.stores[store['city'].item()] = store_dict

    def initialize_agents(self, graph: SimulationGraph) -> dict[str, list]:
        if len(self.stores) == 0:
            self.make_city_dict()
        exporters = self.initialize_exporters(graph)
        importers = self.initialize_importers(graph)
        routes = self.initialize_routes(graph)
        initialized = {"exporters": exporters, "importers": importers, "routes": routes}
        return initialized

    def haversine_km(self, lat1, lon1, lat2, lon2) -> float:
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        d_lon = lon2 - lon1
        d_lat = lat2 - lat1
        a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c

    def find_closest_node(self, graph:SimulationGraph, store: pd.Series):
        lat_c = store['geometry'].x
        lon_c = store['geometry'].y
        return min(
            graph.nodes,
            key=lambda n: self.haversine_km(lat_c, lon_c, graph.nodes[n].get("y", 0), graph.nodes[n].get("x", 0))
        )

    def initialize_exporters(self, graph:SimulationGraph) -> list[ExporterAgent]:
        for city in exporter_cities:
            store = self.stores[city]
            closest_node = self.find_closest_node(graph, store)
            agent_id = len(self.exporters)
            courier_company = random.choice(list(courier_companies))
            exporter = ExporterAgent(agent_id=agent_id, node_id=closest_node, store_name=store['store_name'],
                                     store_category=store['store_category'], city=city, courier_company=courier_company)
            self.exporters.append(exporter)
        return self.exporters

    def initialize_importers(self, graph: SimulationGraph) -> list[BaseAgent]:
        for city in importer_cities:
            store = self.stores[city]
            closest_node = self.find_closest_node(graph, store)
            agent_id = len(self.exporters) + len(self.importers)
            importer = BaseAgent(agent_id=agent_id, node_id=closest_node)
            self.importers.append(importer)
        return self.importers

    def initialize_routes(self, graph: SimulationGraph) -> list[dict]:
        results = []

        graph_undirected = SimulationGraph(default_capacity=graph.default_capacity,
                                           default_price=graph.default_price,
                                           incoming_graph_data=graph)

        for i, (exp, imp) in enumerate(zip(self.exporters, self.importers), start=0):
            print(exp)
            try:
                params = {"default_unit_cost": courier_companies[exp.courier_company]}
                result = exp.find_cheapest_path(graph_undirected, dest_node=imp.node_id, params=params)
                results.append({
                    "agent_id": i,
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

        path = Path(__file__).parent.parent.parent / "network_data" / "paths.pkl"
        with open(path, "wb") as f:
            pickle.dump(data, f)

        return results

    # def calculate_prices(self):
    #     for exporter in self.exporters:
    #         delivery = find_delivery_by_agent()
    #         exporter.production_price = exporter.delivery.calculate_production_price()


# if __name__ == "__main__":
    # am = AgentManager()
    # am.initialize_stores()
    # am.save_to_pickle()
    # pd.set_option('display.max_columns', None)
    # am = AgentManager()
    # f = am.load_from_pickle("furniture")
    # print(f)
    # print(f[f['geometry'].type == 'Point'])
    # am.make_city_dict()
    # am = AgentManager()
    # am.initialize_agents()