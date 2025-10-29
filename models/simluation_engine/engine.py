import pickle

# from IPython.core.events import EventManager
# from pandas.core.internals import DataManager

from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager
import logging
logger = logging.getLogger(__name__)


class Simulation:
    def __init__(self, model, max_time, time_resolution, network, agents):
        self.model = model
        self.current_time = 0
        self.max_time = max_time
        self.time_resolution = time_resolution
        self.network = network
        self.agents = agents
        self.disruption = {}

        # Core managers
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
            pass
            # self.performance_monitor.stop()
            # logger.info(f"Simulation completed in {self.performance_monitor.elapsed_time:.2f} seconds")

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
        pass

    def should_continue(self) -> bool:

        if self.current_time >= self.max_time:
            return False

        return True

    def finalize(self):
        # 1) save simulation results
        self.statistics_manager.calculate_loss()
        df = self.statistics_manager.create_dataframe()
        self.statistics_manager.save_to_csv(df)
        # 2) KPI panel
        self.statistics_manager.show_kpi_panel()
        pass

    def execute_time_step(self):

        t = self.current_time
        logger.debug(f"Executing time step {t}")

        if self.disruption['dayOfStart'] == t:
            self.execute_disruption()
            self.find_disrupted_routes()
            self.update_agents()
        if self.disruption['dayOfStart'] + self.disruption['numberOfDays'] == t:
            self.complete_disruption()
            self.update_agents()

        #TODO
        # 1) if no disruption - update fulfilled demand to the stat manager
        # 2) if there is a disruption - update lost demand to the stat manager
        pass

    def execute_disruption(self):
        #TODO
        # 1) iterate through nodes from self.network
        # if node_id == self.disruption['placeOfDisruption'] then disable the node
        pass

    def find_disrupted_routes(self):
        #TODO
        # 1) iterate through all routes
        # if at least 1 node or edge is disabled mark the starting node (exporter agent)
        # 2) update changed_routed in the stat manager
        pass

    def update_agents(self):
        for agent in self.agents:
            #TODO
            # 1) if an exporter agent is marked
            # search for the next cheapest route
            continue
        pass

    def complete_disruption(self):
        #TODO
        # 1) iterate through nodes from self.network
        # enable all disabled nodes
        pass