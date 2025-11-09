from models.agents import ExporterAgent
from models.delivery.delivery import Delivery


if __name__ == "__main__":
    deliveries = []
    exporter_agents = []
    graph = []

    #TODO CHANGE AGENTS
    for i in range(10):
        exporter_agents.append(ExporterAgent(i, i, 100, 10.0, 1000.0))

    #TODO CHANGE FINAL NODE
    for exporter, i in exporter_agents, range(len(exporter_agents)):
        deliveries.append(Delivery(i, exporter.agent_id, i))

    for delivery in deliveries:
        agent_id = delivery.start_node_id
        for agent in exporter_agents:
            if agent.agent_id == agent_id:
                path = agent.find_cheapest_path(graph, delivery.end_node_id)
                delivery.route = path['path']
                delivery.length(path['total_distance_km'])
                delivery.cost = path['total_cost']
                break