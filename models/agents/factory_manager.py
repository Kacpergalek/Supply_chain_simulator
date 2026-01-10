import pickle
from pathlib import Path

import pandas as pd
import geopandas as gpd
import osmnx as ox
import json

from input_data.agent_data.europe_top_cities import europe_top_cities

class FactoryManager:
    """
    - Query OpenStreetMap (via OSMnx) for industrial/craft/man-made features
      that correspond to different product categories (furniture, technology,
      office supplies, beauty).
    - Cache queries to disk as pickled GeoDataFrames to avoid repeated API calls.
    - Build a compact dictionary of representative factories per city for use
      by agents.

    Attributes
    ----------
    cities : dict[str, list[str]]
        Mapping of country -> list of cities to process.
    factories : dict[str, dict]
        Mapping of city -> chosen factory metadata
        (geometry, factory_name, factory_category).
    cols_of_interest : list[str]
        Columns kept from OSMnx results (name, subtype, geometry).
    tags_furniture, tags_technology, tags_office, tags_beauty : dict[str, list[str]]
        OSM tag specifications used to query industrial features.
    furniture_df, technology_df, office_supplies_df, beauty_df : GeoDataFrame
        Aggregated factory locations per category.
    """
    def __init__(self):
        self.cities = europe_top_cities
        self.factories = {}

        self.cols_of_interest = ['name', 'subtype', 'geometry']

        self.tags_furniture = {
            "industrial": ["furniture", "sawmill", "timber"],
            "craft": ["carpenter", "cabinet_maker", "upholsterer", "joiner"]
        }

        self.tags_technology = {
            "industrial": ["electronics", "microchip", "electrical", "technology"],
            "man_made": ["works"]  # 'works' is a generic factory, often refined by product tags, but useful fallback
        }

        self.tags_office = {
            "industrial": ["printing", "paper_mill", "pulp", "stationery", "plastic"]
        }

        self.tags_beauty = {
            "industrial": ["chemicals", "pharmaceutical", "cosmetics", "soap"],
            "craft": ["perfumery"]
        }

        self.furniture_df = gpd.GeoDataFrame()
        self.technology_df = gpd.GeoDataFrame()
        self.office_supplies_df = gpd.GeoDataFrame()
        self.beauty_df = gpd.GeoDataFrame()

    def _process_geodata(self, city, tags):
        """
        Query OSM for a single city and tag set, and normalize the result.

        Parameters
        ----------
        city : str
            Name of the city (as recognizable by OSM).
        tags : dict[str, list[str]]
            Tag filters passed to `ox.features.features_from_place`.

        Returns
        -------
        GeoDataFrame
            Filtered and normalized GeoDataFrame containing at least:
            - 'name', 'subtype', 'geometry', 'city'.
            Returns an empty GeoDataFrame on error.
        """
        try:
            gdf = ox.features.features_from_place(city, tags)
            gdf['subtype'] = pd.NA

            for key in tags.keys():
                if key in gdf.columns:
                    gdf['subtype'] = gdf['subtype'].fillna(gdf[key])

            gdf['city'] = city
            final_cols = self.cols_of_interest + ['city']
            gdf = gdf.reindex(columns=final_cols)
            gdf = gdf.dropna(subset=['geometry'])

            return gdf

        except Exception as e:
            return gpd.GeoDataFrame()

    def initialize_factories(self) -> None:
        """
        - For every city in `self.cities`:
            * Query OSM for each product category.
            * Append results to category-specific GeoDataFrames.
        - Persist the filtered list of successfully processed cities as JSON.
        - Save per-category GeoDataFrames as pickle files under `input_data`.
        """
        for country in self.cities:
            cities_to_remove = []
            for city in self.cities[country]:
                print(f"Querying Industry in: {city}...")

                try:
                    gdf_f = self._process_geodata(city, self.tags_furniture)
                    if not gdf_f.empty:
                        self.furniture_df = pd.concat([self.furniture_df, gdf_f], ignore_index=True)

                    gdf_t = self._process_geodata(city, self.tags_technology)
                    if not gdf_t.empty:
                        self.technology_df = pd.concat([self.technology_df, gdf_t], ignore_index=True)

                    gdf_o = self._process_geodata(city, self.tags_office)
                    if not gdf_o.empty:
                        self.office_supplies_df = pd.concat([self.office_supplies_df, gdf_o], ignore_index=True)

                    gdf_b = self._process_geodata(city, self.tags_beauty)
                    if not gdf_b.empty:
                        self.beauty_df = pd.concat([self.beauty_df, gdf_b], ignore_index=True)

                except Exception as e:
                    print(f"   > Error processing '{city}': {e}")
                    cities_to_remove.append(city)

            for city in cities_to_remove:
                self.cities[country].remove(city)

        with open('../../input_data/agent_data/europe_top_cities_factories_filtered.json', 'w') as fp:
            json.dump(self.cities, fp)
        self.save_to_pickle("furniture")
        self.save_to_pickle("technology")
        self.save_to_pickle("office_supplies")
        self.save_to_pickle("beauty")


    def save_to_pickle(self, filename: str) -> None:
        path = Path(__file__).parent.parent.parent / "input_data" / "factory_data"

        if filename == "furniture":
            self.furniture_df.to_pickle(f"{path}/factories_{filename}.pkl")
        elif filename == "technology":
            self.technology_df.to_pickle(f"{path}/factories_{filename}.pkl")
        elif filename == "office_supplies":
            self.office_supplies_df.to_pickle(f"{path}/factories_{filename}.pkl")
        elif filename == "beauty":
            self.beauty_df.to_pickle(f"{path}/factories_{filename}.pkl")

    def load_from_pickle(self, filename: str) -> pd.DataFrame:
        path = Path(__file__).parent.parent.parent / "input_data" / "factory_data" / f"factories_{filename}.pkl"
        if not path.exists():
            self.initialize_factories()
            self.save_to_pickle(filename)
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
                "factory_name": str,
                "factory_category": str
            }
        """
        self.furniture_df = self.load_from_pickle("furniture")
        factories = self.furniture_df[self.furniture_df['geometry'].type == 'Point']
        self.technology_df = self.load_from_pickle("technology")
        factories = pd.concat([factories, self.technology_df[self.technology_df['geometry'].type == 'Point']])
        self.office_supplies_df = self.load_from_pickle("office_supplies")
        factories = pd.concat([factories, self.office_supplies_df[self.office_supplies_df['geometry'].type == 'Point']])
        self.beauty_df = self.load_from_pickle("beauty")
        factories = pd.concat([factories, self.beauty_df[self.beauty_df['geometry'].type == 'Point']])

        for city in factories['city'].unique():
            factory = factories[factories['city'] == city].sample()
            store_dict = {"geometry": factory['geometry'].item(),
                          "factory_name": factory['name'].item(), "factory_category": factory['subtype'].item()}
            self.factories[factory['city'].item()] = store_dict
        return self.factories

if __name__ == '__main__':
    factory_manager = FactoryManager()
    f = factory_manager.load_from_pickle("furniture")
    t = factory_manager.load_from_pickle("technology")
    o = factory_manager.load_from_pickle("office_supplies")
    b = factory_manager.load_from_pickle("beauty")
    print(f"Furniture: {factory_manager.furniture_df.shape}")
    print(f"Technology: {factory_manager.technology_df.shape}")
    print(f"Office Supplies: {factory_manager.office_supplies_df.shape}")
    print(f"Beauty: {factory_manager.beauty_df.shape}")
    print(f"Furniture pkl: {f}")
    print(f"Technology pkl: {t}")
    print(f"Office Supplies pkl: {o}")
    print(f"Beauty pkl: {b}")