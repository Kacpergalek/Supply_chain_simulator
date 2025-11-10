import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.affinity import translate
import matplotlib.colors as mcolors
import random

def plot_agent_routes(graph, routes, exporter_nodes, importer_nodes,
                      major_cities=None, node_type_attr="type", capacity_attr="capacity"):
    """
    graph : SimulationGraph (nx.MultiDiGraph)
    routes : list of lists of nodes (ścieżki od find_shortest_path)
    exporter_nodes : list of node IDs
    importer_nodes : list of node IDs
    major_cities : dict {city_name: (lat, lon)} dla podpisów przy punktach
    """
    fig, ax = plt.subplots(figsize=(15, 15))

    # Lista kolorów dla tras
    colors = list(mcolors.TABLEAU_COLORS.values())
    random.shuffle(colors)

    # Maksymalna przepustowość dla skalowania grubości
    max_capacity = max([data.get(capacity_attr, 1) for u, v, k, data in graph.edges(data=True, keys=True)] + [1])

    # Tło - wszystkie krawędzie cienko szare
    edges_data = []
    for u, v, key, data in graph.edges(data=True, keys=True):
        geom = LineString([
            (graph.nodes[u].get("x", 0), graph.nodes[u].get("y", 0)),
            (graph.nodes[v].get("x", 0), graph.nodes[v].get("y", 0))
        ])
        edges_data.append({"geometry": geom, "capacity": data.get(capacity_attr, 1)})
    gdf_edges = gpd.GeoDataFrame(edges_data, crs="EPSG:4326")
    gdf_edges.plot(ax=ax, color="lightgrey", linewidth=0.5, alpha=0.5)

    # Trasy agentów
    for i, path in enumerate(routes):
        coords = [(graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)) for n in path]
        shift_val = 0.0001 * i  # przesunięcie aby nie nachodziły
        coords_shifted = [(x + shift_val, y + shift_val) for x, y in coords]

        # Rysowanie krawędzi trasy wg capacity
        for j, (u, v) in enumerate(zip(path[:-1], path[1:])):
            x_vals = [coords_shifted[j][0], coords_shifted[j+1][0]]
            y_vals = [coords_shifted[j][1], coords_shifted[j+1][1]]
            cap = graph[u][v][0].get(capacity_attr, 1)
            lw = 0.5 + (cap / max_capacity) * 3
            ax.plot(x_vals, y_vals, color=colors[i % len(colors)], lw=lw, alpha=0.8)

        # Początek i koniec trasy
        ax.scatter(*coords_shifted[0], color='green', s=80, zorder=5)
        ax.scatter(*coords_shifted[-1], color='red', s=80, zorder=5)

    # Węzły eksportera i importera + podpisy
    for n in exporter_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="green", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                # przypisanie miasta do najbliższego węzła
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:  # dopasowanie threshold
                    ax.text(x, y, city, fontsize=10, color="green", zorder=7, ha='right', va='bottom')

    for n in importer_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="red", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:
                    ax.text(x, y, city, fontsize=10, color="red", zorder=7, ha='left', va='top')

    ax.legend(["Routes", "Exporters", "Importers"])
    ax.set_title("Agent Routes Visualization", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.show()
