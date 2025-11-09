import pickle
import time
from pathlib import Path

from models.agents import ExporterAgent, BaseAgent
from models.delivery.delivery import Delivery
from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager
import logging

from models.simluation_engine.utils import find_delivery_by_agent, find_exporter_by_node_id

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self, max_time, time_resolution, network):
        self.current_time = 0
        self.max_time = max_time
        self.network = network # TODO jak wyciągnąć atrybuty węzła
        self.exporters = []
        self.importers = []
        self.deliveries = []
        self.disruption = {}

        self.time_manager = TimeManager(time_resolution)
        self.statistics_manager = StatisticsManager()
        pass


    def run(self):

        print("Starting simulation")
        time.sleep(2)

        try:
            self.initialize()
            print(f"Simulation initialized\nExporters:\n{self.exporters}\n"
                  f"Importers:\n{self.importers}\nDeliveries:{self.deliveries}")

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
        print(f"Path: {path}")

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
            exporter = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
            path = exporter.find_cheapest_path(self.network, delivery.end_node_id) # TODO nie działa
            delivery.route = path['path']
            delivery.length = path['total_distance_km'] # TODO dodać długości km z każdej krawędzi
            delivery.cost = path['estimated_cost']

        with open(f"{path}/parameters/disruption_parameters.pkl", 'rb') as f:
            self.disruption = pickle.load(f)

        self.statistics_manager.define_total_routes(len(self.deliveries))
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter.agent_id).cost
            self.statistics_manager.define_cost(exporter.agent_id, cost)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self):
        """ Saving statistics to a csv file and displaying a KPI panel"""
        self.statistics_manager.calculate_loss()
        df = self.statistics_manager.create_dataframe()
        self.statistics_manager.save_to_csv(df)

        self.statistics_manager.show_kpi_panel()

    def execute_time_step(self):

        t = self.current_time
        print(f"Executing time step {t}")

        """ Start a disruption """
        if self.disruption['dayOfStart'] == t:
            self.execute_disruption()
            self.find_disrupted_routes()
            print(f"Disruption started at {t}\n{self.disruption}")

        """ End a disruption"""
        if self.disruption['dayOfStart'] + self.disruption['duration'] == t:
            self.end_disruption()
            self.default_routes()
            for company in self.exporters:
                new_path = company.find_cheapest_path(self.network, find_delivery_by_agent(self.deliveries, company).end_node_id)
                self.statistics_manager.define_cost_after_disruption(company.agent_id, new_path['estimated_cost'])
            print("Disruption ended")

        """ What happens regardless of a disruption"""
        for company in self.exporters:
            # TODO company.produce() + company.sell() ???
            pass

        """ What happens when there is no disruption"""
        if t < int(self.disruption['dayOfStart']) or t > int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            for company in self.exporters:
                # TODO capacity skąd wziąć
                fulfilled_demand = 0
                # self.statistics_manager.update_lost_demand(company.agent_id, fulfilled_demand)

        """ What happens during a disruption"""
        if int(self.disruption['dayOfStart']) <= t <= int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            for company in self.exporters:
                # TODO capacity skąz wziąć
                lost_demand = 0
                # self.statistics_manager.update_lost_demand(company.agent_id, lost_demand)

        for agent in self.exporters:
            print(f'{agent.to_dict()}\n')
        print('\n')
        pass

    def execute_disruption(self):
        """ Disabling the node or the edge where disruption happens"""
        for node in self.network.nodes:
            if node == self.disruption['placeOfDisruption']:
                node.active = False
        pass

    def find_disrupted_routes(self):
        for delivery in self.deliveries:
            for node in delivery.route:
                if not node.active:
                    self.statistics_manager.increment_changed_routes()
                    delivery.disrupted = True
                    new_path = delivery.find_cheapest_route()
                    delivery.update_route(new_path['path'], new_path['total_distance_km'], new_path['estimated_cost'])
                    # TODO dodać długości km z każdej krawędzi

    def default_routes(self):
        for delivery in self.deliveries:
            if delivery.disrupted:
                delivery.update_disrupted(False)
                new_path = delivery.find_cheapest_route()
                delivery.update_route(new_path['path'], new_path['total_distance_km'], new_path['estimated_cost'])
                # TODO dodać długości km z każdej krawędzi

    def end_disruption(self):
        """ Enabling all disabled nodes and edges"""
        for node in self.network.nodes:
            if not node.active:
                node.active = True
