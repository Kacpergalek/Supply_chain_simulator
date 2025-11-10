import json
from pathlib import Path


def find_nodes_to_disrupt(graph):
    #TODO find reasonable nodes to disrupt
    i = 0
    nodes_for_disruption = []
    for node in graph.nodes:
        nodes_for_disruption.append(node)
        i += 1
        if i > 10:
            break

    path = Path(__file__).parent.parent
    print(f"Path: {path}\\form_data\\place_of_disruption.json")
    with open(f'{path}\\form_data\\place_of_disruption.json', 'w') as f:
        json.dump(nodes_for_disruption, f, indent=4)