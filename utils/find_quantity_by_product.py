from models.product.product import Product

def find_quantity_by_product(parcel: list[tuple[Product, int]] | None, product: Product) -> int:
    if not parcel:
        return 0

    for product_in_parcel, quantity in parcel:
        if product_in_parcel == product:
            try:
                return int(quantity or 0)
            except Exception:
                return 0
    return 0
