# network/visualization.py
import folium
from pathlib import Path

def plot_agent_routes(
    graph,
    routes,
    exporter_nodes,
    importer_nodes,
    node_type_attr="type",
    capacity_attr="capacity",
    disrupted_nodes=None
):
    if disrupted_nodes is None:
        disrupted_nodes = []

    # --- INTERACTIVE BASEMAP OSM ---
    m = folium.Map(location=[52.23, 21.01], zoom_start=6)

    # === 🔥 Rysujemy TYLKO trasy agentów ===
    colors = ['blue','orange','green','red','purple','brown','#000000','gray','olive','cyan']

    for i, path in enumerate(routes):
        coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in path]
        folium.PolyLine(
            coords,
            color=colors[i % len(colors)],
            weight=4,
            opacity=0.8
        ).add_to(m)

    # Exporters
    for n in exporter_nodes:
        folium.CircleMarker(
            location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
            radius=7,
            color="green",
            fill=True,
            fill_color="green",
            tooltip=f"Exporter {graph.nodes[n].get('city','')}"
        ).add_to(m)

    # Importers
    for n in importer_nodes:
        folium.CircleMarker(
            location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
            radius=7,
            color="red",
            fill=True,
            fill_color="red",
            tooltip=f"Importer {graph.nodes[n].get('city','')}"
        ).add_to(m)

    # === 🔥 RYSUJEMY WYBRANY WĘZEŁ (DISRUPTED NODE) ===
    for n in disrupted_nodes:
        if n in graph.nodes:
            folium.Marker(
                location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
                icon=folium.DivIcon(
                    html="<b style='color:black;font-size:22px;'>X</b>"
                ),
                tooltip=f"Disrupted node {n}"
            ).add_to(m)

    # Save final map
    save_path = Path(__file__).parent.parent / "static/latest_map.html"
    m.save(save_path)
