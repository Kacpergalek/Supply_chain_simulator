import json
from pathlib import Path
from collections import Counter
from collections import deque
import random


def find_nodes_to_disrupt(graph, deliveries, max_depth=20):
    """
    Wybiera sensowne węzły do zakłóceń:
      - są częścią tras (delivery.route)
      - pojawiają się często w różnych trasach (duże znaczenie)
      - mają wysoki degree w grafie (dużo połączeń)
    """
    # 1️⃣ Zbierz wszystkie węzły z tras
    route_nodes = []
    for delivery in deliveries:
        if delivery.route:
            route_nodes.extend(delivery.route)

    if not route_nodes:
        print("⚠️ Brak tras w dostawach — nie można wybrać węzłów do zakłóceń.")
        return

    # 2️⃣ Policz częstość występowania każdego węzła w trasach
    frequency = Counter(route_nodes)

    # 3️⃣ Policz degree (liczbę połączeń) każdego węzła
    node_degrees = {n: graph.degree(n) for n in route_nodes}

    # 4️⃣ Połącz wagę: częstość + połączenia → sortuj malejąco
    node_scores = {
        n: frequency[n] * 0.7 + node_degrees.get(n, 0) * 0.3
        for n in route_nodes
    }

    # 5️⃣ Wybierz 10 najważniejszych węzłów
    important_nodes = sorted(node_scores, key=node_scores.get, reverse=True)[:10]
    # disruption_nodes = set()
    # for node in important_nodes:
    #     disruption_nodes.update(bfs_limited(graph, node, max_depth=max_depth)) 
    # disruption_nodes = list(disruption_nodes)

    # 6️⃣ Zapisz do JSON (dla formularza)
    path = Path(__file__).parent.parent
    output_path = path / "form_data" / "place_of_disruption.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(important_nodes, f, indent=4)

    print(f"✅ Zapisano {len(important_nodes)} węzłów do zakłóceń w {output_path}")
    # print(f"🔹 Najważniejsze węzły: {disruption_nodes}")



def bfs_limited(graph, start, max_depth):
    visited = set()
    queue = deque([(start, 0)])

    while queue:
        vertex, depth = queue.popleft()
        if vertex not in visited:
            # print(f"{vertex} (poziom {depth})")
            visited.add(vertex)

            if depth < max_depth:
                for neighbor in graph.neighbors(vertex):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
    visited.add(start)
    return visited


def find_random_nodes_to_disrupt(graph, max_depth=20):
    nodes = list(graph.nodes())
    rand_nodes = []
    for i in range(10):
        rand_index = random.randint(0, len(nodes) - 1)
        rand_nodes.append(nodes[rand_index])
    disruption_nodes = set()
    for node in rand_nodes:
        disruption_nodes.update(bfs_limited(graph, node, max_depth=max_depth)) 
    disruption_nodes = list(disruption_nodes)

    # 6️⃣ Zapisz do JSON (dla formularza)
    path = Path(__file__).parent.parent
    output_path = path / "form_data" / "place_of_disruption.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(disruption_nodes, f, indent=4)

    print(f"✅ Zapisano {len(disruption_nodes)} węzłów do zakłóceń w {output_path}")
