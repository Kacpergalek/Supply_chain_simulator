class Product:
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