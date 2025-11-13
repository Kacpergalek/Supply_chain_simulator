# network/empty_visualization.py
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import LineString
from pathlib import Path

def plot_empty_map(graph):
    """
    Rysuje pustą mapę sieci (szare drogi bez eksporterów/importerów)
    i zapisuje do assets/latest_map.png
    """
    save_path = Path(__file__).parent.parent / "assets/latest_map.png"

    fig, ax = plt.subplots(figsize=(15, 15))

    # wszystkie krawędzie jako tło (szare, cienkie)
    edges_data = []
    for u, v, key, data in graph.edges(data=True, keys=True):
        geom = LineString([
            (graph.nodes[u].get("x", 0), graph.nodes[u].get("y", 0)),
            (graph.nodes[v].get("x", 0), graph.nodes[v].get("y", 0))
        ])
        edges_data.append({"geometry": geom})
    gdf_edges = gpd.GeoDataFrame(edges_data, crs="EPSG:4326")
    gdf_edges.plot(ax=ax, color="lightgrey", linewidth=0.4, alpha=0.7)

    ax.set_title("Poland Transport Network (Empty Map)", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()

    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Pusta mapa zapisana: {save_path.resolve()}")
