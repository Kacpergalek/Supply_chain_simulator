import sys, os, math
import networkx as nx
import pandas as pd
from pathlib import Path
import pickle


project_root = os.path.abspath("..")
if project_root not in sys.path:
    sys.path.append(project_root)
from network.graph_reader import GraphManager
import models.agents.exporter_agent as exp_mod
print("ExporterAgent module file:", exp_mod.__file__)
print("ExporterAgent ma metodę find_cheapest_path:", hasattr(exp_mod.ExporterAgent, "find_cheapest_path"))

from network.simulation_graph import SimulationGraph
'''
reader = GraphManager()
try:
    graph = reader.load_pickle_graph("poland_motorway_trunk_primary.pkl")
    print("✅ Załadowano SimulationGraph z pliku poland_motorway_trunk_primary.pkl")
except Exception as e:
    print("❌ Błąd wczytywania grafu:", e)
    graph = None
'''
def initiation(graph):


    major_cities = {
        "Warszawa": (52.23, 21.01),
        "Kraków": (50.06, 19.94),
        "Łódź": (51.77, 19.46),
        "Wrocław": (51.11, 17.03),
        "Poznań": (52.41, 16.93),
        "Gdańsk": (54.35, 18.65),
        "Szczecin": (53.43, 14.55),
        "Lublin": (51.25, 22.57),
        "Katowice": (50.26, 19.03),
        "Białystok": (53.13, 23.15),
        "Rzeszów": (50.04, 22.00),
        "Olsztyn": (53.78, 20.49),
        "Toruń": (53.01, 18.60),
        "Bydgoszcz": (53.12, 18.01),
        "Kielce": (50.87, 20.63),
        "Zielona Góra": (51.94, 15.50),
        "Opole": (50.67, 17.93),
        "Gorzów Wielkopolski": (52.73, 15.24),
        "Radom": (51.40, 21.15),
        "Częstochowa": (50.81, 19.12),
    }

    def haversine_km(lat1, lon1, lat2, lon2):
        """Oblicz dystans Haversine między dwoma punktami."""
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c



    exporter_cities = [
        "Warszawa", "Kraków", "Poznań", "Gdańsk", "Wrocław",
        "Szczecin", "Lublin", "Katowice", "Białystok", "Łódź"
    ]

    exporter_nodes = []
    for city in exporter_cities:
        lat_c, lon_c = major_cities[city]
        closest_node = min(
            graph.nodes,
            key=lambda n: haversine_km(lat_c, lon_c, graph.nodes[n].get("y", 0), graph.nodes[n].get("x", 0))
        )
        exporter_nodes.append(closest_node)

    print(f"✅ Wybrano {len(exporter_nodes)} eksporterów: {exporter_nodes}")



    importer_cities = [
        "Rzeszów", "Olsztyn", "Bydgoszcz", "Toruń", "Kielce",
        "Zielona Góra", "Opole", "Gorzów Wielkopolski", "Radom", "Częstochowa"
    ]

    importer_nodes = []
    for city in importer_cities:
        lat_c, lon_c = major_cities[city]
        closest_node = min(
            graph.nodes,
            key=lambda n: haversine_km(lat_c, lon_c, graph.nodes[n].get("y", 0), graph.nodes[n].get("x", 0))
        )
        if closest_node not in exporter_nodes:
            importer_nodes.append(closest_node)

    print(f"✅ Wybrano {len(importer_nodes)} importerów: {importer_nodes}")



    params = {
        "alpha": 1.0,
        "beta": 1.0,
        "gamma": 0.0,
        "avg_speed_km_per_day": 60.0
    }

    results = []

    graph_undirected = SimulationGraph(default_capacity=graph.default_capacity,
                                    default_price=graph.default_price,
                                    incoming_graph_data=graph)


    for i, (exp_node, imp_node) in enumerate(zip(exporter_nodes, importer_nodes), start=1):
        agent = exp_mod.ExporterAgent(agent_id=i, node_id=exp_node)
        try:
            result = agent.find_cheapest_path(graph_undirected, dest_node=imp_node, params=params)
            results.append({
                "agent_id": i,
                "exporter_node": exp_node,
                "importer_node": imp_node,
                **result
            })
            print(f"✅ Agent {i}: {exp_node} → {imp_node} | dystans: {result['total_distance_km']:.2f} km | koszt: {result['estimated_cost']:.2f}")
        except Exception as e:
            print(f"❌ {exp_node} → {imp_node} | błąd: {e}")
    
    data = {
        "exporter_node": [r["exporter_node"] for r in results],
        "importer_node": [r["importer_node"] for r in results],
        "results": results
    }

    path = Path(__file__).parent.parent / "network_data" / "paths.pkl"
    with open(path, "wb") as f:
        pickle.dump(data, f)

    return results




    #df_paths = pd.DataFrame(results)
    #print(df_paths)
    #display(df_paths[["exporter_node", "importer_node", "total_distance_km", "estimated_cost", "estimated_lead_time_days", "method"]])