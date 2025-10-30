class BaseAgent:
    """
    Podstawowy agent.
    Atrybuty:
      - agent_id: int        (unikalny identyfikator agenta)
      - node_id: int         (id węzła w grafie / OSMnx, na razie przechowujemy int)
      - country: str         (np. "Poland")
    """
    def __init__(self, agent_id, node_id, country="Poland"):
        self.agent_id = int(agent_id)
        self.node_id = int(node_id)
        self.country = str(country)

    def __repr__(self):
        return f"BaseAgent(id={self.agent_id}, node={self.node_id}, country='{self.country}')"

    # prosta metoda pomocnicza do serializacji (np. zapis do JSON)
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "country": self.country
        }
