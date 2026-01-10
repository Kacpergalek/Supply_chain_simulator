import copy
import random
import networkx as nx
import json

from pathlib import Path
from collections import Counter, deque
from networkx.classes import MultiGraph


def get_edge_cost(u, v, d, prices):
    mode = "land"  # Default
    if d.get("mode") in ["air", "flight"] or "aeroway" in d:
        mode = "air"
    elif d.get("mode") in ["sea", "shipping"] or d.get("route") == "ferry":
        mode = "sea"

    if mode == "air":
        unit_cost = prices.get("price_per_km_air", 5.0)
    elif mode == "sea":
        unit_cost = prices.get("price_per_km_sea", 0.5)
    else:
        unit_cost = prices.get("price_per_km_land", 1.0)

    return d.get('cost', unit_cost)

# def radius_search(graph: MultiGraph, center_node: int, radius_meters: float):
#     sub = nx.ego_graph(nx.MultiGraph(graph), center_node, radius=radius_meters, distance='length')
#     return list(sub.nodes)

def find_nodes_to_disrupt(graph, deliveries, max_depth):
    """
    Finds nodes that can be disrupted within a PHYSICAL RADIUS (km)
    without breaking connectivity for any delivery.
    """

    prices = {
        "price_per_km_land": 1.0,
        "price_per_km_air": 5.0,
        "price_per_km_sea": 0.5
    }

    route_nodes = []
    for delivery in deliveries:
        if delivery.route:
            route_nodes.extend(delivery.route)

    if not route_nodes:
        print("⚠️ No routes found.")
        return

    frequency = Counter(route_nodes)
    node_scores = {}
    for n in frequency:
        if n in graph:
            node_scores[n] = frequency[n] * 0.8 + graph.degree(n) * 0.2

    important_nodes = sorted(node_scores, key=node_scores.get, reverse=True)[:10]

    delivery_endpoints = {d.start_node_id for d in deliveries} | {d.end_node_id for d in deliveries}

    def path_weight(u, v, d):
        return get_edge_cost(u, v, d, prices)

    def is_disruption_safe(center_node):
        try:
            region = bfs_limited(graph, center_node, max_depth=max_depth)
        except Exception:
            region = [center_node]

        nodes_to_deactivate = [n for n in region if n not in delivery_endpoints]

        if not nodes_to_deactivate:
            return False

        graph_copy = copy.deepcopy(graph)

        if hasattr(graph_copy, "deactivate_nodes"):
            graph_copy.deactivate_nodes(nodes_to_deactivate)
        else:
            for n in nodes_to_deactivate:
                if n in graph_copy.nodes:
                    graph_copy.nodes[n]["active"] = False

        if hasattr(graph_copy, "get_active_graph"):
            active_graph = graph_copy.get_active_graph()
        else:
            active_nodes = [n for n, d in graph_copy.nodes(data=True) if d.get("active", True)]
            active_graph = graph_copy.subgraph(active_nodes)

        for d in deliveries:
            s, t = d.start_node_id, d.end_node_id
            if s not in active_graph or t not in active_graph:
                return False
            try:
                nx.shortest_path(active_graph, s, t, weight=path_weight)
            except nx.NetworkXNoPath:
                return False

        return True

    print(f"Checking candidates with {max_depth} radius...")
    safe_centers = []
    for n in important_nodes:
        if is_disruption_safe(n):
            safe_centers.append(n)

    path = Path(__file__).parent.parent
    output_path = path / "input_data" / "form_data" / "place_of_disruption.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(safe_centers, f, indent=4)


def bfs_limited(graph, start, max_depth):
    visited = set()
    try:
        if start not in graph:
            print(f"bfs_limited: start node {start} is not in the graph")
            return visited
    except Exception:
        pass

    queue = deque([(start, 0)])

    while queue:
        vertex, depth = queue.popleft()
        if vertex in visited:
            continue
        try:
            if vertex not in graph:
                continue
        except Exception:
            pass

        visited.add(vertex)

        if depth < max_depth:
            try:
                for neighbor in graph.neighbors(vertex):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
            except Exception:
                continue

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

    path = Path(__file__).parent.parent
    output_path = path / "form_data" / "place_of_disruption.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(disruption_nodes, f, indent=4)