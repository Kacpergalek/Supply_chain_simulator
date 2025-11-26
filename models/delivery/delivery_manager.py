import pandas as pd

from models.delivery.product import Product


class DeliveryManager:
    def __init__(self):
        self.categories = []
        self.furniture = []
        self.technology = []
        self.office_supplies = []

    def read_csv(self, filepath, columns):
        df = pd.read_csv(filepath, encoding='cp1252')
        return df[columns]

    def sort_products(self):
        columns = ["Product ID", "Category", "Sub-Category", "Product Name", "Sales", "Quantity"]
        products_df = pd.DataFrame(self.read_csv("../../input/products.csv", columns))
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