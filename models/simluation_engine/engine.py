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

from network.visualization import plot_agent_routes
from network.network import NetworkManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))
logger = logging.getLogger(__name__)


class Simulation:
    """
    - Initialize the transportation network (including airports).
    - Initialize agents (exporters, factories, importers) and their deliveries.
    - Configure and execute disruption scenarios over discrete time steps.
    - Track and persist statistics via `StatisticsManager`.
    - Generate intermediate visualizations of agent routes and disruptions.

    Attributes
    ----------
    current_time : int
        Current simulation time step.
    network : SimulationGraph
        Underlying transportation network (road/air).
    agent_manager : AgentManager
        Manages creation and configuration of agents and routes.
    material_exporters, importer_exporters, product_importers : list
        Agent lists returned by `AgentManager`.
    material_paths, product_paths : list[dict]
        Precomputed path metadata for material and product flows.
    deliveries : list[Delivery]
        Deliveries derived from precomputed paths.
    max_time : int
        Number of discrete time steps to simulate.
    time_manager : TimeManager
        Helper for time granularity (e.g. days).
    path : Path
        Root path of the project (used for data I/O).
    disruption, start_day, end_day, severity, disruption_type, place_of_disruption
        Parameters loaded from `disruption_parameters.pkl`.
    depth, number_of_phases, phase, disaster_steps_dict
        Internal representation of disruption severity and recovery phases.
    statistics_manager : StatisticsManager
        Collects and persists simulation statistics.
    """
    def __init__(self):
        """ Time and path initialization """
        self.disruption = {}
        self.current_time = 0
        self.max_time = 15
        self.time_manager = TimeManager("day")
        self.path = Path(__file__).parent.parent.parent
        # self.inject_parameters()

        """ Network initialization"""
        #time_start = time.time()
        network_manager = NetworkManager()
        # self.network = network_manager.get_graph_from_file("europe")
        # airplane_graph = network_manager.load_airports_graph(default_capacity=10, default_price=7)
        # self.network.compose(airplane_graph)
        # seaport_graph = network_manager.load_seaports_graph(default_capacity=5, default_price=3)
        # self.network.compose(seaport_graph)
        # self.network.connect_airports_seaports(default_capacity=1000, default_price=0.5)
        self.network = network_manager.get_graph_from_file("world", road_type="")
        # print(f"Czas inicjalizowania grafu: {time.time() - time_start}")
        # self.network = network_manager.get_graph_from_file("europe")
        # airplane_graph = network_manager.load_airports_graph(default_capacity=10, default_price=1000)
        # self.network.compose(airplane_graph)
        #print(f"Czas inicjalizowania grafu: {time.time() - time_start}")

        """ Agents initialization """
        self.agent_manager = AgentManager()
        initialized = self.agent_manager.initialize_agents(self.network)
        self.material_exporters = initialized["material_exporters"]
        self.importer_exporters = initialized["importer_exporters"]
        self.product_importers = initialized["product_importers"]
        self.material_paths = initialized["material_routes"]
        self.product_paths = initialized["product_routes"]
        self.node_to_exporter = {int(agent.node_id): agent for agent in self.importer_exporters + self.material_exporters}

        """ Deliveries initialization """
        self.product_deliveries = self.agent_manager.delivery_manager.initialize_deliveries(self.network,
                                                                                        self.node_to_exporter,
                                                                                        self.product_paths, True)
        self.material_deliveries = self.agent_manager.delivery_manager.initialize_deliveries(self.network,
                                                                                        self.node_to_exporter,
                                                                                        self.material_paths, False)
        self.deliveries = []
        for delivery in self.product_deliveries:
            self.deliveries.append(delivery)
        for delivery in self.material_deliveries:
            self.deliveries.append(delivery)
            #print(delivery.to_dict())

        """ Disruption parameters """
        self.load_disruption_parameters()
        self.start_day = int(self.disruption['dayOfStart'])
        self.end_day = self.start_day + int(self.disruption['duration'])
        self.severity = self.disruption['severity']
        self.disruption_type = self.disruption['disruptionType']
        self.place_of_disruption = int(self.disruption["placeOfDisruption"])
        self.disruption_nodes = []
        self.disaster_steps_dict = {}
        self.number_of_phases = 0
        self.phase = 1
        self.depth = 0
        self.interpret_disruption_parameters()

        """ Statistics initialization"""
        self.statistics_manager = StatisticsManager(len(self.importer_exporters), max_time=self.max_time)
        self.statistics_manager.total_routes = len(self.product_paths)
        for exporter in self.importer_exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.cost[exporter.agent_id] = cost

        self.initialize()

    def load_disruption_parameters(self):
        full_path = self.path / "input_data" / "disruption_parameters.pkl"

        if not full_path.exists():
            logger.error(f"Disruption parameters not found at {full_path}")
            raise FileNotFoundError(f"Missing config: {full_path}")

        try:
            with open(full_path, 'rb') as f:
                self.disruption = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load disruption parameters: {e}")
            raise


    def run(self) -> None:
        """
        - Advance time step by step while `should_continue()` is True.
        - Apply disruptions and recovery logic at configured days.
        - Record statistics each time step.
        - Save statistics at the end and print summary information.
        """
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
        """
        - Assign random initial finances to each importer-exporter.
        - Compute and store initial costs for all product deliveries.
        - Save deliveries and an initial route map to disk.
        """
        #find_nodes_to_disrupt(self.network, self.deliveries, 50)
        self.statistics_manager.update_cost(self.product_deliveries, self.node_to_exporter)
        self.save_deliveries()
        self.save_current_map()

    def interpret_disruption_parameters(self) -> None:
        """
        Translate disruption configuration into internal severity parameters.
        depth controls the BFS radius of node deactivation.
        """
        if self.severity == "Low":
            self.depth = 10
        elif self.severity == "Normal":
            self.depth = 25
        else:
            self.depth = 50

        if self.disruption_type == "Natural disaster":
            self.disaster_steps_dict = {
                "phase_1": round(self.depth / 2),
                "phase_2": round(self.depth / 4),
                "phase_3": round(self.depth / 6),
                "phase_4": round(self.depth / 8)
            }
            self.number_of_phases = len(self.disaster_steps_dict)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self) -> None:
        self.statistics_manager.save_statistics()

    def execute_time_step(self) -> None:
        """
        - Start a disruption when `current_time == start_day`.
        - End a disruption or gradually recover from it depending on type.
        - Always invoke `handle_time_step` for per-step demand/parcel logic.
        """
        t = self.current_time
        print(f" =========== Executing time step {t} ===========")
        """ Send first parcel """
        if self.current_time == 1:
            for agent in self.importer_exporters + self.material_exporters:
                agent.send_parcel()

        """ Start a disruption """
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


    def handle_disruption_start(self) -> None:
        places_of_disruption = bfs_limited(self.network, self.place_of_disruption, self.depth)
        deactivated_nodes = self.deactivate_nodes(places_of_disruption)
        deactivated_deliveries = self.find_deactivated_deliveries()
        disrupted_deliveries = self.mark_deliveries_disrupted(deactivated_deliveries, disrupted=True)

        self.update_deliveries(disrupted_deliveries)
        self.reset_parcels(disrupted_deliveries)

        self.save_current_map(self.place_of_disruption)
        print(f"Disruption started at node {self.place_of_disruption}, deactivated nodes: {deactivated_nodes}")
    def deactivate_nodes(self, places_of_disruption: list[int]) -> list[int]:
        exporter_nodes = {e.node_id for e in self.material_exporters}
        importer_exporter_nodes = {ie.node_id for ie in self.importer_exporters}
        importer_nodes = {i.node_id for i in self.product_importers}
        nodes_to_deactivate = [n for n in places_of_disruption if n not in importer_exporter_nodes
                               and n not in importer_nodes and n not in exporter_nodes]
        self.network.deactivate_nodes(nodes_to_deactivate)

        return nodes_to_deactivate

    def handle_disruption_end(self) -> None:
        places_of_disruption = bfs_limited(self.network, self.place_of_disruption, max_depth=self.depth)
        self.network.activate_nodes(places_of_disruption)

        deliveries_to_fix = [delivery for delivery in self.deliveries if delivery.disrupted]
        product_deliveries_to_fix = [d for d in deliveries_to_fix if d in self.product_deliveries]

        self.mark_deliveries_disrupted(deliveries_to_fix, disrupted=False)
        self.load_deliveries(deliveries_to_fix)
        self.statistics_manager.reset_loss(product_deliveries_to_fix, self.node_to_exporter)
        self.statistics_manager.update_cost(product_deliveries_to_fix, self.node_to_exporter)
        self.statistics_manager.update_lost_demand(product_deliveries_to_fix, self.node_to_exporter, False)
        self.reset_parcels(deliveries_to_fix)
        self.disruption_nodes = []
        self.save_current_map()

    def handle_gradual_ending(self) -> None:
        """ If disruption type is a natural disaster (after ending the comeback is gradual) """
        if self.phase == 5:
            self.handle_disruption_end()
            return
        if self.phase == 1:
            deactivated_nodes = bfs_limited(self.network, self.place_of_disruption, max_depth=self.depth)
        else:
            previous_depth = self.disaster_steps_dict[f"phase_{self.phase - 1}"]
            deactivated_nodes = bfs_limited(self.network, self.place_of_disruption, max_depth=previous_depth)

        current_depth = self.disaster_steps_dict[f"phase_{self.phase}"]
        nodes_to_deactivate = bfs_limited(self.network, self.place_of_disruption, max_depth=current_depth)

        nodes_to_activate = deactivated_nodes - nodes_to_deactivate
        self.network.activate_nodes(nodes_to_activate)

        previously_disrupted_deliveries = [d for d in self.deliveries if d.disrupted]
        self.load_deliveries(previously_disrupted_deliveries)
        currently_disrupted_deliveries = self.find_deactivated_deliveries()
        currently_disrupted_deliveries = self.mark_deliveries_disrupted(currently_disrupted_deliveries, disrupted=True)

        fixed_deliveries = [d for d in previously_disrupted_deliveries if d not in currently_disrupted_deliveries]
        fixed_product_deliveries = [d for d in fixed_deliveries if d in self.product_deliveries]

        self.mark_deliveries_disrupted(fixed_deliveries, disrupted=False)

        self.update_deliveries(currently_disrupted_deliveries)
        self.reset_parcels(currently_disrupted_deliveries)

        self.load_deliveries(fixed_deliveries)
        self.statistics_manager.update_cost(fixed_product_deliveries, self.node_to_exporter)
        self.reset_parcels(currently_disrupted_deliveries)
        self.statistics_manager.reset_loss(fixed_product_deliveries, self.node_to_exporter)
        self.statistics_manager.update_lost_demand(fixed_product_deliveries, self.node_to_exporter, False)

        self.save_current_map(self.place_of_disruption)
        self.phase += 1

    def handle_time_step(self, t: int) -> None:
        for exporter in self.importer_exporters:
            """ Updating fulfilled demand """
            delivery = find_delivery_by_agent(self.product_deliveries, exporter)
            if self.start_day + delivery.lead_time > t >= self.start_day:
                self.statistics_manager.update_fulfilled_demand(exporter, True)
            else:
                self.statistics_manager.update_fulfilled_demand(exporter, False)

        """ Reset parcel content """
        deliveries_to_reset = self.find_parcels_to_reset()
        self.reset_parcels(deliveries_to_reset)

    def save_current_map(self, disrupted_nodes=None) -> None:
        try:
            if disrupted_nodes is not None:
                if isinstance(disrupted_nodes, int):
                    self.disruption_nodes = [disrupted_nodes]
                else:
                    self.disruption_nodes = list(disrupted_nodes) if not isinstance(disrupted_nodes, int) else [disrupted_nodes]

            print("MAP_UPDATE")
        except Exception as e:
            print(f"❌ Błąd podczas zapisu mapy: {e}")

    def find_deactivated_deliveries(self) -> list[Delivery]:
        disrupted_deliveries = []
        for delivery in self.deliveries:
            for node in delivery.route:
                if not self.network.nodes[node].get('active'):
                    self.statistics_manager.changed_routes += 1
                    disrupted_deliveries.append(delivery)
                    break
        return disrupted_deliveries

    def mark_deliveries_disrupted(self, deliveries: list[Delivery], disrupted: bool) -> list[Delivery]:
        for delivery in deliveries:
            delivery.disrupted = disrupted
        return deliveries

    def update_deliveries(self, disrupted_deliveries: list[Delivery]) -> None:
        """
        In both material and product deliveries update:
            * route
            * capacity
            * length
            * costs
            * lead time
        In only product deliveries update:
            * loss
        """
        active_network = self.network.get_active_graph()
        disrupted_product_deliveries = [d for d in disrupted_deliveries if d in self.product_deliveries]
        old_cost = [d.cost for d in disrupted_product_deliveries]

        for delivery in disrupted_deliveries:
            delivery.reset_delivery()
            delivery.update_delivery(self.node_to_exporter, active_network)
        self.statistics_manager.update_cost(disrupted_product_deliveries, self.node_to_exporter)
        self.statistics_manager.update_loss(disrupted_product_deliveries, self.node_to_exporter, old_cost)
        self.statistics_manager.update_lost_demand(disrupted_product_deliveries, self.node_to_exporter, True)

    def display_info(self) -> None:
        t = self.current_time
        for exporter in self.importer_exporters:
            print(f"Agent {exporter.agent_id}'s finances: {exporter.finances:.2f}")
        if int(self.disruption['dayOfStart']) == t:
            print(f"DISRUPTION OCCURS (time step {t})")
        if int(self.disruption['dayOfStart']) + int(self.disruption['duration']) == t:
            print(f"DISRUPTION ENDS (time step {t})")

    def save_deliveries(self, folder: str = "delivery", file_name: str = "starting_deliveries.json") -> None:
        data_path = os.path.join(self.path, "input_data/simulation_data")
        folder_path = os.path.join(data_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        full_path = os.path.join(folder_path, file_name)
        with open(full_path, "w", encoding="utf-8") as json_file:
            json.dump([delivery.to_dict() for delivery in self.deliveries], json_file, indent=4, ensure_ascii=False)

    def load_deliveries(self, deliveries: list[Delivery], folder: str = "delivery",
                        file_name: str = "starting_deliveries.json") -> None:
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

        for o in data:
            try:
                if self.deliveries[o["delivery_id"]] in deliveries:
                    self.deliveries[o["delivery_id"]].route = o["route"]
                    self.deliveries[o["delivery_id"]].length = o["length"]
                    self.deliveries[o["delivery_id"]].cost = o["cost"]
                    self.deliveries[o["delivery_id"]].lead_time = o["lead_time"]
                    self.deliveries[o["delivery_id"]].disrupted = o["disrupted"]
                    self.deliveries[o["delivery_id"]].capacity = self.deliveries[o["delivery_id"]].find_minimum_capacity(self.network)
                    self.deliveries[o["delivery_id"]].is_product = o["is_product"]
                    # print(f"New delivery loaded: {self.deliveries[object["delivery_id"]]}")
            except TypeError as e:
                print(f"Error while deserializing delivery object: {str(e)}")


    def find_parcels_to_reset(self) -> list[Delivery]:
        deliveries_to_reset = []
        for delivery in self.deliveries:
            if delivery.lead_time != 0 and self.current_time % math.ceil(delivery.lead_time) == 0:
                deliveries_to_reset.append(delivery)
        return deliveries_to_reset

    def reset_parcels(self, deliveries: list[Delivery]) -> None:
        for delivery in deliveries:
            agent = self.node_to_exporter[delivery.start_node_id]
            number_of_products = random.randrange(int(self.product_paths[agent.agent_id % 10]['total_distance_km'] / 10.0),
                                                  int(self.product_paths[agent.agent_id % 10]['total_distance_km'] / 5.0))
            new_parcel = self.agent_manager.delivery_manager.initialize_parcel([inv[0] for inv in agent.inventory],
                                                                               number_of_products)
            new_batch = self.agent_manager.delivery_manager.initialize_raw_material_batch(new_parcel)
            if delivery.is_product:
                delivery.parcel = new_parcel
            else:
                delivery.parcel = new_batch
            agent.send_parcel()

    def reset(self) -> None:
        self.current_time = 0

        """ Disruption reinitialization """
        with open(self.path, 'rb') as f:
            self.disruption = pickle.load(f)
        self.start_day = int(self.disruption['dayOfStart'])
        self.end_day = self.start_day + int(self.disruption['duration'])
        self.severity = self.disruption['severity']
        self.disruption_type = self.disruption['disruptionType']
        self.place_of_disruption = int(self.disruption["placeOfDisruption"])
        self.disaster_steps_dict = {}
        self.number_of_phases = 0
        self.phase = 1
        self.depth = 0
        self.interpret_disruption_parameters()

        """ Statistics reinitialization"""
        self.statistics_manager = StatisticsManager(len(self.importer_exporters), max_time=self.max_time)
        self.statistics_manager.total_routes = len(self.product_paths)
        for exporter in self.importer_exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.cost[exporter.agent_id] = cost

        self.initialize()
        # self.run()
