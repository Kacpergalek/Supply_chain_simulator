class Product:
    """
    Parameters
    ----------
    product_id : int | str
        Unique identifier for the product (as found in the CSV source).
    name : str | None
        Human-readable product name. May be `None` if not provided in the
        CSV; downstream code should handle missing names gracefully.
    category : str
        High-level product category (e.g. "Furniture", "Technology",
        "Office Supplies", "Beauty").
    subcategory : str
        More fine-grained category (e.g. "Chairs", "Phones", "Binders").
        In some cases, this might be equal to `category` if no specific
        subcategory is available.
    retail_price : float
        Unit retail price used when computing parcel values and costs.
    """
    def __init__(self, product_id: str, name: str, category: str, subcategory: str, retail_price: float):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.subcategory = subcategory
        self.retail_price = retail_price

    def to_dict(self) -> dict[str, str | float]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "retail_price": self.retail_price,
        }