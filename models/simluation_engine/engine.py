import math
import pickle
import time
import logging
import random
import sys
import os
import json
from pathlib import Path

from models.agents.agent_manager import AgentManager
from models.delivery.delivery import Delivery
from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager

from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt
from utils.find_delivery import find_delivery_by_agent
from utils.find_exporter import find_exporter_by_node_id

from network.visualization import plot_agent_routes
from network.network import NetworkManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))
logger = logging.getLogger(__name__)


class Simulation:
    def __init__(self):
        self.current_time = 0
        self.exporters = []
        self.importers = []
        self.deliveries = []

        """ Network initialization"""
        time_start = time.time()
        network_manager = NetworkManager()
        self.network = network_manager.get_graph_from_file("europe")
        airplane_graph = network_manager.load_airports_graph(default_capacity=10, default_price=1000)
        self.network.compose(airplane_graph)
        print(f"Czas inicjalizowania grafu: {time.time() - time_start}")

        """ Agents initialization """
        self.agent_manager = AgentManager()
        initialized = self.agent_manager.initialize_agents(self.network)
        self.exporters = initialized["exporters"]
        self.importers = initialized["importers"]
        self.agent_paths = initialized["routes"]

        """ Deliveries initialization """
        self.deliveries = self.agent_manager.delivery_manager.initialize_deliveries(self.network, self.exporters,
                                                                                    self.agent_paths)
        """ Time and path initialization """
        self.max_time = 15
        self.time_manager = TimeManager("day")
        self.path = Path(__file__).parent.parent.parent
        # self.inject_parameters()

        """ Disruption parameters """
        full_path = os.path.join(self.path, "input_data", "disruption_parameters.pkl")
        with open(full_path, 'rb') as f:
            self.disruption = pickle.load(f)
        self.start_day = int(self.disruption['dayOfStart'])
        self.end_day = self.start_day + int(self.disruption['duration'])
        self.severity = self.disruption['severity']
        self.disruption_type = self.disruption['disruptionType']
        self.place_of_disruption = int(self.disruption["placeOfDisruption"])
        self.disaster_steps_dict = {}
        self.number_of_phases = 0
        self.phase = 2
        self.depth = 0
        self.interpret_disruption_parameters()
        print(f"Day of start: {self.start_day}, day of end: {self.end_day}, disruption severity: {self.severity}, disruption type: {self.disruption_type}, place of disruption: {self.place_of_disruption}")

        """ Statistics initialization"""
        self.statistics_manager = StatisticsManager(len(self.exporters), max_time=self.max_time)
        self.statistics_manager.total_routes = len(self.agent_paths)
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.cost[exporter.agent_id] = cost

        self.initialize()

    # def inject_parameters(self):
    #     project_path = Path(__file__).parent.parent.parent
    #     full_path = os.path.join(project_path, "input_data", "disruption_parameters.pkl")
    #     with open(full_path, 'rb') as f:
    #         self.disruption = pickle.load(f)
    #     self.statistics_manager = StatisticsManager(len(self.exporters), max_time=self.max_time)
    #     self.statistics_manager.total_routes = len(self.agent_paths)
    #     for exporter in self.exporters:
    #         cost = find_delivery_by_agent(self.deliveries, exporter).cost
    #         self.statistics_manager.cost[exporter.agent_id] = cost

    def run(self) -> None:

        print("Starting simulation")
        time.sleep(1)

        try:
            while self.should_continue():
                self.current_time += 1
                self.display_info()
                self.execute_time_step()
                self.statistics_manager.add_snapshot(current_time=self.current_time)
                time.sleep(1)

            self.finalize()

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise
        finally:
            print(f"Simulation completed after {self.current_time} time steps")

    def initialize(self) -> None:
        for exporter in self.exporters:
            # exporter.delivery = find_delivery_by_agent(self.deliveries, exporter)
            exporter.finances = random.randrange(1000, 5000)

        # find_nodes_to_disrupt(self.network, self.deliveries, 30)
        self.update_cost(self.deliveries)
        self.save_deliveries()
        self.save_current_map()

    def interpret_disruption_parameters(self) -> None:
        if self.severity == "low":
            self.depth = 10
        elif self.severity == "Normal":
            self.depth = 20
        else:
            self.depth = 30

        # if self.disruption_type in ["Geopolitical", "Technical"]:
        #     self.disaster_steps_dict = {
        #         "Phase 1": self.depth,
        #         "Phase 2": self.depth,
        #         "Phase 3": self.depth,
        #         "Phase 4": self.depth
        #     }
        if self.disruption_type == "Natural disaster":
            self.disaster_steps_dict = {
                "Phase 1": self.depth,
                "Phase 2": round(self.depth / 2),
                "Phase 3": round(self.depth / 4),
                "Phase 4": round(self.depth / 8)
            }
            self.number_of_phases = len(self.disaster_steps_dict)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self) -> None:
        self.statistics_manager.save_statistics()

    def execute_time_step(self):

        t = self.current_time
        print(f" =========== Executing time step {t} ===========")

        """ Start a disruption """
        # print(f"Day of start: {self.start_day}, current day: {t}, Are they equal: {self.start_day == t}")
        if self.start_day == t:
            self.handle_disruption_start()

        """ End a disruption"""
        if self.end_day == t and self.disruption_type != "Natural disaster":
            self.handle_disruption_end()
        """ End a disruption gradually """
        if self.end_day <= t <= self.end_day + self.number_of_phases and self.disruption_type == "Natural disaster":
            self.handle_gradual_ending()

        """ What happens regardless of a disruption"""
        self.handle_time_step(t)

        # """ What happens during a disruption"""
        # if self.start_day <= t <= self.end_day:
        #     self.statistics_manager.calculate_loss()

    def handle_disruption_start(self) -> None:
        depth = self.depth
        places_of_disruption = bfs_limited(self.network, self.place_of_disruption, depth)

        exporter_nodes = {e.node_id for e in self.exporters}
        importer_nodes = {i.node_id for i in self.importers}
        nodes_to_deactivate = [n for n in places_of_disruption if n not in exporter_nodes and n not in importer_nodes]
        self.network.deactivate_nodes(nodes_to_deactivate)

        disrupted_deliveries = self.find_disrupted_deliveries()
        self.mark_deliveries_disrupted(disrupted_deliveries, disrupted=True)
        self.update_deliveries(disrupted_deliveries)
        self.update_cost(disrupted_deliveries)
        self.update_lost_demand(disrupted_deliveries, disrupted=True)
        self.reset_parcels(disrupted_deliveries)

        self.save_current_map(nodes_to_deactivate)

    def handle_disruption_end(self) -> None:
        depth = self.depth
        places_of_disruption = bfs_limited(self.network, self.place_of_disruption, max_depth=depth)
        self.network.activate_nodes(places_of_disruption)
        self.save_current_map()

        disrupted_deliveries = [delivery for delivery in self.deliveries if delivery.disrupted]
        self.update_lost_demand(disrupted_deliveries, disrupted=False)
        self.mark_deliveries_disrupted(disrupted_deliveries, disrupted=False)
        self.load_deliveries(disrupted_deliveries)
        self.update_cost(disrupted_deliveries)
        self.reset_parcels(disrupted_deliveries)

    def handle_time_step(self, t: int):
        for exporter in self.exporters:
            """ Updating finances """
            exporter.send_parcel()

            """ Updating fulfilled demand """
            delivery = find_delivery_by_agent(self.deliveries, exporter)
            if self.start_day + delivery.lead_time > t >= self.start_day:
                self.statistics_manager.fulfilled_demand[exporter.agent_id] = 0
            else:
                self.statistics_manager.fulfilled_demand[exporter.agent_id] = exporter.unit_demand

            """ Reset parcel content """
            deliveries_to_reset = self.find_parcels_to_reset()
            self.reset_parcels(deliveries_to_reset)

    def handle_gradual_ending(self):
        """ If disruption type is a natural disaster (after ending the comeback is gradual) """
        if self.phase == 5:
            self.handle_disruption_end()
            return
        previous_depth = self.disaster_steps_dict[f"Phase {self.phase - 1}"]
        previous_deactivated = bfs_limited(self.network, self.place_of_disruption, max_depth=previous_depth)

        current_depth = self.disaster_steps_dict[f"Phase {self.phase}"]
        current_deactivated = bfs_limited(self.network, self.place_of_disruption, max_depth=current_depth)

        self.network.activate_nodes(previous_deactivated - current_deactivated)

        disrupted_deliveries = self.find_disrupted_deliveries()
        new_deliveries = [d for d in self.deliveries if d not in disrupted_deliveries]
        self.mark_deliveries_disrupted(new_deliveries, disrupted=False)
        self.update_lost_demand(disrupted_deliveries, disrupted=False)
        self.load_deliveries(new_deliveries)
        self.update_cost(new_deliveries)
        self.reset_parcels(new_deliveries)

        self.save_current_map(current_deactivated)
        self.phase += 1

    def save_current_map(self, disrupted_nodes=None):
        try:
            routes = [d.route for d in self.deliveries]
            exporter_nodes = [e.node_id for e in self.exporters]
            importer_nodes = [i.node_id for i in self.importers]

            plot_agent_routes(
                self.network,
                routes,
                exporter_nodes,
                importer_nodes,
                disrupted_nodes=disrupted_nodes,
            )
            print("MAP_UPDATE")
        except Exception as e:
            print(f"❌ Błąd podczas zapisu mapy: {e}")

    def find_disrupted_deliveries(self) -> list[Delivery]:
        disrupted_deliveries = []
        for delivery in self.deliveries:
            for node in delivery.route:
                if not self.network.nodes[node].get('active'):
                    self.statistics_manager.changed_routes += 1
                    disrupted_deliveries.append(delivery)
                    break
        return disrupted_deliveries

    def mark_deliveries_disrupted(self, deliveries: list[Delivery], disrupted: bool):
        for delivery in deliveries:
            delivery.disrupted = disrupted

    def update_deliveries(self, deliveries: list[Delivery]):
        """ Update:
            * route
            * capacity
            * length
            * costs
            * lead time
            of disrupted deliveries """
        active_network = self.network.get_active_graph()
        for delivery in deliveries:
            # print(f"Agent affected: {find_exporter_by_node_id(self.exporters, delivery.start_node_id).agent_id}")
            delivery.reset_delivery()
            old_cost = delivery.cost
            delivery.update_delivery(self.exporters, active_network)
            new_cost = delivery.cost
            self.statistics_manager.calculate_loss(self.exporters, delivery, new_cost - old_cost)

    def update_cost(self, deliveries: list[Delivery]):
        for delivery in deliveries:
            agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
            self.statistics_manager.cost[agent.agent_id] = delivery.cost

    def update_lost_demand(self, deliveries: list[Delivery], disrupted: bool = False):
        if disrupted:
            for delivery in deliveries:
                agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
                self.statistics_manager.lost_demand[agent.agent_id] = agent.unit_demand
        else:
            for delivery in deliveries:
                agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
                self.statistics_manager.lost_demand[agent.agent_id] = 0

    def display_info(self):
        t = self.current_time
        for exporter in self.exporters:
            print(f"Agent {exporter.agent_id}'s finances: {exporter.finances:.2f}")
        if int(self.disruption['dayOfStart']) == t:
            print(f"DISRUPTION OCCURS (time step {t})")
        if int(self.disruption['dayOfStart']) + int(self.disruption['duration']) == t:
            print(f"DISRUPTION ENDS (time step {t})")

    def reset(self):
        self.current_time = 0
        self.exporters = []
        self.importers = []
        self.deliveries = []
        self.statistics_manager = StatisticsManager(len(self.exporters), self.max_time)

        self.initialize()

    def save_deliveries(self, folder: str = "delivery", file_name: str = "starting_deliveries.json"):
        data_path = os.path.join(self.path, "input_data/simulation_data")
        folder_path = os.path.join(data_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        full_path = os.path.join(folder_path, file_name)
        with open(full_path, "w", encoding="utf-8") as json_file:
            json.dump([delivery.to_dict() for delivery in self.deliveries], json_file, indent=4, ensure_ascii=False)

    def load_deliveries(self, deliveries: list[Delivery], folder: str = "delivery",
                        file_name: str = "starting_deliveries.json"):
        data_path = os.path.join(self.path, "input_data/simulation_data")
        folder_path = os.path.join(data_path, folder)
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder: {folder_path} does not exist.")

        full_path = os.path.join(folder_path, file_name)
        if not os.path.exists(full_path):
            raise FileExistsError(f"File: {full_path} does not exist.")

        with open(full_path, "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"Json loading error: {str(e)}")
                return

        for object in data:
            try:
                # print(*object)
                # obj_cpy = object.copy()
                # obj_cpy.pop("capacity")
                # delivery = Delivery(**obj_cpy)
                # self.deliveries.append(delivery)
                if self.deliveries[object["delivery_id"]] in deliveries:
                    self.deliveries[object["delivery_id"]].route = object["route"]
                    self.deliveries[object["delivery_id"]].length = object["length"]
                    self.deliveries[object["delivery_id"]].cost = object["cost"]
                    self.deliveries[object["delivery_id"]].lead_time = object["lead_time"]
                    self.deliveries[object["delivery_id"]].disrupted = object["disrupted"]
                    self.deliveries[object["delivery_id"]].find_minimum_capacity(self.network)
                    # print(f"New delivery loaded: {self.deliveries[object["delivery_id"]]}")
            except TypeError as e:
                print(f"Error while deserializing delivery object: {str(e)}")

    def find_parcels_to_reset(self) -> list[Delivery]:
        deliveries_to_reset = []
        for delivery in self.deliveries:
            if self.current_time % math.ceil(delivery.lead_time) == 0:
                deliveries_to_reset.append(delivery)
        return deliveries_to_reset

    def reset_parcels(self, deliveries: list[Delivery]):
        for delivery in deliveries:
            agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
            number_of_products = random.randrange(int(self.agent_paths[agent.agent_id]['total_distance_km'] / 10.0),
                                                  int(self.agent_paths[agent.agent_id]['total_distance_km'] / 5.0))
            new_parcel = self.agent_manager.delivery_manager.initialize_parcel([inv[0] for inv in agent.inventory],
                                                                               number_of_products)
            delivery.parcel = new_parcel

    # def reset_parcel(self, deliveries: list[Delivery]):
    #     for delivery in deliveries:
    #         if self.current_time % math.ceil(delivery.lead_time) == 0:
    #             agent = find_exporter_by_node_id(self.exporters, delivery.start_node_id)
    #             number_of_products = random.randrange(int(self.agent_paths[agent.agent_id]['total_distance_km'] / 10.0),
    #                                                   int(self.agent_paths[agent.agent_id]['total_distance_km'] / 5.0))
    #             new_parcel = self.agent_manager.delivery_manager.initialize_parcel([inv[0] for inv in agent.inventory],
    #                                                                                number_of_products)
    #             delivery.parcel = new_parcel
