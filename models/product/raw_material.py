class RawMaterial:
    def __init__(self, material_id: str, name: str, category: str, unit_cost: float):
        self.material_id = material_id
        self.name = name
        self.category = category
        self.retail_price = unit_cost

    def to_dict(self) -> dict[str, str | float]:
        return {
            "material_id": self.material_id,
            "name": self.name,
            "category": self.category,
            "retail_price": self.retail_price
        }