import math
import pickle
from pathlib import Path

import osmnx as ox
import pandas as pd

from models.agents.europe_top_cities import europe_top_cities

from models.delivery.delivery_manager import DeliveryManager


class AgentManager:
    def __init__(self):
        self.delivery_manager = DeliveryManager()
        self.delivery_manager.sort_products()
        self.cities = europe_top_cities
        self.cities_coordinates = {}
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

        self.furniture_df = pd.DataFrame()
        self.technology_df = pd.DataFrame()
        self.office_supplies_df = pd.DataFrame()

        self.exporter_nodes = []
        self.importer_nodes = []


    def initialize_stores(self):
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

    def save_to_pickle(self, filename):
        path = Path(__file__).parent.parent.parent / "parameters"

        if filename == "furniture":
            self.furniture_df.to_pickle(f"{path}/stores_furniture.pkl")
        elif filename == "technology":
            self.technology_df.to_pickle(f"{path}/stores_technology.pkl")
        elif filename == "office_supplies":
            self.office_supplies_df.to_pickle(f"{path}/stores_office_supplies.pkl")

    def load_from_pickle(self, filename):
        path = Path(__file__).parent.parent.parent / "parameters"

        if filename == "furniture":
            with open(f"{path}/stores_furniture.pkl", 'rb') as f:
                return pickle.load(f)
        elif filename == "technology":
            with open(f"{path}/stores_technology.pkl", 'rb') as f:
                return pickle.load(f)
        elif filename == "office_supplies":
            with open(f"{path}/stores_office_supplies.pkl", 'rb') as f:
                return pickle.load(f)
        return None

    def make_city_dict(self):
        furniture_stores = self.load_from_pickle("furniture")
        furniture_stores = furniture_stores[furniture_stores['geometry'].type == 'Point']

        self.cities_coordinates = {k: v for k, v in zip(furniture_stores['city'], furniture_stores['geometry'])}

    def haversine_km(self, lat1, lon1, lat2, lon2):
        """Oblicz dystans Haversine między dwoma punktami."""
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c

    def initialize_exporters(self, graph):

        exporter_cities = [
            "Berlin, Germany", "Paris, France", "London, United Kingdom", "Rome, Italy", "Madrid, Spain",
            "Warsaw, Poland", "Kyiv, Ukraine", "Bucharest, Romania", "Amsterdam, Netherlands", "Brussels, Belgium"
        ]

        for city in exporter_cities:
            lat_c, lon_c = self.cities_coordinates[city]
            closest_node = min(
                graph.nodes,
                key=lambda n: self.haversine_km(lat_c, lon_c, graph.nodes[n].get("y", 0), graph.nodes[n].get("x", 0))
            )
            self.exporter_nodes.append(closest_node)

    def initialize_importers(self, graph):
        importer_cities = [
            "Lisbon, Portugal", "Stockholm, Sweden", "Budapest, Hungary", "Vienna, Austria", "Zürich, Switzerland",
            "Dublin, Ireland", "Oslo, Norway", "Copenhagen, Denmark", "Helsinki, Finland", "Hamburg, Germany"
        ]

        for city in importer_cities:
            lat_c, lon_c = self.cities_coordinates[city]
            closest_node = min(
                graph.nodes,
                key=lambda n: self.haversine_km(lat_c, lon_c, graph.nodes[n].get("y", 0), graph.nodes[n].get("x", 0))
            )
            if closest_node not in self.exporter_nodes:
                self.importer_nodes.append(closest_node)


if __name__ == "__main__":
    # am = AgentManager()
    # am.initialize_stores()
    # am.save_to_pickle()
    am = AgentManager()
    # f = am.load_from_pickle("furniture")
    # print(f)
    # print(f[f['geometry'].type == 'Point'])
    am.make_city_dict()