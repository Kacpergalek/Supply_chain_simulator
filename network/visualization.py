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

    # === 🔥 NIE rysujemy całej sieci dróg — TYLKO TRASY ===

    # Draw routes
    colors = ['blue','orange','green','red','purple','brown','pink','gray','olive','cyan']
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
        city = graph.nodes[n].get("city")
        folium.CircleMarker(
            location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
            radius=7,
            color="green",
            fill=True,
            fill_color="green",
            tooltip=city or "Exporter"
        ).add_to(m)

    # Importers
    for n in importer_nodes:
        city = graph.nodes[n].get("city")
        folium.CircleMarker(
            location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
            radius=7,
            color="red",
            fill=True,
            fill_color="red",
            tooltip=city or "Importer"
        ).add_to(m)

    # Disrupted nodes
    for n in disrupted_nodes:
        if n in graph.nodes:
            folium.Marker(
                location=(graph.nodes[n]["y"], graph.nodes[n]["x"]),
                icon=folium.DivIcon(html=f"<b style='color:black;font-size:22px;'>X</b>"),
                tooltip="Wyłączony"
            ).add_to(m)

    # Save interactive map
    save_path = Path(__file__).parent.parent / "static/latest_map.html"
    m.save(save_path)
