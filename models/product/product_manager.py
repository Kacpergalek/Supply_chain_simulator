import pandas as pd

from pathlib import Path
from models.product.product import Product


class ProductManager:
    """
        Manages the catalog of products and their categorization into broad store
        categories (furniture, technology, office supplies, beauty).

        Responsibilities
        ----------------
        - Load product data from CSV files.
        - Build `Product` objects and split them into category-specific lists.
        - Expose category-specific product lists based on a store's tag/category.

        Attributes
        ----------
        categories : list[str]
            Unique list of product categories found in the CSV data.
        furniture : list[Product]
            All products categorized as furniture.
        technology : list[Product]
            All products categorized as technology / electronics.
        office_supplies : list[Product]
            All products categorized as office supplies.
        beauty : list[Product]
            All products treated as "Beauty" (fallback / non-standard categories).
        tags_furniture, tags_technology, tags_office, tags_beauty : list[str]
            Lowercase store-category tags used to map store types to product lists.
        """
    def __init__(self):
        self.categories = []
        self.furniture = []
        self.technology = []
        self.office_supplies = []
        self.beauty = []

        self.tags_furniture = ["furniture", "bed", "kitchen", "lighting", "interior_decoration", "bathroom_furnishing"]
        self.tags_technology = ["electronics", "computer", "mobile_phone", "hifi", "photo", "video_games"]
        self.tags_office = ["office_supplies", "stationery", "copyshop", "printer_ink"]
        self.tags_beauty = ["cosmetics", "chemist", "perfumery", "drugstore", "hairdresser_supply", "herbalist"]

    def initialize_products(self, store_category: str) -> list[Product]:
        """
        Return a list of products appropriate for a store with a given category tag.

        Parameters
        ----------
        store_category : str
            Lowercase store category/tag (e.g. 'furniture', 'electronics').

        Returns
        -------
        list[Product]
            Products corresponding to the given store category tag.
            Returns an empty list if the tag does not match any known group.
        """
        if store_category in self.tags_furniture:
            return self.furniture
        elif store_category in self.tags_technology:
            return self.technology
        elif store_category in self.tags_office:
            return self.office_supplies
        elif store_category in self.tags_beauty:
            return self.beauty
        else:
            return []

    def sort_products(self):
        """
                Load product data from CSV files and populate category-specific lists.

                This method:
                - Reads product data from `products.csv` and `products2.csv` in the
                  `input_data` directory.
                - Concatenates both datasets, drops duplicate `Product ID`s, and
                  reorders columns.
                - Builds `Product` instances and assigns them into lists based on the
                  high-level `Category` field:
                    * "Furniture"        -> `self.furniture`
                    * "Technology"       -> `self.technology`
                    * "Office Supplies"  -> `self.office_supplies`
                    * anything else      -> `self.beauty`, with category normalized to "Beauty"

                Notes
                -----
                - If the product does not have Name in the csv file it will be set to None
                - If the product does not have a subcategory it will be set to the category from the csv file
        """
        path = Path(__file__).parent.parent.parent / "data" / "input_data"
        columns = ["Product ID", "Category", "Sub-Category", "Product Name", "Price", "Quantity"]
        products_df = pd.read_csv(f"{path}/products.csv")
        products_df = pd.concat([products_df, pd.read_csv(f"{path}/products2.csv")])
        products_df = products_df.reindex(columns=columns)

        products_df.drop_duplicates(subset=['Product ID'], inplace=True)
        self.categories = list(set([row["Category"] for index, row in products_df.iterrows()]))

        for index, row in products_df.iterrows():
            product = Product(row["Product ID"], row["Product Name"], row["Category"], row["Sub-Category"],
                              row["Price"] / row["Quantity"])
            if row["Category"] == "Furniture":
                self.furniture.append(product)
            elif row["Category"] == "Technology":
                self.technology.append(product)
            elif row["Category"] == "Office Supplies":
                self.office_supplies.append(product)
            elif row["Category"] in ("skincare", "haircare", "cosmetics"):
                product.subcategory = row["Category"]
                product.category = "Beauty"
                product.name = "None"
                self.beauty.append(product)