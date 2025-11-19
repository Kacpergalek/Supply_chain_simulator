import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString
import matplotlib.colors as mcolors
import random
from pathlib import Path
import contextily as ctx
import pyproj

def plot_agent_routes(
    graph,
    routes,
    exporter_nodes,
    importer_nodes,
    node_type_attr="type",
    capacity_attr="capacity",
    disrupted_nodes=None
):
    """
    Wizualizacja tras agentów + eksport/import + wyłączone węzły
    z podkładem OpenStreetMap.
    """
    if disrupted_nodes is None:
        disrupted_nodes = []

    save_path = Path(__file__).parent.parent / "assets/latest_map.png"

    fig, ax = plt.subplots(figsize=(15, 15))

    # ---- TRANSFORMER EPSG 4326 -> 3857 (Mercator) ----
    project = pyproj.Transformer.from_crs(4326, 3857, always_xy=True).transform

    # ------- TŁO: WSZYSTKIE DROGI SZARE -------
    edges_data = []
    for u, v, key, data in graph.edges(data=True, keys=True):
        x1, y1 = graph.nodes[u]["x"], graph.nodes[u]["y"]
        x2, y2 = graph.nodes[v]["x"], graph.nodes[v]["y"]
        geom = LineString([(x1, y1), (x2, y2)])
        edges_data.append({"geometry": geom})

    gdf_edges = gpd.GeoDataFrame(edges_data, crs="EPSG:4326")
    gdf_edges = gdf_edges.to_crs(epsg=3857)
    gdf_edges.plot(ax=ax, color="lightgrey", linewidth=0.5, alpha=0.5)

    # ------- PODKŁAD OpenStreetMap -------
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # Kolory tras
    BRIGHT_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    colors = [BRIGHT_COLORS[i % len(BRIGHT_COLORS)] for i in range(len(routes))]

    # -------- RYSOWANIE TRAS AGENTÓW --------
    max_capacity = max(
        [data.get(capacity_attr, 1) for u, v, k, data in graph.edges(data=True, keys=True)]
        + [1]
    )

    for i, path in enumerate(routes):
        color = colors[i % len(colors)]
        coords = [
            project(graph.nodes[n]["x"], graph.nodes[n]["y"])
            for n in path
        ]

        # przesunięcie, żeby linie nie nachodziły
        shift = 10 * i
        coords_shifted = [(x + shift, y + shift) for x, y in coords]

        # rysowanie po segmentach
        for j, (u, v) in enumerate(zip(path[:-1], path[1:])):
            x1, y1 = coords_shifted[j]
            x2, y2 = coords_shifted[j + 1]

            cap = graph[u][v][0].get(capacity_attr, 1)
            lw = 0.5 + 3 * (cap / max_capacity)

            ax.plot([x1, x2], [y1, y2], color=color, lw=lw, alpha=0.7)

    # ------ RYSOWANIE EKSPORTERÓW / IMPORTERÓW ------
    def draw_point(n, color):
        x, y = graph.nodes[n]["x"], graph.nodes[n]["y"]
        x_m, y_m = project(x, y)
        ax.scatter(x_m, y_m, color=color, s=120, zorder=10)

    for n in exporter_nodes:
        draw_point(n, "green")

    for n in importer_nodes:
        draw_point(n, "red")

    # -------- WYŁĄCZONE WĘZŁY (duży X) --------
    for n in disrupted_nodes:
        if n in graph.nodes:
            x, y = graph.nodes[n]["x"], graph.nodes[n]["y"]
            x_m, y_m = project(x, y)

            ax.scatter(
                x_m, y_m,
                marker="X",
                color="black",
                s=300,
                zorder=20
            )
            ax.text(
                x_m + 150, y_m + 150, f"X {n}",
                fontsize=12,
                color="black",
                weight="bold",
                zorder=21
            )

    # -------- FORMATOWANIE --------
    ax.set_axis_off()
    plt.tight_layout()

    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
