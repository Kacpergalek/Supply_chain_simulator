# raczej się nie przyda 

from shapely import LineString

class Edge():
    def __init__(self, 
                 id : int, 
                 start_node : int, 
                 end_node : int,
                 length : float,
                 capacity : int,
                 type : str,
                 cost : float,
                 linestring : LineString
                 ):
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.length = length
        self.capacity = capacity
        self.type = type
        self.cost = cost
        self.linestring = linestring

    def as_dict(self):
        edge = {
            "id": self.id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "length": self.length,
            "capacity": self.capacity,
            "type": self.type,
            "cost": self.cost,
            "linestring": self.linestring
        }
        return edge
    