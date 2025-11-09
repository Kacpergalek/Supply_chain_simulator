from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager

reader = GraphManager()
graph = reader.load_pickle_graph("poland.pkl")
simulation = Simulation(10, 'day', graph)
simulation.run()