from .. import ExporterAgent


def test_exporter():
    exp = ExporterAgent(agent_id=1, node_id=101, quantity=50, price=5.0, finances=500.0)
    exp.produce()
    print(exp)
    offer = exp.create_offer()
    print("Oferta:", offer)
    sold, revenue = exp.sell(20)
    print(f"Sprzedano {sold}, przychód {revenue}, stan magazynu: {exp.inventory}")

if __name__ == "__main__":
    test_exporter()
