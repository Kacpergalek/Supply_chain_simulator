import pickle
import time
import logging
import random
import sys 
import os
import json
from pathlib import Path

from models.agents.agent_manager import AgentManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from utils.find_nodes_to_disrupt import bfs_limited
from utils.find_nodes_to_disrupt import find_nodes_to_disrupt

from models.simluation_engine.statistics_manager import StatisticsManager
from models.simluation_engine.time_manager import TimeManager

from utils.find_delivery import find_delivery_by_agent
from utils.find_exporter import  find_exporter_by_node_id

from network.visualization import plot_agent_routes
from network.network import NetworkManager

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self):
        self.current_time = 0
        self.exporters = []
        self.importers = []
        self.deliveries = []

        self.statistics_manager = None

        """ Network initialization"""
        time_start = time.time()
        network_manager = NetworkManager()
        # self.network = network_manager.create_graph()
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
        # self.agent_paths = initiation(self.network)

        """ Deliveries initialization """
        self.deliveries = self.agent_manager.delivery_manager.initialize_deliveries(self.network, self.exporters,
                                                                                    self.agent_paths)
        self.max_time = 15
        self.time_manager = TimeManager("day")
        self.inject_parameters()
        self.initialize()


    def inject_parameters(self):
        project_path = Path(__file__).parent.parent.parent
        full_path = os.path.join(project_path, "input_data", "disruption_parameters.pkl")
        with open(full_path, 'rb') as f:
            self.disruption = pickle.load(f)
        self.statistics_manager = StatisticsManager(len(self.exporters), max_time=self.max_time)
        self.statistics_manager.total_routes = len(self.agent_paths)
        for exporter in self.exporters:
            cost = find_delivery_by_agent(self.deliveries, exporter).cost
            self.statistics_manager.cost[exporter.agent_id] = cost


    def run(self):

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
            exporter.delivery = find_delivery_by_agent(self.deliveries, exporter)
            exporter.finances = random.randrange(1000, 5000)

        # NOWE: wywolanie funkcji ktora szuka najlepszych wezlow do disruption i zapisuje w json i zapisanie wersji mapy na samym poczatku bez zadnych zaklocen
        find_nodes_to_disrupt(self.network, self.deliveries)
        self.save_deliveries()
        self.save_current_map()
        #time.sleep(2)

    def should_continue(self) -> bool:
        if self.current_time >= self.max_time:
            return False
        return True

    def finalize(self):
        """ Saving statistics to a csv file and displaying a KPI panel"""
        self.statistics_manager.save_statistics()

    def save_current_map(self, filename="latest_map.png", disrupted_nodes =None):
        """Zapisuje aktualny stan sieci i tras do pliku PNG."""
        try:
            '''
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
            )'''
            if disrupted_nodes is not None:
                self.disruption_nodes = disrupted_nodes
            print("MAP_UPDATE")
        except Exception as e:
            print(f"❌ Błąd podczas zapisu mapy: {e}")

    def execute_time_step(self):

        t = self.current_time
        print(f" =========== Executing time step {t} ===========")

        """ Start a disruption """
        if int(self.disruption['dayOfStart']) == t:
            start_disruption_time = time.time()
            disruption_place = int(self.disruption["placeOfDisruption"])
            place_of_disr_time = time.time()
            places_of_disruption = bfs_limited(self.network, disruption_place, max_depth=20)
            print(f"Finding place of disruption: {time.time() - place_of_disr_time}")
            self.network.deactivate_nodes(places_of_disruption)
            self.disruption_nodes = [disruption_place]
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
            self.disruption_nodes = []
            # self.default_routes()
            self.load_deliveries()
            self.save_current_map()
            time.sleep(2)

        """ What happens regardless of a disruption"""
        for exporter in self.exporters:
            # TODO
            """ Updating finances """
            exporter.send_parcel()

            """ Updating fulfilled demand """
            self.statistics_manager.fulfilled_demand[exporter.agent_id] = exporter.unit_demand

        # """ What happens when there is no disruption"""
        # if t < int(self.disruption['dayOfStart']) or t > int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
        #     for exporter in self.exporters:
        #         delivery = find_delivery_by_agent(self.deliveries, exporter)
        #         fulfilled_demand = int(exporter.quantity / delivery.lead_time)
        #         self.statistics_manager.update_fulfilled_demand(exporter.agent_id, fulfilled_demand)

        """ What happens during a disruption"""
        if int(self.disruption['dayOfStart']) <= t <= int(self.disruption['dayOfStart']) + int(self.disruption['duration']):
            self.statistics_manager.calculate_loss()
        #     for exporter in self.exporters:
        #         delivery = find_delivery_by_agent(self.deliveries, exporter)
        #         lost_demand = int(exporter.quantity / delivery.lead_time)
        #         self.statistics_manager.update_lost_demand(exporter.agent_id, lost_demand)
        #self.save_current_map()


    def find_disrupted_routes(self):
        """ Mark all routes that contain disrupted nodes as disrupted"""
        for delivery in self.deliveries:
            for node in delivery.route:
                if not self.network.nodes[node].get('active'):
                    self.statistics_manager.changed_routes += 1
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
            self.statistics_manager.cost[agent.agent_id] = delivery.cost

    def update_lost_demand(self):
        for exporter in self.exporters:
            delivery = find_delivery_by_agent(self.deliveries, exporter)
            if delivery.disrupted:
                self.statistics_manager.lost_demand[exporter.agent_id] = exporter.unit_demand


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


    def reset(self):
        self.current_time = 0
        self.exporters = []
        self.importers = []
        self.deliveries = []
        self.statistics_manager = StatisticsManager()

        self.initialize()

    def save_deliveries(self, folder : str = "delivery", file_name : str = "starting_deliveries.json"):
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data")
        folder_path = os.path.join(data_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        full_path = os.path.join(folder_path, file_name)
        with open(full_path, "w", encoding="utf-8") as json_file:
            json.dump([delivery.to_dict() for delivery in self.deliveries], json_file, indent=4, ensure_ascii=False)


    def load_deliveries(self, folder : str = "delivery", file_name : str = "starting_deliveries.json"):
        data_path = os.path.join(Path(__file__).parent.parent.parent, "input_data/simulation_data")
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
                self.deliveries[object["delivery_id"]].route = object["route"]
                self.deliveries[object["delivery_id"]].length = object["length"]
                self.deliveries[object["delivery_id"]].cost = object["cost"]
                self.deliveries[object["delivery_id"]].lead_time = object["lead_time"]
                self.deliveries[object["delivery_id"]].disrupted = object["disrupted"]
                self.deliveries[object["delivery_id"]].find_minimum_capacity(self.network)
            except TypeError as e:
                print(f"Error while deserializing delivery object: {str(e)}")