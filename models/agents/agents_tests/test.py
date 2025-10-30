# scripts/test_agents.py
from agents import ExporterAgent

# stwórz eksportera: id=1, przypisany do node_id=12345, produkuje 50 sztuk na krok, cena=5.0, finanse=500
exp = ExporterAgent(agent_id=1, node_id=12345, quantity=50, price=5.0, finances=500.0)

print(exp)           # debug: pokazuje stan startowy
exp.produce()        # wyprodukuj
print("po produkcji:", exp)
offer = exp.create_offer()   # oferta sprzedaży
print("Oferta:", offer)

# symulujemy sprzedaż 30 sztuk
sold, revenue = exp.sell(30)
print(f"Sprzedano {sold} szt., przychód = {revenue}. Stan konta = {exp.finances}, inventory = {exp.inventory}")
