import pickle
import time
import logging
import random
import sys 
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from utils.find_nodes_to_disrupt import bfs_limited

from models.agents.base_agent import BaseAgent
from models.agents.exporter_agent import ExporterAgent
from models.delivery.delivery import Delivery
from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager

from utils.find_delivery import find_delivery_by_agent
from utils.find_exporter import  find_exporter_by_node_id

from network.simulation_graph import SimulationGraph
from network.agents_initiation import initiation
from network.visualization import plot_agent_routes
from network.graph_reader import GraphManager

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
        time.sleep(1)

        try:
            self.initialize()

            while self.should_continue():
                self.current_time += 1
                self.display_info()
                self.execute_time_step()
                self.statistics_manager.add_dataframe(current_time=self.current_time)
                time.sleep(1)

            self.finalize()

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            print(f"Simulation completed after {self.current_time} time steps")


    def initialize(self):

        for i in range(len(self.agent_paths)):
            delivery = Delivery(i, self.agent_paths[i]['exporter_node'], self.agent_paths[i]['importer_node'],
                                self.agent_paths[i]['path'], self.agent_paths[i]['total_distance_km'],
                                self.agent_paths[i]['estimated_cost'], self.agent_paths[i]['estimated_lead_time_days'])
            delivery.capacity = delivery.find_minimum_capacity(self.network)
            self.deliveries.append(delivery)

        for i in range(len(self.agent_paths)):
            delivery = self.deliveries[i]
            finances = random.randrange(1000, 5000)
            quantity = random.randrange(int(delivery.capacity*0.4), delivery.capacity)
            price = random.randrange(int(delivery.cost / delivery.lead_time / quantity),
                                     int(delivery.cost / delivery.lead_time / delivery.capacity * 100))

            exporter = ExporterAgent(agent_id=i, node_id=self.agent_paths[i]['exporter_node'],
                                     quantity=quantity, price=price, finances=finances)
            self.exporters.append(exporter)
        for i in range(len(self.agent_paths)):
            importer = BaseAgent(i + 10, self.agent_paths[i]['importer_node'])
            self.importers.append(importer)

        self.statistics_manager.define_total_routes(len(self.agent_paths))
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.define_cost(exporter.agent_id, cost)
            #TODO
        #NOWE: wywolanie funkcji ktora szuka najlepszych wezlow do disruption i zapisuje w json i zapisanie wersji mapy na samym poczatku bez zadnych zaklocen
        #find_nodes_to_disrupt(self.network, self.deliveries)
        self.save_current_map()
        time.sleep(2)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self):
        """ Saving statistics to a csv file and displaying a KPI panel"""
        self.statistics_manager.create_final_snapshot()
        self.statistics_manager.save_statistics()

    def save_current_map(self, filename="latest_map.png", disrupted_nodes =None):
        """Zapisuje aktualny stan sieci i tras do pliku PNG."""
        try:
            routes = [d.route for d in self.deliveries]
            exporter_nodes = [e.node_id for e in self.exporters]
            importer_nodes = [i.node_id for i in self.importers]
            #disrupted_nodes = [int(self.disruption["placeOfDisruption"])]


            #save_path = Path(__file__).parent.parent.parent / "assets/maps" / filename
            plot_agent_routes(
                self.network,
                routes,
                exporter_nodes,
                importer_nodes,
                disrupted_nodes = disrupted_nodes,
            )
            # print(f"✅ Mapa zapisana")
        except Exception as e:
            print(f"❌ Błąd podczas zapisu mapy: {e}")

    def execute_time_step(self):

        t = self.current_time
        print(f" =========== Executing time step {t} ===========")

        """ Start a disruption """
        if int(self.disruption['dayOfStart']) == t:
            disruption_place = int(self.disruption["placeOfDisruption"])
            places_of_disruption = bfs_limited(self.network, disruption_place, max_depth=20)
            self.network.deactivate_nodes(places_of_disruption)
            self.find_disrupted_routes()
            self.update_disrupted_routes()
            self.update_lost_demand()
            self.save_current_map(disrupted_nodes=[int(self.disruption["placeOfDisruption"])])
            time.sleep(2)

        """ End a disruption"""
        if int(self.disruption['dayOfStart']) + int(self.disruption['duration']) == t:
            disruption_place = int(self.disruption["placeOfDisruption"])
            places_of_disruption = bfs_limited(self.network, disruption_place, max_depth=20)
            self.network.activate_nodes(places_of_disruption)
            self.default_routes()
            self.save_current_map()
            time.sleep(2)

        """ What happens regardless of a disruption"""
        for exporter in self.exporters:
            #TODO
            """ Updating finances """
            exporter.produce()
            exporter.sell(exporter.quantity)
            delivery = find_delivery_by_agent(self.deliveries, exporter)
            exporter.finances -= delivery.cost / delivery.lead_time

            """ Updating fulfilled demand """
            delivery = find_delivery_by_agent(self.deliveries, exporter)
            fulfilled_demand = int(exporter.quantity / delivery.lead_time)
            self.statistics_manager.update_fulfilled_demand(exporter.agent_id, fulfilled_demand)
            pass

        # """ What happens when there is no disruption"""
        # if t < int(self.disruption['dayOfStart']) or t > int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
        #     for exporter in self.exporters:
        #         delivery = find_delivery_by_agent(self.deliveries, exporter)
        #         fulfilled_demand = int(exporter.quantity / delivery.lead_time)
        #         self.statistics_manager.update_fulfilled_demand(exporter.agent_id, fulfilled_demand)

        """ What happens during a disruption"""
        if int(self.disruption['dayOfStart']) <= t <= int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            self.statistics_manager.calculate_loss(self.deliveries)
        #     for exporter in self.exporters:
        #         delivery = find_delivery_by_agent(self.deliveries, exporter)
        #         lost_demand = int(exporter.quantity / delivery.lead_time)
        #         self.statistics_manager.update_lost_demand(exporter.agent_id, lost_demand)


    def find_disrupted_routes(self):
        """ Mark all routes that contain disrupted nodes as disrupted"""
        for delivery in self.deliveries:
            for node in delivery.route:
                if not self.network.nodes[node].get('active'):
                    self.statistics_manager.increment_changed_routes()
                    delivery.disrupted = True
                    break

    def update_disrupted_routes(self):
        """ Updating routes, lengths and costs of disrupted deliveries"""
        disrupted_deliveries = [delivery for delivery in self.deliveries if delivery.disrupted]
        for delivery in disrupted_deliveries:
            print(f"Agent affected: {find_exporter_by_node_id(self.exporters, delivery.start_node_id).agent_id}")
            delivery.reset_delivery()
            delivery.update_delivery(self.exporters, self.network)
            agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
            self.statistics_manager.define_cost_after_disruption(agent.agent_id, delivery.cost)

    def update_lost_demand(self):
        for exporter in self.exporters:
            delivery = find_delivery_by_agent(self.deliveries, exporter)
            if delivery.disrupted:
                lost_demand = int(exporter.quantity / delivery.lead_time)
                self.statistics_manager.update_lost_demand(exporter.agent_id, lost_demand)

    def default_routes(self):
        """ Resetting routes and lengths of disrupted deliveries"""
        for delivery in [delivery for delivery in self.deliveries if delivery.disrupted]:
            delivery.disrupted = False
            delivery.reset_delivery()
            delivery.update_delivery(self.exporters, self.network)

    def display_info(self):
        t = self.current_time
        for exporter in self.exporters:
            print(f"Agent {exporter.agent_id}'s finances: {exporter.finances:.2f}")
        if int(self.disruption['dayOfStart']) == t:
                print(f"DISRUPTION OCCURS (time step {t})")
        if int(self.disruption['dayOfStart']) + int(self.disruption['duration']) == t:
                print(f"DISRUPTION ENDS (time step {t})")

# if __name__ == "__main__":
#     # graph_manager = GraphManager()
#     # graph = graph_manager.load_pickle_graph("poland_motorway_trunk_primary.pkl")
#     simulation = Simulation(max_time=15, time_resolution="day")
#     simulation.run()