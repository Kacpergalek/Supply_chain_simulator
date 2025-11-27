from .base_agent import BaseAgent
from typing import Optional, Dict, Any, Union
import networkx as nx


class ExporterAgent(BaseAgent):
    """
    Agent typu Eksporter (dziedziczy z BaseAgent).
    Dodatkowe atrybuty:
      - quantity: ile produkuje / ma do wysłania per krok (int)
      - price: cena za jednostkę (float)
      - finances: stan konta / budżet (float)
    Dodatkowe pola:
      - inventory: aktualny zapas (int) - startuje od 0
    Proste metody:
      - produce()        -> zwiększa inventory o quantity
      - create_offer(qty=None) -> zwraca ofertę sprzedaży (qty i unit_price)
      - sell(qty)        -> aktualizuje inventory i finances (zwraca kwotę)
    """

    def __init__(self, agent_id: int, node_id: int, store_name: str, store_category: str, city: str,
                 courier_company: str, finances: float = 1000.0):
        super().__init__(agent_id, node_id, city.split(",")[1])
        self.store_name = store_name
        self.store_category = store_category
        self.city = city
        self.courier_company = courier_company

        self.production_price = 0
        self.retail_price = 0
        # self.quantity = int(quantity)
        self.finances = float(finances)
        self.inventory = 0  # ile aktualnie ma w magazynie

    def __repr__(self):
        return (f"ExporterAgent(id={self.agent_id}, node={self.node_id}"
                f"retail_price={self.retail_price}, finances={self.finances}, inventory={self.inventory})")

    # def produce(self):
    #     """Proste wytwarzanie: przyrost zapasu o 'quantity'."""
    #     self.inventory += self.quantity
    #     self.finances -= (self.retail_price * 0.5) * self.quantity
    #     return self.inventory
    #
    # def create_offer(self, qty=None):
    #     """
    #     Tworzy ofertę sprzedaży. Jeśli qty nie podane -> proponuje max możliwy (min(inventory, quantity)).
    #     Zwraca dict: {'agent_id', 'node_id', 'qty', 'unit_price'}.
    #     """
    #     if qty is None:
    #         qty = min(self.inventory, self.quantity)
    #     qty = int(min(qty, self.inventory))
    #     return {
    #         "agent_id": self.agent_id,
    #         "node_id": self.node_id,
    #         "qty": qty,
    #         "unit_price": self.retail_price
    #     }
    #
    # def sell(self, qty):
    #     """
    #     Realizuje sprzedaż: zmniejsza inventory i zwiększa finances.
    #     Zwraca revenue (float). Jeśli qty > inventory -> sprzedaje tyle ile ma.
    #     """
    #     qty = int(qty)
    #     sold = min(qty, self.inventory)
    #     revenue = sold * self.retail_price
    #     self.inventory -= sold
    #     self.finances += revenue
    #     return sold, revenue

    def to_dict(self):
        d = super().to_dict()
        d.update({
            # "quantity": self.quantity,
            "price": self.retail_price,
            "finances": self.finances,
            "inventory": self.inventory
        })
        return d

    @staticmethod
    def _parse_maxspeed(ms: Union[str, float, list, None]) -> Optional[float]:
        """
        ms może być: int/float, string ('50', '50 mph', '50;70'), list ['50','70'] itd.
        Zwraca speed w km/h lub None jeśli nie da się sparsować.
        """
        if ms is None:
            return None

        if isinstance(ms, (int, float)):
            return float(ms)

        if isinstance(ms, (list, tuple)):
            vals = [ExporterAgent._parse_maxspeed(x) for x in ms]
            valid_vals = [v for v in vals if v is not None]
            return max(valid_vals) if valid_vals else None

        if isinstance(ms, str):
            s = ms.strip().lower()
            s = s.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace(" ", "")

            # Helper to extract number from string
            def get_num(val_str):
                try:
                    return float(''.join(c for c in val_str if (c.isdigit() or c == '.')))
                except ValueError:
                    return None

            # Handle mph
            is_mph = "mph" in s

            # Handle separators like ';' or ',' or '|'
            for sep in [";", ",", "|"]:
                if sep in s:
                    parts = [get_num(p) for p in s.split(sep) if p]
                    valid = [p for p in parts if p is not None]
                    val = max(valid) if valid else None
                    return val * 1.60934 if (val and is_mph) else val

            # Single value string
            val = get_num(s)
            if val is not None:
                return val * 1.60934 if is_mph else val

        return None

    def find_cheapest_path(self, sim_graph, dest_node: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Finds the cheapest path based on monetary cost (length_km * unit_cost).
        Also calculates estimated lead time based on maxspeed.

        Arguments:
            sim_graph: SimulationGraph or nx.MultiDiGraph.
            dest_node: Target node ID.
            params: Dict with optional settings:
                - driving_hours_per_day (float): Default 8.0
                - default_speed_kmh (float): Default 60.0 (fallback if no maxspeed)
                - default_unit_cost (dict[str, float]):
        """
        if params is None:
            params = {}

        # 1. Configuration
        driving_hours = float(params.get("driving_hours_per_day", 8.0))
        default_speed = float(params.get("default_speed_kmh", 60.0))

        prices = params.get("courier_price_profile", {
            "price_per_km_land": 1.0,
            "price_per_km_air": 5.0,
            "price_per_km_sea": 0.5
        })
        speed_land_default = 60.0
        speed_air_default = 800.0  # Avg cruising speed
        speed_sea_default = 35.0

        if sim_graph is None or nx is None:
            return {"error": "Graph or NetworkX not available"}

        def get_edge_mode(edge_data):
            """Returns 'air', 'sea', or 'land' based on OSM tags."""
            # Explicit override
            if edge_data.get("mode") in ["air", "flight"]:
                return "air"
            if edge_data.get("mode") in ["sea", "shipping"]:
                return "sea"

            # OSM standard tags
            if edge_data.get("route") == "ferry":
                return "sea"
            if "aeroway" in edge_data:
                return "air"

            # Default to land (highway, railway, etc.)
            return "land"

<<<<<<< HEAD
                data[tmp_attr] = (alpha * dist_km) * (beta * cost_attr) + gamma * risk_attr + (delta * (time_days if time_days is not None else 0.0))
                data["_tmp_time_days"] = time_days if time_days is not None else 0.0
           
            try:
                path = sim_graph.safe_astar_path(self.node_id, dest_node, weight=tmp_attr)
               
                total_weight = 0.0
                total_distance_km = 0.0
                total_cost = 0.0
                total_risk = 0.0
                total_time_days = 0.0
            
                for u, v in zip(path[:-1], path[1:]):
=======
        # 2. Define Cost Function for Dijkstra
        # This function calculates weight dynamically without modifying the graph.
        def weight_function(u, v, d):
            length_m = d.get("length", 0.0)
            dist_km = length_m / 1000.0
>>>>>>> 57ce2d7 (for merging)

            # Get unit cost from edge (defaulting to 1.0 if missing)
            # You requested: Cost = Length * Unit Cost

            mode = get_edge_mode(d)

            if mode == "air":
                unit_cost = prices["price_per_km_air"]
            elif mode == "sea":
                unit_cost = prices["price_per_km_sea"]
            else:
                unit_cost = prices["price_per_km_land"]

            return dist_km * unit_cost

        try:
            # 3. Find Path (Minimizing Monetary Cost)
            # shortest_path automatically handles MultiDiGraph by picking the edge minimizing the weight
            path = nx.shortest_path(sim_graph, source=self.node_id, target=dest_node, weight=weight_function)

            # 4. Calculate Statistics for the found path
            total_distance_km = 0.0
            total_money_cost = 0.0
            total_lead_time_days = 0.0

            # Iterate through the path to sum up stats
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]

                # In a MultiDiGraph, there might be multiple edges between u and v.
                # We must find the specific edge that gave us the minimum cost (the one Dijkstra picked).
                edges_data = sim_graph.get_edge_data(u, v)

                # Find the 'best' edge key based on our cost criteria
                best_edge = None
                best_cost_val = float('inf')

                # edges_data is a dict of {key: attributes}
                for key, attr in edges_data.items():
                    w = weight_function(u, v, attr)
                    if w < best_cost_val:
                        best_cost_val = w
                        best_edge = attr

                if best_edge:
                    # Metrics for this segment
                    length_m = best_edge.get("length", 0.0)
                    dist_km = length_m / 1000.0
                    mode = get_edge_mode(best_edge)

                    # Time Calculation
                    # --- Time Calculation Logic ---
                    hours_required = 0.0

                    if mode == "land":
                        # Land: Respect maxspeed and driving hours limits
                        ms = self._parse_maxspeed(best_edge.get("maxspeed"))
                        speed = ms if (ms and ms > 0) else speed_land_default
                        hours_driving = dist_km / speed

                        # Convert driving hours to "elapsed days" considering shifts
                        # e.g., if driving 8h/day, a 16h drive takes 2 days.
                        if driving_hours > 0:
                            total_lead_time_days += (hours_driving / driving_hours)
                        else:
                            # Fallback if driving hours is 0 (continuous)
                            total_lead_time_days += (hours_driving / 24.0)

                    elif mode == "air":
                        # Air: Continuous travel (24h/day valid), high speed
                        speed = speed_air_default  # Flight speed usually constant
                        hours_flying = dist_km / speed
                        # Add typical loading/unloading overhead for air (e.g. 4 hours)?
                        # hours_flying += 4.0
                        total_lead_time_days += (hours_flying / 24.0)

                    elif mode == "sea":
                        # Sea: Continuous travel (24h/day valid), low speed
                        speed = speed_sea_default
                        hours_sailing = dist_km / speed
                        total_lead_time_days += (hours_sailing / 24.0)

                    total_distance_km += dist_km
                    total_money_cost += best_cost_val
            return {
                "method": "multimodal_cost_min",
                "path": path,
                "total_weight": total_money_cost,
                "estimated_cost": total_money_cost,
                "total_distance_km": total_distance_km,
                "estimated_lead_time_days": total_lead_time_days,
            }

        except nx.NetworkXNoPath:
            print(f"No path found for agent {self.agent_id} to {dest_node}")
            return {}
        except Exception as e:
            print(f"Error in pathfinding: {e}")
            import traceback
            traceback.print_exc()
            return {}