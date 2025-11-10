import pickle
import time
import logging
from pathlib import Path
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))


from models.agents import ExporterAgent, BaseAgent
from models.delivery.delivery import Delivery
from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager
from network.graph_reader import GraphManager

from utils.find_delivery import find_delivery_by_agent
from utils.find_exporter import  find_exporter_by_node_id

from network.simulation_graph import SimulationGraph

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self, max_time: int, time_resolution: str, network: SimulationGraph):
        self.current_time = 0
        self.max_time = max_time
        self.network = network
        self.exporters = []
        self.importers = []
        self.deliveries = []
        self.disruption = {}

        self.time_manager = TimeManager(time_resolution)
        self.statistics_manager = StatisticsManager()

    def run(self):

        print("Starting simulation")
        time.sleep(2)

        try:
            self.initialize()
            print(f"Simulation initialized\nExporters:\n{self.exporters}\n"
                  f"Importers:\n{self.importers}")
            for delivery in self.deliveries:
                print(f"Delivery {delivery.to_dict()}")

            while self.should_continue():
                self.execute_time_step()
                self.current_time += 1
                time.sleep(5)

            self.finalize()

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            print(f"Simulation completed after {self.current_time} time steps")

    def initialize(self):
        path = Path(__file__).parent.parent.parent

        with open(f"{path}/network_data/paths.pkl", 'rb') as f:
            paths = pickle.load(f)
        for i in range(10):
            exporter = ExporterAgent(i, paths['exporter_node'][int(i)])
            self.exporters.append(exporter)
        for i in range(10):
            importer = BaseAgent(i + 10, paths['importer_node'][int(i)])
            self.importers.append(importer)

        for i in range(10):
            delivery = Delivery(i, self.exporters[i].node_id, self.importers[i].node_id)
            self.deliveries.append(delivery)

        for delivery in self.deliveries:
            delivery.update_delivery(self.exporters, self.network)

        with open(f"{path}/parameters/disruption_parameters.pkl", 'rb') as f:
            self.disruption = pickle.load(f)

        self.statistics_manager.define_total_routes(len(self.deliveries))
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.define_cost(exporter.agent_id, cost)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self):
        """ Saving statistics to a csv file and displaying a KPI panel"""
        self.statistics_manager.calculate_loss()
        self.statistics_manager.save_to_csv()

        self.statistics_manager.show_kpi_panel()

    def execute_time_step(self):

        t = self.current_time
        print(f"Executing time step {t}")

        """ Start a disruption """
        if self.disruption['dayOfStart'] == t:
            self.execute_disruption()
            self.find_disrupted_routes()
            self.update_disrupted_routes()
            print(f"Disruption started at {t}\n{self.disruption}")

        """ End a disruption"""
        if self.disruption['dayOfStart'] + self.disruption['duration'] == t:
            self.end_disruption()
            self.default_routes()
            print("Disruption ended")

        """ What happens regardless of a disruption"""
        for exporter in self.exporters:
            #TODO
            exporter.produce()
            exporter.sell(90)
            pass

        """ What happens when there is no disruption"""
        if t < int(self.disruption['dayOfStart']) or t > int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            for exporter in self.exporters:
                delivery = find_delivery_by_agent(self.deliveries, exporter)
                fulfilled_demand = delivery.capacity
                self.statistics_manager.update_fulfilled_demand(exporter.agent_id, fulfilled_demand)

        """ What happens during a disruption"""
        if int(self.disruption['dayOfStart']) <= t <= int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            for exporter in self.exporters:
                # TODO jak liczymy lost demand
                lost_demand = 0
                # self.statistics_manager.update_lost_demand(exporter.agent_id, lost_demand)

    def execute_disruption(self):
        """ Disabling the node or the edge where disruption happens"""
        for node in self.network.nodes:
            if node == self.disruption['placeOfDisruption']:
                node.active = False

    def find_disrupted_routes(self):
        """ Mark all routes that contain disrupted nodes as disrupted"""
        for delivery in self.deliveries:
            for node in delivery.route:
                if not node.active:
                    self.statistics_manager.increment_changed_routes()
                    delivery.disrupted = True

    def update_disrupted_routes(self):
        """ Updating routes, lengths and costs of disrupted deliveries"""
        disrupted_deliveries = [delivery for delivery in self.deliveries if delivery.disrupted]
        for delivery in disrupted_deliveries:
            delivery.reset_delivery()
            delivery.update_delivery(self.exporters, self.network)
            agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
            self.statistics_manager.define_cost_after_disruption(agent.agent_id, delivery.cost)

    def default_routes(self):
        """ Resetting routes and lengths of disrupted deliveries"""
        for delivery in self.deliveries:
            if delivery.disrupted:
                delivery.disrupted = False
                delivery.reset_delivery()
                delivery.update_delivery(self.exporters, self.network)

    def end_disruption(self):
        """ Enabling all disabled nodes and edges"""
        for node in self.network.nodes:
            if not node.active:
                node.active = True


if __name__ == "__main__":
    graph_manager = GraphManager()
    graph = graph_manager.load_pickle_graph("poland_motorway_trunk_primary.pkl") 
    simulation = Simulation(max_time= 10, time_resolution="day", network=graph)    
    simulation.run()