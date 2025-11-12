import pickle
import time
import logging
from pathlib import Path
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))
from network.visualization import plot_agent_routes


from models.agents import ExporterAgent, BaseAgent
from models.delivery.delivery import Delivery
from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager
from network.graph_reader import GraphManager

from utils.find_delivery import find_delivery_by_agent
from utils.find_exporter import  find_exporter_by_node_id

from network.simulation_graph import SimulationGraph
from network.agents_initiation import initiation

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self, max_time: int, time_resolution: str):
        self.current_time = 0
        self.max_time = max_time
        self.exporters = []
        self.importers = []
        self.deliveries = []

        self.time_manager = TimeManager(time_resolution)
        self.statistics_manager = StatisticsManager()

        """ Network initialization"""
        graph_manager = GraphManager()
        graph = graph_manager.load_pickle_graph("poland_motorway_trunk_primary.pkl")
        self.network = SimulationGraph(default_capacity=graph.default_capacity,
                                           default_price=graph.default_price,
                                           incoming_graph_data=graph)

        """ Agents initialization """
        self.agent_paths = initiation(self.network)

        """ Disruption initialization """
        path = Path(__file__).parent.parent.parent
        with open(f"{path}/parameters/disruption_parameters.pkl", 'rb') as f:
            self.disruption = pickle.load(f)

    def run(self):

        print("Starting simulation")
        time.sleep(2)

        try:
            self.initialize()

            while self.should_continue():
                self.execute_time_step()
                self.statistics_manager.add_dataframe(current_time=self.current_time)
                self.current_time += 1
                print(self.exporters)
                time.sleep(5)

            self.finalize()

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            print(f"Simulation completed after {self.current_time} time steps")
            self.statistics_manager.save_to_csv()


    def initialize(self):

        for i in range(len(self.agent_paths)):
            exporter = ExporterAgent(i, self.agent_paths[i]['exporter_node'])
            self.exporters.append(exporter)
        for i in range(len(self.agent_paths)):
            importer = BaseAgent(i + 10, self.agent_paths[i]['importer_node'])
            self.importers.append(importer)
        for i in range(len(self.agent_paths)):
            delivery = Delivery(i, self.exporters[i].node_id, self.importers[i].node_id, self.agent_paths[i]['path'])
            self.deliveries.append(delivery)

        self.statistics_manager.define_total_routes(len(self.agent_paths))
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.define_cost(exporter.agent_id, cost)
        
        self.save_current_map()

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self):
        """ Saving statistics to a csv file and displaying a KPI panel"""
        self.statistics_manager.calculate_loss()
        self.statistics_manager.save_to_csv()
        self.statistics_manager.show_kpi_panel()
    
    def save_current_map(self, filename="latest_map.png"):
        """Zapisuje aktualny stan sieci i tras do pliku PNG."""
        try:
            routes = [d.route for d in self.deliveries]
            exporter_nodes = [e.node_id for e in self.exporters]
            importer_nodes = [i.node_id for i in self.importers]
            disrupted_nodes = [
                n for n in self.network.nodes if hasattr(n, "active") and not n.active
            ]

            #save_path = Path(__file__).parent.parent.parent / "assets/maps" / filename
            plot_agent_routes(
                self.network,
                routes,
                exporter_nodes,
                importer_nodes,
                disrupted_nodes,
            )
            print(f"✅ Mapa zapisana")
        except Exception as e:
            print(f"❌ Błąd podczas zapisu mapy: {e}")

    def execute_time_step(self):

        t = self.current_time
        print(f"Executing time step {t}")

        # TODO exporters need to pay according to the path cost, not only the production fee

        """ Start a disruption """
        if self.disruption['dayOfStart'] == t:
            places_of_disruption = [node for node in self.network.nodes if node == self.disruption['placeOfDisruption']]
            self.network.deactivate_nodes(places_of_disruption)
            self.find_disrupted_routes()
            self.update_disrupted_routes()
            # self.statistics_manager.add_dataframe(option="b", current_time=self.current_time)
            print(f"Disruption started at {t}\n{self.disruption}")
            
            self.save_current_map("during_disruption.png")

        """ End a disruption"""
        if self.disruption['dayOfStart'] + self.disruption['duration'] == t:
            places_of_disruption = [node for node in self.network.nodes if node == self.disruption['placeOfDisruption']]
            self.network.activate_nodes(places_of_disruption)
            self.default_routes()
            # self.statistics_manager.add_dataframe(option="a", current_time=self.current_time)
            print("Disruption ended")
            self.save_current_map("after_disruption.png")

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
                delivery = find_delivery_by_agent(self.deliveries, exporter)
                lost_demand = delivery.lead_time * exporter.quantity * (exporter.price*0.75)
                self.statistics_manager.update_lost_demand(exporter.agent_id, lost_demand)


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


if __name__ == "__main__":
    # graph_manager = GraphManager()
    # graph = graph_manager.load_pickle_graph("poland_motorway_trunk_primary.pkl")
    simulation = Simulation(max_time= 3, time_resolution="day")
    simulation.run()