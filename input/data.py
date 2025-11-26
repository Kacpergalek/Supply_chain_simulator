import osmnx as ox
import pandas as pd


def read_csv(file_name):
    df = pd.read_csv(file_name)
    if file_name == "data1.csv":
        return df[["Product type", "Price", "Availability", "Number of products sold", "Revenue generated",
        "Order quantities"]]
    else:
        return df[["product_id", "product_category_name", "product_weight_g", "product_length_cm", "product_height_cm",
        "product_width_cm"]]


if __name__ == "__main__":
    """ price = max (weight, dimensional weight) """
    """ dimensional = length * height * width / DIM factor (166 or 139) """

    """ every delivery has some amount of products 
     delivery cost is calculated with dimensional weight, length of the road, and transport type
     *) add transport types 
     *) add different delivery companies 
     *) add international shipping fee 
     *) add list of products in delivery 
     
     Real data for paths:
     *) add start point adn end point from csv
     *) find nodes and coordinates by city name
     """

    """ WAREHOUSE LOCALIZATION """

    place = "Praga, Warsaw, Poland"
    tags = {"building": True}

    buildings = ox.features.features_from_place(place, tags)
    print(buildings.columns)
