class Delivery:
    def __init__(self, delivery_id: int, start_node_id: int, end_node_id: int):
        self.delivery_id = delivery_id
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.route = []
        self.length = 0
        self.cost = 0
        self.disrupted = False
        pass

    def update_route(self, route: list, length, cost):
        self.route = route
        self.length = length
        self.cost = cost