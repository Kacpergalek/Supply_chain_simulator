class Product:
    def __init__(self, product_id: str, name: str, category: str, subcategory: str, production_price: float, quantity: int):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.subcategory = subcategory
        self.production_price = production_price
        self.quantity = quantity

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "production_price": self.production_price,
            "quantity": self.quantity
        }