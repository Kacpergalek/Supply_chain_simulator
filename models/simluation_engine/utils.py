from models.agents import BaseAgent, ExporterAgent
from models.delivery.delivery import Delivery


def find_delivery_by_agent(deliveries, agent) -> Delivery:
    for delivery in deliveries:
        if delivery.start_node_id == agent.node_id:
            return delivery

def find_exporter_by_node_id(agents, node_id) -> ExporterAgent:
    for agent in agents:
        if agent.node_id == node_id:
            return agent

def find_exporter_by_id(agents, agent_id) -> ExporterAgent:
    for agent in agents:
        if agent.agent_id == agent_id:
            return agent
