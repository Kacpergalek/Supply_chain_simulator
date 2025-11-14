from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery


def find_delivery_by_agent(deliveries: list[Delivery], agent: ExporterAgent) -> Delivery | None:
    for delivery in deliveries:
        if delivery.start_node_id == agent.node_id:
            return delivery
    return None