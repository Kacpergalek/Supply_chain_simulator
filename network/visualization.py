import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

def plot_graph(sim_graph,
               exporters=None,
               importers=None,
               paths=None,
               basemap=False,
               show_arrows=True,
               figsize=(10, 10),
               title="Mapa sieci transportowej"):
    """
    Wizualizacja grafu transportowego (SimulationGraph) z eksportami i importerami.

    Args:
        sim_graph: obiekt SimulationGraph (działa też z NetworkX)
        exporters: lista node_id eksporterów
        importers: lista node_id importerów
        paths: lista ścieżek (listy node_id) – np. z find_cheapest_path
        basemap: czy rysować tło geopandas (domyślnie False)
        show_arrows: czy pokazywać kierunki przepływu
        figsize: rozmiar wykresu
        title: tytuł wykresu
    """

    pos = {node: (data['x'], data['y'])
           for node, data in sim_graph.nodes(data=True)
           if 'x' in data and 'y' in data}

 
    edges = []
    for u, v, data in sim_graph.edges(data=True):
        cap = data.get('capacity', 1000)
        flow = data.get('flow', 0)
        cost = data.get('cost', 1)
        edges.append((u, v, cap, flow, cost))

    df_edges = pd.DataFrame(edges, columns=['u', 'v', 'capacity', 'flow', 'cost'])

    node_colors = []
    for n, d in sim_graph.nodes(data=True):
        if exporters and n in exporters:
            node_colors.append("red")
        elif importers and n in importers:
            node_colors.append("green")
        else:
            node_colors.append("gray")

    plt.figure(figsize=figsize)
    plt.title(title)


    widths = [0.5 + data.get('capacity', 1000) / 5000 for _, _, data in sim_graph.edges(data=True)]

    nx.draw_networkx_edges(sim_graph, pos, width=widths, alpha=0.5, edge_color="blue", arrows=show_arrows)
    nx.draw_networkx_nodes(sim_graph, pos, node_color=node_colors, node_size=30)
    nx.draw_networkx_labels(sim_graph, pos, font_size=6)

  
    if paths:
        for path in paths:
            nx.draw_networkx_edges(
                sim_graph, pos,
                edgelist=list(zip(path[:-1], path[1:])),
                width=2.5, edge_color="orange"
            )

    plt.axis("off")
    plt.show()

    return plt
