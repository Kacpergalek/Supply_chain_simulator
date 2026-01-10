from enum import Enum

# minimalny koszt przewozu towaru za 1km
class MinimalCostType(Enum):
    ROAD = 3
    AIR_ROUTE = 6
    SEA_ROUTE = 4