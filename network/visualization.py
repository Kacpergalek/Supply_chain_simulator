import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString
import matplotlib.colors as mcolors
import random
from pathlib import Path

def plot_agent_routes(graph, routes, exporter_nodes, importer_nodes,
                      #major_cities=None, 
                      node_type_attr="type", capacity_attr="capacity",
                      disrupted_nodes=None
                      ):
    """
    graph : SimulationGraph (nx.MultiDiGraph)
    routes : list of lists of nodes (ścieżki od find_shortest_path)
    exporter_nodes : list of node IDs
    importer_nodes : list of node IDs
    major_cities : dict {city_name: (lat, lon)} dla podpisów przy punktach
    disrupted_nodes : lista węzłów, które są wyłączone (np. z powodu zakłócenia)
    """
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

    save_path = Path(__file__).parent.parent / "assets/latest_map.png"

    if disrupted_nodes is None:
        disrupted_nodes = []

    fig, ax = plt.subplots(figsize=(15, 15))

    # Lista kolorów dla tras
    # Stała paleta: jasne, dobrze widoczne, powtarzalne kolory
    BRIGHT_COLORS = [
        '#1f77b4',  # niebieski
        '#ff7f0e',  # pomarańczowy
        '#2ca02c',  # zielony
        '#d62728',  # czerwony
        '#9467bd',  # fioletowy
        '#8c564b',  # brązowy
        '#e377c2',  # różowy
        '#7f7f7f',  # szary
        '#bcbd22',  # żółto-zielony
        '#17becf'   # turkusowy
    ]

    # Powtarzaj paletę cyklicznie (zawsze ten sam kolor dla tej samej trasy)
    colors = [BRIGHT_COLORS[i % len(BRIGHT_COLORS)] for i in range(len(routes))]

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
            ax.plot(x_vals, y_vals, color=colors[i % len(colors)], lw=lw, alpha=0.5)

        # Początek i koniec trasy
        ax.scatter(*coords_shifted[0], color='green', s=80, zorder=5)
        ax.scatter(*coords_shifted[-1], color='red', s=80, zorder=5)

        
        for idx in range(19, len(coords)-1, 20):
            x1, y1 = coords[idx]
            x2, y2 = coords[idx+1]
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle='->', color=colors[i % len(colors)], lw=3.5, alpha=1))

    # Węzły eksportera i importera + podpisy
    for n in exporter_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="green", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:
                    ax.text(x+0.1, y+0.1, city, fontsize=10, color="green", zorder=7, ha='right', va='bottom')

    for n in importer_nodes:
        x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
        ax.scatter(x, y, color="red", s=100, zorder=6)
        if major_cities:
            for city, (lat, lon) in major_cities.items():
                dist = ((lat - graph.nodes[n].get("y",0))**2 + (lon - graph.nodes[n].get("x",0))**2)**0.5
                if dist < 0.05:
                    ax.text(x, y-0.1, city, fontsize=10, color="red", zorder=7, ha='left', va='top')

    # Wyłączone węzły – czarne X
    # Wyłączone węzły – czarne X + podpis z ID
    # Wyłączone węzły – bardzo duże czarne X
    for n in disrupted_nodes:
        if n in graph.nodes:
            x, y = graph.nodes[n].get("x", 0), graph.nodes[n].get("y", 0)
            
            ax.scatter(
                    x, y,
                    marker='X',
                    color='black',
                    s=200,          # 🔧 mniejszy rozmiar
                    zorder=100,
                    linewidths=2    # 🔧 cieńsze linie
            )
                # 🔧 grubsze linie X-a
            # 🔧 dodaj podpis obok X-a, żeby było jasne który to węzeł
            ax.text(x + 0.05, y + 0.05, f"X {n}", fontsize=12, color="black", weight="bold", zorder=51)

            
            

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

    if save_path:
        save_path = Path(save_path)               # upewnij się, że to Path
        save_path.parent.mkdir(parents=True, exist_ok=True)  # utwórz katalog
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        # print(f"Wykres zapisany: {save_path.resolve()}")
