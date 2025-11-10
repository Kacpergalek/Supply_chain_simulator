import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString
import matplotlib.colors as mcolors
import random

def plot_agent_routes(graph, routes, exporter_nodes, importer_nodes,
                      major_cities=None, node_type_attr="type", capacity_attr="capacity",
                      disrupted_nodes=None):
    """
    graph : SimulationGraph (nx.MultiDiGraph)
    routes : list of lists of nodes (ścieżki od find_shortest_path)
    exporter_nodes : list of node IDs
    importer_nodes : list of node IDs
    major_cities : dict {city_name: (lat, lon)} dla podpisów przy punktach
    disrupted_nodes : lista węzłów, które są wyłączone (np. z powodu zakłócenia)
    """
    if disrupted_nodes is None:
        disrupted_nodes = []

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

        # Strzałki na trasie – co 5 węzłów (duże odstępy)
        arrow_interval = 5
        for idx in range(arrow_interval - 1, len(path) - 1, arrow_interval):
            start_idx = idx
            end_idx = idx + 1
            if end_idx >= len(coords_shifted):
                break
            x1, y1 = coords_shifted[start_idx]
            x2, y2 = coords_shifted[end_idx]
            dx = x2 - x1
            dy = y2 - y1
            # Strzałka w środku odcinka
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            ax.annotate('', xy=(mid_x, mid_y), xytext=(mid_x - dx * 0.3, mid_y - dy * 0.3),
                        arrowprops=dict(arrowstyle='->', color=colors[i % len(colors)], lw=2),
                        zorder=10)

    # Węzły eksportera i importera + podpisy
    for n in exporter_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="green", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:
                    ax.text(x, y, city, fontsize=10, color="green", zorder=7, ha='right', va='bottom')

    for n in importer_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="red", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:
                    ax.text(x, y, city, fontsize=10, color="red", zorder=7, ha='left', va='top')

    # Wyłączone węzły – czarne X
    for n in disrupted_nodes:
        if n in graph.nodes:
            x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
            ax.scatter(x, y, marker='X', color='black', s=120, zorder=10, linewidths=2)

    # Legenda
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='gray', lw=1, label='Drogi (tło)'),
        Line2D([0], [0], color='blue', lw=2, label='Trasy agentów'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Eksporterzy'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=8, label='Importerzy'),
        Line2D([0], [0], marker='X', color='w', markerfacecolor='black', markersize=10, label='Wyłączone węzły')
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    ax.set_title("Agent Routes Visualization", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    plt.show()