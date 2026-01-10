import json
import pickle
from pathlib import Path

import osmnx as ox
import pandas as pd
import geopandas as gpd

from input_data.agent_data.europe_top_cities import europe_top_cities
from models.delivery.product_manager import ProductManager


class RetailStoreManager:
    """
    - Query OpenStreetMap (via OSMnx) for retail locations tagged as furniture,
      technology, office supplies or beauty.
    - Cache queries to disk as pickled GeoDataFrames.
    - Build a mapping from city to a single representative store and assign
      product assortments using `ProductManager`.

    Attributes
    ----------
    cities : dict[str, list[str]]
        Mapping of country -> list of cities to process.
    stores : dict[str, dict]
        Mapping of city -> store metadata
        (geometry, store_name, store_category).
    cols_of_interest : list[str]
        Columns kept from OSMnx results (name, shop, geometry).
    tags_furniture, tags_technology, tags_office, tags_beauty : dict[str, list[str]]
        OSM tag specifications used to query different types of stores.
    furniture_df, technology_df, office_supplies_df, beauty_df : GeoDataFrame
        Aggregated store locations per category.
    product_manager : ProductManager
        Used to obtain product assortments for each store category.
    """
    def __init__(self):
        json_path = (Path(__file__).parent.parent.parent / "input_data" / "agent_data" /
                     "europe_top_cities_stores_filtered.json")
        if json_path.exists():
            with open(json_path) as fp:
                self.cities = json.load(fp)
        else:
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
        self.tags_beauty = {
            "shop": ["cosmetics", "chemist", "perfumery", "drugstore", "hairdresser_supply", "herbalist"]
        }
        self.furniture = []
        self.technology = []
        self.office_supplies = []
        self.beauty = []

        self.furniture_df = gpd.GeoDataFrame()
        self.technology_df = gpd.GeoDataFrame()
        self.office_supplies_df = gpd.GeoDataFrame()
        self.beauty_df = gpd.GeoDataFrame()

        self.product_manager = ProductManager()
        self.product_manager.sort_products()

    def initialize_stores(self) -> None:
        """
        - For every city in `self.cities`:
            * Query OSM for each store category.
            * Append results to category-specific GeoDataFrames.
            * If the city's polygon is not found, remove the city from the list.
        - Persist the filtered list of successfully processed cities as JSON.
        - Save per-category GeoDataFrames as pickle files under `input_data`.
        """
        for country in self.cities:
            cites_to_remove = []
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

                    gdf_b = ox.features.features_from_place(
                        city, self.tags_beauty)
                    gdf_b = gdf_b[self.cols_of_interest].dropna()
                    gdf_b['city'] = city
                    self.beauty_df = pd.concat(
                        [self.beauty_df, gdf_b], ignore_index=True)

                except Exception as e:
                    print(f"   > Polygon not found for '{city}'")

            for city in cites_to_remove:
                self.cities[country].remove(city)

        with open('../../input_data/agent_data/europe_top_cities_stores_filtered.json', 'w') as fp:
            json.dump(self.cities, fp)
        self.save_to_pickle("furniture")
        self.save_to_pickle("technology")
        self.save_to_pickle("office_supplies")
        self.save_to_pickle("beauty")

    def save_to_pickle(self, filename: str) -> None:
        path = Path(__file__).parent.parent.parent / "input_data" / "store_data"

        if filename == "furniture":
            self.furniture_df.to_pickle(f"{path}/stores_furniture.pkl")
        elif filename == "technology":
            self.technology_df.to_pickle(f"{path}/stores_technology.pkl")
        elif filename == "office_supplies":
            self.office_supplies_df.to_pickle(f"{path}/stores_office_supplies.pkl")
        elif filename == "beauty":
            self.beauty_df.to_pickle(f"{path}/stores_beauty.pkl")

    def load_from_pickle(self, filename: str) -> pd.DataFrame:
        path = Path(__file__).parent.parent.parent / "input_data" / "store_data" / f"stores_{filename}.pkl"
        if not path.exists():
            self.initialize_stores()
        with open(path, 'rb') as f:
            return pickle.load(f)

    def make_city_dict(self) -> dict:
        """
        Returns
        -------
        dict[str, dict]
            Dictionary mapping:
            city -> {
                "geometry": Point,
                "store_name": str,
                "store_category": str  # OSM 'shop' tag
            }
        """
        self.furniture_df = self.load_from_pickle("furniture")
        stores = self.furniture_df[self.furniture_df['geometry'].type == 'Point']
        self.technology_df = self.load_from_pickle("technology")
        stores = pd.concat([stores, self.technology_df[self.technology_df['geometry'].type == 'Point']])
        self.office_supplies_df = self.load_from_pickle("office_supplies")
        stores = pd.concat([stores, self.office_supplies_df[self.office_supplies_df['geometry'].type == 'Point']])
        self.beauty_df = self.load_from_pickle("beauty")
        stores = pd.concat([stores, self.beauty_df[self.beauty_df['geometry'].type == 'Point']])

        for city in stores['city'].unique():
            store = stores[stores['city'] == city].sample()
            store_dict = {"geometry": store['geometry'].item(),
                          "store_name": store['name'].item(), "store_category": store['shop'].item()}
            self.stores[store['city'].item()] = store_dict
        return self.stores

if __name__ == '__main__':
    retail_store_manager = RetailStoreManager()
    retail_store_manager.initialize_stores()