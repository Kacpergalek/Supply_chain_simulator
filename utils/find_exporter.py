from models.agents import ExporterAgent


def find_exporter_by_node_id(agents: list[ExporterAgent], node_id: int) -> ExporterAgent | None:
    for agent in agents:
        if agent.node_id == node_id:
            return agent
    return None


def find_exporter_by_id(agents: list[ExporterAgent], agent_id: int) -> ExporterAgent | None:
    for agent in agents:
        if agent.agent_id == agent_id:
            return agent
    return None