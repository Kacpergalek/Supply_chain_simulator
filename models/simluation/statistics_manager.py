import numpy as np
import os
import json

from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery

def save_to_json(data, directory, file_name):
    try:
        aggregated_path = os.path.join(directory, f"{file_name}.json")
        with open(aggregated_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Failed to save timeseries to disk: {e}")


class StatisticsManager:
    """ class for managing statistics

        Monitored variables per timestamp (lists index = agent_id)
        --------------------------------------------------------------
            lost_demand (list(int)): number of lost supplies in the current timestamp
            fulfilled_demand (list(int)): number of fulfilled supplies in the current timestamp
            cost (list(float)): total cost of the route in the current timestamp
            loss (list(float)): (route cost in the current timestamp) - (previous route cost)

        Snapshot dictionaries for CSV (timeseries dicts per agent: { 'Agent 0': { '<time>': value, ... }, ... }):
        --------------------------------------------------------------
            fulfilled_demand (dict): {agent_id: value}
            lost_demand (dict): {agent_id: value}
            cost (dict): {agent_id: value}
            loss (dict): {agent_id: value}

        Aggregated values for JSON - sums up all disrupted agents per timestamp (list index = timestamp):
        --------------------------------------------------------------
            avg_fulfilled_demand (list(int)): average fulfilled demand
            avg_lost_demand (list(int)): average lost demand
            avg_cost (list(float)): average cost
            avg_loss (list(float)): average loss
            ==========================================================================
            sum_fulfilled_demand (list(int)): total fulfilled demand
            sum_lost_demand (list(int)): total lost demand
            sum_cost (list(float)): total cost
            sum_loss (list(float)): total loss

        Final snapshot for JSON per agent (lists index = agent_id)
        --------------------------------------------------------------
        final_snapshot : dict
        Mapping:
        "Agent <id>" -> {
            "final_fulfilled_demand": float,
            "final_lost_demand": float,
            "final_cost": float,
            "final_loss": float
        }
    """

    def __init__(self, number_of_agents: int, max_time: int):
        self.number_of_agents = number_of_agents
        self.max_time = max_time + 1
        self.total_routes = 0
        self.changed_routes = 0

        """ REFRESHES EVERY TIMESTAMP """
        self.lost_demand = np.zeros(number_of_agents)
        self.fulfilled_demand = np.zeros(number_of_agents)
        self.cost = np.zeros(number_of_agents)
        self.loss = np.zeros(number_of_agents)
        self.lead_time = np.zeros(number_of_agents)

        """ SAVES EVERY TIMESTAMP """
        self.fulfilled_timeseries = {f"Agent {i}": {} for i in range(number_of_agents)}
        self.lost_timeseries = {f"Agent {i}": {}for i in range(number_of_agents)}
        self.cost_timeseries = {f"Agent {i}": {}for i in range(number_of_agents)}
        self.loss_timeseries = {f"Agent {i}": {}for i in range(number_of_agents)}
        self.lead_time_timeseries = {f"Agent {i}": {} for i in range(number_of_agents)}

        """ AGGREGATED STATS AFTER COMPLETION"""
        self.avg_fulfilled_demand = np.zeros(self.max_time)
        self.avg_lost_demand = np.zeros(self.max_time)
        self.avg_cost = np.zeros(self.max_time)
        self.avg_loss = np.zeros(self.max_time)
        self.avg_lead_time = np.zeros(self.max_time)

        self.sum_fulfilled_demand = np.zeros(self.max_time)
        self.sum_lost_demand = np.zeros(self.max_time)
        self.sum_cost = np.zeros(self.max_time)
        self.sum_loss = np.zeros(self.max_time)
        self.sum_lead_time = np.zeros(self.max_time)

        """ FINAL SNAPSHOT"""
        self.final_snapshot = {f"Agent {i}": {} for i in range(number_of_agents)}

    def update_fulfilled_demand(self, exporter: ExporterAgent, disruption: bool) -> None:
        if disruption:
            self.fulfilled_demand[exporter.agent_id] = 0
        else:
            self.fulfilled_demand[exporter.agent_id] = exporter.unit_demand

    def update_lost_demand(self, deliveries: list[Delivery], node_to_exporter: dict[int, ExporterAgent],
                           disrupted: bool = False) -> None:
        if disrupted:
            for delivery in deliveries:
                agent = node_to_exporter[delivery.start_node_id]
                self.lost_demand[agent.agent_id] = agent.unit_demand
        else:
            for delivery in deliveries:
                agent = node_to_exporter[delivery.start_node_id]
                self.lost_demand[agent.agent_id] = 0

    def update_cost(self, deliveries: list[Delivery], node_to_exporter: dict[int, ExporterAgent]) -> None:
        for delivery in deliveries:
            agent = node_to_exporter[delivery.start_node_id]
            self.cost[agent.agent_id] = delivery.cost

    def update_loss(self, deliveries: list[Delivery], node_to_exporter: dict[int, ExporterAgent],
                    old_cost: list[float]) -> None:
        for i, delivery in enumerate(deliveries):
            agent = node_to_exporter[delivery.start_node_id]
            if len(old_cost) == 0:
                self.loss[agent.agent_id] = 0
            else:
                self.loss[agent.agent_id] = delivery.cost - old_cost[i]

    def update_lead_time(self, deliveries: list[Delivery], node_to_exporter: dict[int, ExporterAgent]) -> None:
        """
        Update per-agent lead time, analogical to update_cost.
        """
        for delivery in deliveries:
            agent = node_to_exporter[delivery.start_node_id]
            self.lead_time[agent.agent_id] = delivery.lead_time

    def add_snapshot(self, current_time: int):
        """
        Capture the current per-agent statistics at a given timestamp.

        Parameters
        ----------
        current_time : int
            Current simulation time step (index into time series arrays).

        Side Effects
        ------------
        - Updates per-agent time series dictionaries.
        - Updates per-timestamp sum arrays.
        """
        time_key = str(int(current_time))
        for i in range(self.number_of_agents):
            agent_key = f"Agent {i}"
            self.fulfilled_timeseries[agent_key][time_key] = round(float(self.fulfilled_demand[i]), 2)
            self.lost_timeseries[agent_key][time_key] = round(float(self.lost_demand[i]), 2)
            self.cost_timeseries[agent_key][time_key] = round(float(self.cost[i]), 2)
            self.loss_timeseries[agent_key][time_key] = round(float(self.loss[i]), 2)
            self.lead_time_timeseries[agent_key][time_key] = round(float(self.lead_time[i]), 2)

            self.sum_fulfilled_demand[current_time] += self.fulfilled_demand[i]
            self.sum_lost_demand[current_time] += self.lost_demand[i]
            self.sum_cost[current_time] += self.cost[i]
            self.sum_loss[current_time] += self.loss[i]
            self.sum_lead_time[current_time] += self.lead_time[i]


    def create_final_snapshot(self):
        """ Create a final snapshot for every agent
            The snapshot consists of the sum of all values in the timeseries for that agent
            self.final_snapshot saves final snapshots for every agent

            Method is called after the simulation is completed"""
        for i in range(self.number_of_agents):
            final_snapshot = {
                'final_fulfilled_demand': round(sum(self.fulfilled_timeseries[f"Agent {i}"].values()), 2),
                'final_lost_demand': round(sum(self.lost_timeseries[f"Agent {i}"].values()), 2),
                'final_cost': round(sum(self.cost_timeseries[f"Agent {i}"].values()), 2),
                'final_loss': round(sum(self.loss_timeseries[f"Agent {i}"].values()), 2),
                'final_lead_time': round(sum(self.lead_time_timeseries[f"Agent {i}"].values()), 2),
            }
            self.final_snapshot[f"Agent {i}"].update(final_snapshot)


    def aggregate_snapshots(self):
        """ Calculate the average of all snapshots for every timestamp
        Method is called after the simulation is completed"""
        for t in range(self.max_time):
            self.avg_fulfilled_demand[t] = self.sum_fulfilled_demand[t]/self.number_of_agents
            self.avg_lost_demand[t] = self.sum_lost_demand[t]/self.number_of_agents
            self.avg_cost[t] = self.sum_cost[t]/self.number_of_agents
            self.avg_loss[t] = self.sum_loss[t]/self.number_of_agents
            self.avg_lead_time[t] = self.sum_lead_time[t] / self.number_of_agents

    def save_statistics(self):
        """
        - Build final per-agent snapshot.
        - Compute aggregated averages and sums across agents.
        - Write:
            * average_<metric>.json
            * sum_<metric>.json
            * final_snapshot.json
            * per-agent time series JSON files
          into the `output_data` directory.
        """
        self.create_final_snapshot()
        self.aggregate_snapshots()

        average_data = {
            'avg_fulfilled_demand': self.avg_fulfilled_demand.tolist()[1:],
            'avg_lost_demand': self.avg_lost_demand.tolist()[1:],
            'avg_cost': self.avg_cost.tolist()[1:],
            'avg_loss': self.avg_loss.tolist()[1:],
            'avg_lead_time': self.avg_lead_time.tolist()[1:],
        }

        sum_data = {
            'sum_fulfilled_demand': self.sum_fulfilled_demand.tolist()[1:],
            'sum_lost_demand': self.sum_lost_demand.tolist()[1:],
            'sum_cost': self.sum_cost.tolist()[1:],
            'sum_loss': self.sum_loss.tolist()[1:],
            'sum_lead_time': self.sum_lead_time.tolist()[1:],
        }

        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        directory = os.path.join(path, 'data', 'output_data')
        os.makedirs(directory, exist_ok=True)

        save_to_json(average_data, directory, 'average')
        save_to_json(sum_data, directory, 'sum')
        save_to_json(self.final_snapshot, directory, 'final_snapshot')
        save_to_json(self.fulfilled_timeseries, directory, 'fulfilled_timeseries')
        save_to_json(self.lost_timeseries, directory, 'lost_timeseries')
        save_to_json(self.cost_timeseries, directory, 'cost_timeseries')
        save_to_json(self.loss_timeseries, directory, 'loss_timeseries')
        save_to_json(self.lead_time_timeseries, directory, 'lead_time_timeseries')