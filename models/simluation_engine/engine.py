import pickle

from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager
import logging

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self, model, max_time, time_resolution, network, agents):
        # TODO clean up the initialization and check for name collisions
        self.model = model
        self.current_time = 0
        self.max_time = max_time
        self.time_resolution = time_resolution
        self.network = network
        self.exporters = [agent for agent in agents if agent.type == 'exporter']
        self.distributors = [agent for agent in agents if agent.type == 'distributor']
        self.disruption = {}

        self.time_manager = TimeManager(time_resolution)
        self.statistics_manager = StatisticsManager()
        pass

    def run(self):

        logger.info("Starting simulation")

        try:
            self.initialize()

            while self.should_continue():
                self.execute_time_step()
                self.current_time += 1

            self.finalize()

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            logger.info(f"Simulation completed after {self.current_time} time steps")

    def initialize(self):
        #TODO
        # 1) load OSM data
        # 2) initialize network
        # 3) initialize delivery routes
        # 4) initialize agents
        # 5) collect simulation parameters
        with open('../parameters/disruption_parameters.pkl', 'rb') as f:
            self.disruption = pickle.load(f)
        #TODO
        # 6) add initial data to statistics_manager
        #TODO
        routes = []
        self.statistics_manager.total_routes = len(routes)
        for company in self.exporters:
            #TODO
            cost = 0
            self.statistics_manager.define_cost(company.agent_id, cost)
        pass

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
        pass

    def execute_time_step(self):

        t = self.current_time
        logger.debug(f"Executing time step {t}")

        """ Start a disruption """
        if self.disruption['dayOfStart'] == t:
            self.execute_disruption()
            self.find_disrupted_routes()
            self.update_agents()

        """ End a disruption"""
        if self.disruption['dayOfStart'] + self.disruption['numberOfDays'] == t:
            self.end_disruption()
            self.update_agents()
            # TODO
            changed_routes = []
            self.statistics_manager.changed_routes = len(changed_routes)
            for company in self.exporters:
                # TODO
                cost = 0
                self.statistics_manager.define_cost_after_disruption(company.agent_id, cost)

        """ What happens regardless of a disruption"""
        for company in self.exporters:
            # TODO company.produce() + company.sell() ???
            pass

        """ What happens when there is no disruption"""
        if t < self.disruption['dayOfStart'] or t > self.disruption['dayOfStart'] + self.disruption['numberOfDays']:
            for company in self.exporters:
                # TODO capacity
                fulfilled_demand = 0
                self.statistics_manager.update_lost_demand(company.agent_id, fulfilled_demand)

        """ What happens during a disruption"""
        if self.disruption['dayOfStart'] <= t <= self.disruption['dayOfStart'] + self.disruption['numberOfDays']:
            for company in self.exporters:
                # TODO capacity
                lost_demand = 0
                self.statistics_manager.update_lost_demand(company.agent_id, lost_demand)
        pass

    def execute_disruption(self):
        """ Disabling the node or the edge where disruption happens"""
        #TODO check for name collisions
        for node in self.network.nodes:
            if node.node_id == self.disruption['placeOfDisruption']:
                node.active = False
        for edge in self.network.edges:
            if edge.edge_id == self.disruption['placeOfDisruption']:
                edge.active = False
        pass

    def find_disrupted_routes(self):
        #TODO
        # 1) iterate through all routes
        # if at least 1 node or edge is disabled mark the starting node (exporter agent)
        # 2) update changed_routed in the stat manager
        pass

    def update_agents(self):
        for exporter in self.exporters:
            #TODO
            # 1) if an exporter agent is marked
            # search for the next cheapest route
            continue
        pass

    def end_disruption(self):
        """ Enabling all disabled nodes and edges"""
        #TODO check for name collisions
        for node in self.network.nodes:
            if not node.active:
                node.active = True
        for edge in self.network.edges:
            if not edge.active:
                edge.active = True
        pass
