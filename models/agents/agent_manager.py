import json
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
from models.delivery.delivery_manager import DeliveryManager
from models.delivery.product import Product

from network.simulation_graph import SimulationGraph


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

        self.delivery_manager = DeliveryManager()
        self.delivery_manager.sort_products()

    def initialize_stores(self) -> None:
        for country in self.cities:
            for city in self.cities[country]:
                print(f"Querying: {city}...")

                try:
                    gdf_f = ox.features.features_from_place(
                        city, self.tags_furniture)
                    gdf_f = gdf_f[self.cols_of_interest].dropna()
                    gdf_f['city'] = city
                    self.furniture_df = pd.concat(
                        [self.furniture_df, gdf_f], ignore_index=True)

                    gdf_t = ox.features.features_from_place(
                        city, self.tags_technology)
                    gdf_t = gdf_t[self.cols_of_interest].dropna()
                    gdf_t['city'] = city
                    self.technology_df = pd.concat(
                        [self.technology_df, gdf_t], ignore_index=True)

                    gdf_o = ox.features.features_from_place(
                        city, self.tags_office)
                    gdf_o = gdf_o[self.cols_of_interest].dropna()
                    gdf_o['city'] = city
                    self.office_supplies_df = pd.concat(
                        [self.office_supplies_df, gdf_o], ignore_index=True)

                except Exception as e:
                    print(f"   > Polygon not found for '{city}'")
                    self.cities[country].remove(city)
        with open('europe_top_cities_filtered.json', 'w') as fp:
            json.dump(self.cities, fp)
        self.save_to_pickle("furniture")
        self.save_to_pickle("technology")
        self.save_to_pickle("office_supplies")

    def save_to_pickle(self, filename: str) -> None:
        path = Path(__file__).parent.parent.parent / "input_data"

        if filename == "furniture":
            self.furniture_df.to_pickle(f"{path}/stores_furniture.pkl")
        elif filename == "technology":
            self.technology_df.to_pickle(f"{path}/stores_technology.pkl")
        elif filename == "office_supplies":
            self.office_supplies_df.to_pickle(
                f"{path}/stores_office_supplies.pkl")

    def load_from_pickle(self, filename: str) -> pd.DataFrame:
        path = Path(__file__).parent.parent.parent / "input_data" / f"stores_{filename}.pkl"
        if not path.exists():
            self.initialize_stores()
            self.save_to_pickle(filename)
        with open(path, 'rb') as f:
            return pickle.load(f)

    def make_city_dict(self) -> None:
        self.furniture_df = self.load_from_pickle("furniture")
        stores = self.furniture_df[self.furniture_df['geometry'].type == 'Point']
        self.technology_df = self.load_from_pickle("technology")
        stores = pd.concat(
            [stores, self.technology_df[self.technology_df['geometry'].type == 'Point']])
        self.office_supplies_df = self.load_from_pickle("office_supplies")
        stores = pd.concat(
            [stores, self.office_supplies_df[self.office_supplies_df['geometry'].type == 'Point']])

        for city in stores['city'].unique():
            store = stores[stores['city'] == city].sample()
            store_dict = {"geometry": store['geometry'].item(),
                          "store_name": store['name'].item(), "store_category": store['shop'].item()}
            self.stores[store['city'].item()] = store_dict

    def initialize_agents(self, graph: SimulationGraph) -> dict[str, list]:
        if len(self.stores) == 0:
            self.make_city_dict()
        exporters = self.initialize_exporters(graph)
        importers = self.initialize_importers(graph)
        routes = self.initialize_routes(graph)
        initialized = {"exporters": exporters,
                       "importers": importers, "routes": routes}
        return initialized

    def haversine_km(self, lat1, lon1, lat2, lon2) -> float:
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        d_lon = lon2 - lon1
        d_lat = lat2 - lat1
        a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(d_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c

    def _is_airport_node(self, graph: SimulationGraph, node_id: int) -> bool:
        """
        Heuristic check whether a node represents an airport / airport-only route.
        Adjust this if your airport tagging schema is different.
        """
        data = graph.nodes[node_id]

        # 1) Direct node tags commonly used for airports
        if data.get("type") == "airport":
            return True
        else:
            return False
        # if data.get("is_airport"):
        #     return True
        # if data.get("aeroway") in {"aerodrome", "airport", "heliport"}:
        #     return True
        # if data.get("amenity") == "airport":
        #     return True
        # return False

        # 2) If all incident edges are air-mode edges, treat as airport node
        # def edge_is_air(e_data: dict) -> bool:
        #     mode = e_data.get("mode")
        #     route = e_data.get("route")
        #     if mode in {"air", "flight"}:
        #         return True
        #     if route in {"air", "flight"}:
        #         return True
        #     return False
        #
        # has_edges = False
        # for _, _, e_data in graph.out_edges(node_id, data=True):
        #     has_edges = True
        #     if not edge_is_air(e_data):
        #         return False
        # for _, _, e_data in graph.in_edges(node_id, data=True):
        #     has_edges = True
        #     if not edge_is_air(e_data):
        #         return False
        #
        # # If there are edges and all of them look like air edges -> airport node
        # return has_edges

    def find_closest_node(self, graph: SimulationGraph, store: pd.Series):
        #TODO check if node is an airport - we don't take airports
        # GeoPandas Point: .x is longitude, .y is latitude
        lon_c = store['geometry'].x
        lat_c = store['geometry'].y

        sorted_nodes = sorted(
            graph.nodes,
            key=lambda n: self.haversine_km(
                lat_c,
                lon_c,
                graph.nodes[n].get("y", 0),
                graph.nodes[n].get("x", 0),
            ),
        )

        for node_id in sorted_nodes:
            if not self._is_airport_node(graph, node_id):
                return node_id

            # Fallback: if everything looks like an airport, just return the closest
            # (or you could raise an error instead)
        return sorted_nodes[0]

    def initialize_exporters(self, graph: SimulationGraph) -> list[ExporterAgent]:
        for city in exporter_cities:
            store = self.stores[city]
            closest_node = self.find_closest_node(graph, store)
            agent_id = len(self.exporters)
            courier_company = random.choice(list(courier_companies))
            products = self.delivery_manager.initialize_products(
                store['store_category'])
            exporter = ExporterAgent(agent_id=agent_id, node_id=closest_node, store_name=store['store_name'],
                                     store_category=store['store_category'], city=city, courier_company=courier_company,
                                     products=products)
            self.exporters.append(exporter)
        # Debug: show how many exporters were created and sample node ids
        # try:
        #     print(
        #         f"Initialized {len(self.exporters)} exporters. Sample nodes: {[e.node_id for e in self.exporters[:5]]}")
        # except Exception:
        #     pass
        return self.exporters

    def initialize_importers(self, graph: SimulationGraph) -> list[BaseAgent]:
        for city in importer_cities:
            store = self.stores[city]
            closest_node = self.find_closest_node(graph, store)
            agent_id = len(self.exporters) + len(self.importers)
            importer = BaseAgent(agent_id=agent_id, node_id=closest_node)
            self.importers.append(importer)
        # Debug: show how many importers were created and sample node ids
        # try:
        #     print(
        #         f"Initialized {len(self.importers)} importers. Sample nodes: {[i.node_id for i in self.importers[:5]]}")
        # except Exception:
        #     pass
        return self.importers

    def initialize_routes(self, graph: SimulationGraph) -> list[dict]:
        results = []

        graph_undirected = SimulationGraph(default_capacity=graph.default_capacity,
                                           default_price=graph.default_price,
                                           incoming_graph_data=graph)

        # --- DEBUG: show connected components and where agents are  ---
        import networkx as nx
        components = list(nx.connected_components(graph_undirected))
        print(f"Graph has {len(components)} connected components")
        comp_index_by_node = {}
        for idx, comp in enumerate(components):
            for n in comp:
                comp_index_by_node[n] = idx

        for idx, exp in enumerate(self.exporters):
            imp = self.importers[idx]
            exp_comp = comp_index_by_node.get(exp.node_id, None)
            imp_comp = comp_index_by_node.get(imp.node_id, None)
            print(
                f"Pair {idx}: exporter {exp.node_id} in comp {exp_comp}, "
                f"importer {imp.node_id} in comp {imp_comp}"
            )
        # --- END DEBUG ---

        for i, (exp, imp) in enumerate(zip(self.exporters, self.importers), start=0):
            print(exp)
            try:
                params = {
                    "default_unit_cost": courier_companies[exp.courier_company]
                }
                result = exp.find_cheapest_path(
                    graph_undirected, dest_node=imp.node_id, params=params)
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

        path = Path(__file__).parent.parent.parent / \
            "input_data" / "network_data" / "paths.pkl"
        with open(path, "wb") as f:
            pickle.dump(data, f)

        return results

    # def calculate_prices(self):
    #     for exporter in self.exporters:
    #         delivery = find_delivery_by_agent()
    #         exporter.production_price = exporter.delivery.calculate_production_price()


if __name__ == "__main__":
    am = AgentManager()
    am.initialize_stores()
