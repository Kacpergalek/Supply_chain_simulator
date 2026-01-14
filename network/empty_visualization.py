import folium
from pathlib import Path
from network.graph_reader import GraphManager

def plot_empty_map():
    """
    Rysuje pustą mapę (bez sieci dróg, bez eksporterów/importerów)
    bazującą wyłącznie na podkładzie OpenStreetMap.
    Zapisuje do static/latest_map.html.
    """

    # Ładujemy graf tylko po to, żeby ewentualnie użyć środka Polski
    # (logiki grafu nie ruszamy, ale nie korzystamy z krawędzi)
    reader = GraphManager()
    _ = reader.load_pickle_graph("polska_motorway.pkl")

    # Bardzo szybka interaktywna mapa
    m = folium.Map(location=[52.23, 21.01], zoom_start=6)

    # --- 🔥 Brak rysowania krawędzi! ---
    # Dzięki temu mapa ładuje się w ~100 ms.

    # Zapis do HTML
    save_path = Path(__file__).parent.parent / "static/latest_map.html"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(save_path)
