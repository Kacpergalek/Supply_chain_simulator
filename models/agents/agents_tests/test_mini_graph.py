import networkx as nx
from models.agents.exporter_agent import ExporterAgent

# zbuduj Mini SimulationGraph (MultiDiGraph)
G = nx.MultiDiGraph()
# dodaj węzły
G.add_node(1, x=21.01, y=52.23)
G.add_node(2, x=19.94, y=50.06)
G.add_node(3, x=20.50, y=51.00)

# dodaj krawędzie (u,v,key,attrs)
G.add_edge(1, 2, key=0, length=250000, cost=100.0)    # 250 km
G.add_edge(1, 3, key=0, length=120000, cost=50.0)     # 120 km
G.add_edge(3, 2, key=0, length=130000, cost=60.0)     # 130 km

# symuluj minimalny interface SimulationGraph: implementacja safe_shortest_path
class FakeSimGraph(nx.MultiDiGraph):
    def safe_shortest_path(self, start, end, weigth="length"):
        return nx.shortest_path(self, start, end, weight=weigth)

sim = FakeSimGraph()
sim.add_nodes_from(G.nodes(data=True))
for u,v,k,d in G.edges(data=True, keys=True):
    sim.add_edge(u, v, key=k, **d)

exp = ExporterAgent(agent_id=1, node_id=1)
params = {"alpha":1.0, "beta":0.001, "avg_speed_km_per_day": 60.0}
res = exp.find_cheapest_path(sim, dest_node=2, params=params)
print(res)
