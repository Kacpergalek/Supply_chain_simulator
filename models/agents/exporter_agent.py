from models.agents.base_agent import BaseAgent
from typing import Optional, Dict, Any, Union
import networkx as nx

from models.delivery.product import Product
from utils.find_quantity_by_product import find_quantity_by_product


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
                 courier_company: str, products: list[Product], finances: float = 1000.0):
        super().__init__(agent_id, node_id, city.split(",")[1])
        self.store_name = store_name
        self.store_category = store_category
        self.city = city
        self.courier_company = courier_company

        self.inventory = [(product, 1_000_000) for product in products]
        self.delivery = None
        self.unit_demand = 0
        self.finances = float(finances)

        # self.production_price = 0
        # self.retail_price = 0
        # # self.quantity = int(quantity)

        # self.inventory = 0  # ile aktualnie ma w magazynie

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "store_name": self.store_name,
            "store_category": self.store_category,
            "city": self.city,
            "courier_company": self.courier_company,
            "products": [product for product, _ in self.inventory],
            "finances": self.finances
        }

    # def __repr__(self):
    #     return (f"ExporterAgent(id={self.agent_id}, node={self.node_id}"
    #             f"retail_price={self.retail_price}, finances={self.finances}, inventory={self.inventory})")

    # def produce(self, quantity: int = 1):
    #     for product, inventory in self.inventory:
    #         inventory += quantity
    #         self.finances -= product.production_price * quantity

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
    def products_to_dict(self):
        product_dict = {}
        for product, inventory in self.inventory:
            product_dict[product.product_id] = inventory
        return product_dict

    def send_parcel(self):
        # Defensive checks: ensure delivery exists and parcel is iterable
        if self.delivery is None:
            raise RuntimeError(
                f"Exporter {self.agent_id} has no delivery assigned")

        demand = 0
        new_inventory = []
        parcel = getattr(self.delivery, "parcel", []) or []

        for product, inv in self.inventory:
            quantity = find_quantity_by_product(parcel, product)
            # Ensure quantity is an int and clamp to available inventory
            try:
                quantity = int(quantity or 0)
            except Exception:
                quantity = 0

            sold = min(inv, quantity)
            inv = inv - sold
            demand += sold
            new_inventory.append((product, inv))

        # Persist updated inventory
        self.inventory = new_inventory

        # Update finances defensively (guard if delivery methods/attrs missing)
        try:
            self.finances += self.delivery.find_parcel_retail_price()
        except Exception:
            pass

        try:
            parcel_cost = getattr(
                self.delivery, 'find_parcel_cost', lambda: 0)()
            self.finances -= parcel_cost * getattr(self.delivery, 'cost', 0)
        except Exception:
            pass

        self.unit_demand = demand
        # """
        # Realizuje sprzedaż: zmniejsza inventory i zwiększa finances.
        # Zwraca revenue (float). Jeśli qty > inventory -> sprzedaje tyle ile ma.
        # """
        # qty = int(qty)
        # sold = min(qty, self.inventory)
        # revenue = sold * self.retail_price
        # self.inventory -= sold
        # self.finances += revenue
        # return sold, revenue

    # def to_dict(self):
    #     d = super().to_dict()
    #     d.update({
    #         # "quantity": self.quantity,
    #         "price": self.retail_price,
    #         "finances": self.finances,
    #         "inventory": self.inventory
    #     })
    #     return d

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
            s = s.replace("[", "").replace("]", "").replace(
                "(", "").replace(")", "").replace(" ", "")

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
        Finds the cheapest path based on monetary cost (length_km * unit_cost) on the *active* graph.

        - If `sim_graph` has get_active_graph(), routing is done on that active subgraph.
        - If no path exists in the active graph but exists in the full graph, we treat it
          as a disruption-caused disconnection and return a structured "no path" result.
        """
        if params is None:
            params = {}

        # 1. Configuration
        driving_hours = float(params.get("driving_hours_per_day", 8.0))
        default_speed = float(params.get("default_speed_kmh", 60.0))

        prices = {
            "price_per_km_land": 1.0,
            "price_per_km_air": 5.0,
            "price_per_km_sea": 0.5
        }
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

        # 3. Dynamic cost function (kept here for flexibility; could be precomputed for even more speed)
        def weight_function(u, v, d):
            length_m = d.get("length", 0.0)
            dist_km = length_m / 1000.0

            mode = get_edge_mode(d)
            if mode == "air":
                unit_cost = prices["price_per_km_air"]
            elif mode == "sea":
                unit_cost = prices["price_per_km_sea"]
            else:
                unit_cost = prices["price_per_km_land"]

            # If edge has its own "cost" attribute, use it as a multiplier; otherwise use unit_cost
            return d.get('cost', unit_cost)

        # 4. Path finding
        try:
            # Defensive presence checks on the routing graph (active or full)
            if self.node_id not in sim_graph:
                raise nx.NetworkXNoPath(f"source node {self.node_id} not in routing graph")
            if dest_node not in sim_graph:
                raise nx.NetworkXNoPath(f"target node {dest_node} not in routing graph")

            # Dijkstra-style shortest path on routing_graph with custom weight
            # path = nx.shortest_path(
            #     sim_graph,
            #     source=self.node_id,
            #     target=dest_node,
            #     weight=weight_function
            # )

            path = sim_graph.astar(start_node=self.node_id, end_node=dest_node)

            # 5. Aggregate metrics
            total_distance_km = 0.0
            total_money_cost = 0.0
            total_lead_time_days = 0.0
            print(len(path))

            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                edges_data = sim_graph.get_edge_data(u, v)
                if not edges_data:
                    continue  # Should not happen, but be defensive

                # Find best edge between u and v by our weight_function
                best_edge = None
                best_cost_val = float("inf")
                for key, attr in edges_data.items():
                    w = weight_function(u, v, attr)
                    if w < best_cost_val:
                        best_cost_val = w
                        best_edge = attr

                if best_edge is None:
                    continue

                length_m = best_edge.get("length", 0.0)
                dist_km = length_m / 1000.0
                mode = get_edge_mode(best_edge)

                if mode == "land":
                    ms = self._parse_maxspeed(best_edge.get("maxspeed"))
                    speed = ms if (ms and ms > 0) else speed_land_default
                    hours_driving = dist_km / speed

                    if driving_hours > 0:
                        total_lead_time_days += (hours_driving / driving_hours)
                    else:
                        total_lead_time_days += (hours_driving / 24.0)
                elif mode == "air":
                    speed = speed_air_default
                    hours_flying = dist_km / speed
                    total_lead_time_days += (hours_flying / 24.0)
                elif mode == "sea":
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
            # 6. Robust diagnostics:
            #    Distinguish between:
            #    - graph disconnected even without disruptions
            #    - only active graph disconnected (disruption effect)
            # src_in_routing = self.node_id in sim_graph
            # dst_in_routing = dest_node in sim_graph
            # src_in_full = self.node_id in full_graph
            # dst_in_full = dest_node in full_graph
            #
            # reachable_in_full = False
            # if src_in_full and dst_in_full:
            #     try:
            #         reachable_in_full = nx.has_path(full_graph, self.node_id, dest_node)
            #     except Exception:
            #         reachable_in_full = False
            #
            # if reachable_in_full and not (src_in_routing and dst_in_routing):
            #     # One of endpoints was stripped out from active graph (e.g. deactivated node)
            #     reason = "endpoint_removed_from_active_graph"
            # elif reachable_in_full and (src_in_routing and dst_in_routing):
            #     # Both endpoints still present but active graph substructure broke connectivity
            #     reason = "disruption_disconnected_components"
            # else:
            #     reason = "no_path_even_in_full_graph"

            # print(
            #     f"No path found for agent {self.agent_id} from {self.node_id} to {dest_node}. "
            #     f"reason={reason}, "
            #     f"src_in_routing={src_in_routing}, dst_in_routing={dst_in_routing}, "
            #     f"src_in_full={src_in_full}, dst_in_full={dst_in_full}, "
            #     f"reachable_in_full={reachable_in_full}"
            # )

            # Return structured "no path" result instead of empty dict
            return {}

        except Exception as e:
            print(f"Error in pathfinding for agent {self.agent_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "method": "error",
                "error": str(e),
                "path": [],
            }
