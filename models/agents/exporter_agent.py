from .base_agent import BaseAgent

class ExporterAgent(BaseAgent):
    """
    Agent typu Eksporter (dziedziczy z BaseAgent).
    Dodatkowe atrybuty:
      - quantity: ile produkuje / ma do wysłania per krok (int)
      - price: cena za jednostkę (float)
      - finances: stan konta / budżet (float)
    Dodatkowe pola:
      - inventory: aktualny zapas (int) - startuje od 0
    Proste metody:
      - produce()        -> zwiększa inventory o quantity
      - create_offer(qty=None) -> zwraca ofertę sprzedaży (qty i unit_price)
      - sell(qty)        -> aktualizuje inventory i finances (zwraca kwotę)
    """
    def __init__(self, agent_id, node_id, country="Poland", quantity=100, price=10.0, finances=1000.0):
        super().__init__(agent_id, node_id, country)
        self.quantity = int(quantity)
        self.price = float(price)
        self.finances = float(finances)
        self.inventory = 0  # ile aktualnie ma w magazynie

    def __repr__(self):
        return (f"ExporterAgent(id={self.agent_id}, node={self.node_id}, qty_per_step={self.quantity}, "
                f"price={self.price}, finances={self.finances}, inventory={self.inventory})")

    def produce(self):
        """Proste wytwarzanie: przyrost zapasu o 'quantity'."""
        self.inventory += self.quantity
        return self.inventory

    def create_offer(self, qty=None):
        """
        Tworzy ofertę sprzedaży. Jeśli qty nie podane -> proponuje max możliwy (min(inventory, quantity)).
        Zwraca dict: {'agent_id', 'node_id', 'qty', 'unit_price'}.
        """
        if qty is None:
            qty = min(self.inventory, self.quantity)
        qty = int(min(qty, self.inventory))
        return {
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "qty": qty,
            "unit_price": self.price
        }

    def sell(self, qty):
        """
        Realizuje sprzedaż: zmniejsza inventory i zwiększa finances.
        Zwraca revenue (float). Jeśli qty > inventory -> sprzedaje tyle ile ma.
        """
        qty = int(qty)
        sold = min(qty, self.inventory)
        revenue = sold * self.price
        self.inventory -= sold
        self.finances += revenue
        return sold, revenue

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "quantity": self.quantity,
            "price": self.price,
            "finances": self.finances,
            "inventory": self.inventory
        })
        return d
