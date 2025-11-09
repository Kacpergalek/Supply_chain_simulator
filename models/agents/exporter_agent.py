from .base_agent import BaseAgent
import math
from typing import Optional, Dict, Any

try:
    import networkx as nx
except Exception:
    nx = None 

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
    def __init__(self, agent_id, node_id, country="Poland", quantity=100, price=10.0, finances=1000.0):
        super().__init__(agent_id, node_id, country)
        self.quantity = int(quantity)
        self.price = float(price)
        self.finances = float(finances)
        self.inventory = 0  # ile aktualnie ma w magazynie

    def __repr__(self):
        return (f"ExporterAgent(id={self.agent_id}, node={self.node_id}, qty_per_step={self.quantity}, "
                f"price={self.price}, finances={self.finances}, inventory={self.inventory})")

    def produce(self):
        """Proste wytwarzanie: przyrost zapasu o 'quantity'."""
        self.inventory += self.quantity
        return self.inventory

    def create_offer(self, qty=None):
        """
        Tworzy ofertę sprzedaży. Jeśli qty nie podane -> proponuje max możliwy (min(inventory, quantity)).
        Zwraca dict: {'agent_id', 'node_id', 'qty', 'unit_price'}.
        """
        if qty is None:
            qty = min(self.inventory, self.quantity)
        qty = int(min(qty, self.inventory))
        return {
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "qty": qty,
            "unit_price": self.price
        }

    def sell(self, qty):
        """
        Realizuje sprzedaż: zmniejsza inventory i zwiększa finances.
        Zwraca revenue (float). Jeśli qty > inventory -> sprzedaje tyle ile ma.
        """
        qty = int(qty)
        sold = min(qty, self.inventory)
        revenue = sold * self.price
        self.inventory -= sold
        self.finances += revenue
        return sold, revenue

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "quantity": self.quantity,
            "price": self.price,
            "finances": self.finances,
            "inventory": self.inventory
        })
        return d



    def find_cheapest_path(self, sim_graph, dest_node: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Znajdź najtańszą ścieżkę z self.node_id do dest_node na obiekcie SimulationGraph.

        Arguments:
            sim_graph: SimulationGraph lub inny nx.MultiDiGraph z krawędziami zawierającymi 'length' (metry) i 'cost' (opcjonalnie)
            dest_node: target node id (int)
            params: dict (opcjonalne), możliwe klucze:
                - alpha (float): waga distance_km (domyślnie 1.0)
                - beta  (float): waga cost (domyślnie 0.0)
                - gamma (float): waga risk (domyślnie 0.0)  -- jeśli krawędzie mają 'risk' attr
                - coords_map: dict node_id -> (lat, lon) używane w fallback
                - avg_speed_km_per_day: float (do est. lead time, domyślnie 60.0)
        Returns:
            dict z polami:
              - method: 'graph' lub 'heuristic'
              - path: list node ids (przybliżony lub rzeczywisty)
              - total_weight: suma wag (alpha*dist + beta*cost + gamma*risk)
              - total_distance_km
              - estimated_lead_time_days
              - estimated_cost
        """
        #print(f"[DEBUG] Agent {self.agent_id}: sim_graph={type(sim_graph)}")
        if params is None:
            params = {}

        alpha = float(params.get("alpha", 1.0))
        beta = float(params.get("beta", 1.0))
        if beta == 0:
            beta = 1.0 
        gamma = float(params.get("gamma", 0.0))
        delta = float(params.get("time_weight", 1.0)) 
        coords_map = params.get("coords_map", None)
        avg_speed = float(params.get("avg_speed_km_per_day", 60.0))
        driving_hours_per_day = float(params.get("driving_hours_per_day", 24.0)) 
        default_speed_kmh = float(params.get("default_speed_kmh", max(60.0, avg_speed / driving_hours_per_day)))

        def parse_maxspeed(ms):
            """
            ms może być: int/float, string ('50', '50 mph', '50;70'), list ['50','70'] itd.
            Zwraca speed w km/h lub None jeśli nie da się sparsować.
            """
            if ms is None:
                return None
            # jeśli liczba
            if isinstance(ms, (int, float)):
                try:
                    return float(ms)
                except Exception:
                    return None
            # jeśli lista / tuple
            if isinstance(ms, (list, tuple)):
                vals = []
                for it in ms:
                    v = parse_maxspeed(it)
                    if v is not None:
                        vals.append(v)
                return max(vals) if vals else None
            # jeśli string
            if isinstance(ms, str):
                s = ms.strip()
                # usuń nawiasy i spacje
                s = s.strip("[]() ")
                # często separator ';' lub ',' lub '|' - spróbuj rozbić
                for sep in [";", ",", "|", " "]:
                    if sep in s:
                        parts = [p.strip() for p in s.split(sep) if p.strip()]
                        vals = []
                        for p in parts:
                            # sprawdź mph
                            if "mph" in p.lower():
                                try:
                                    num = float(''.join(ch for ch in p if (ch.isdigit() or ch == ".")))
                                    vals.append(num * 1.60934)  # mph -> km/h
                                except Exception:
                                    pass
                            else:
                                try:
                                    num = float(''.join(ch for ch in p if (ch.isdigit() or ch == ".")))
                                    vals.append(num)
                                except Exception:
                                    pass
                        if vals:
                            return max(vals)
                # jeśli nie było rozdzielania, spróbuj pojedynczej liczby lub '50mph'
                if "mph" in s.lower():
                    try:
                        num = float(''.join(ch for ch in s if (ch.isdigit() or ch == ".")))
                        return num * 1.60934
                    except Exception:
                        return None
                try:
                    num = float(''.join(ch for ch in s if (ch.isdigit() or ch == ".")))
                    return num
                except Exception:
                    return None
            return None
     
        if sim_graph is not None:
          
            tmp_attr = "_tmp_combined_weight"

 
            for u, v, key, data in sim_graph.edges(data=True, keys=True):
             
                length_m = data.get("length", None)
                if length_m is None:
                    dist_km = 0.0
                else:
                    try:
                        dist_km = float(length_m) / 1000.0
                    except Exception:
                        dist_km = 0.0

                cost_attr = float(data.get("cost", 0.0))
                risk_attr = float(data.get("risk", 0.0))

                speed_kmh = parse_maxspeed(data.get("maxspeed", None))
                if speed_kmh is None or speed_kmh <= 0:
                    speed_kmh = default_speed_kmh

                km_per_day = speed_kmh * driving_hours_per_day 
                time_days = dist_km / km_per_day if km_per_day > 0 else None

                data[tmp_attr] = (alpha * dist_km) * (beta * cost_attr) + gamma * risk_attr + (delta * (time_days if time_days is not None else 0.0))
                data["_tmp_time_days"] = time_days if time_days is not None else 0.0
           
            try:
                path = sim_graph.safe_shortest_path(self.node_id, dest_node, weight=tmp_attr)
               
                total_weight = 0.0
                total_distance_km = 0.0
                total_cost = 0.0
                total_risk = 0.0
                total_time_days = 0.0
            
                for u, v in zip(path[:-1], path[1:]):

                    edges_between = sim_graph[u].get(v, {})
                 
                    best_weight = None
                    best_data = None
                    for k, ed in edges_between.items():
                        w_val = ed.get(tmp_attr, None)

                        if w_val is None:
                            length_m = ed.get("length", 0.0)
                            dist_km = float(length_m) / 1000.0 if length_m is not None else 0.0
                            c = float(ed.get("cost", 0.0))
                            r = float(ed.get("risk", 0.0))
                            speed_kmh = parse_maxspeed(ed.get("maxspeed", None)) or default_speed_kmh
                            km_per_day = speed_kmh * driving_hours_per_day if driving_hours_per_day > 0 else default_speed_kmh * driving_hours_per_day
                            time_days_local = dist_km / km_per_day if km_per_day > 0 else 0.0
                            w_val = (alpha * dist_km) * (beta * c) + gamma * r + delta * time_days_local
                        if best_weight is None or w_val < best_weight:
                            best_weight = w_val
                            best_data = ed

          
                    if best_data is None:
                        dist_km = 0.0
                        cost_e = 0.0
                        risk_e = 0.0
                        w_val = 0.0
                        time_days_e =0.0
                    else:
                        length_m = best_data.get("length", 0.0)
                        dist_km = float(length_m) / 1000.0 if length_m is not None else 0.0
                        cost_e = float(best_data.get("cost", 0.0))
                        risk_e = float(best_data.get("risk", 0.0))
                        time_days_e = float(best_data.get("_tmp_time_days", 0.0))
                        w_val = best_weight

                    total_weight += w_val
                    total_distance_km += dist_km
                    total_cost += cost_e
                    total_risk += risk_e
                    total_time_days += time_days_e

                for u, v, key, data in sim_graph.edges(data=True, keys=True):
                    if tmp_attr in data:
                        del data[tmp_attr]
                    if "_tmp_time_days" in data:
                        del data["_tmp_time_days"]

                est_days = None
                if delta > 0.0:
                    est_days = total_time_days
                else:
                    # fallback na avg_speed_km_per_day
                    est_days = total_distance_km / avg_speed if avg_speed > 0 else None

                return {
                    "method": "graph",
                    "path": path,
                    "total_weight": total_weight,
                    "total_distance_km": total_distance_km,
                    "estimated_lead_time_days": est_days,
                    "estimated_cost": total_cost,
                    "total_risk": total_risk
                }

            except Exception as e:
                # jeśli coś poszło nie tak (np. NodeNotFound, NoPath), przejdź do heurystyki
                # przed przejściem - cleanup tmp_attr (na wszelki wypadek)
                for u, v, key, data in sim_graph.edges(data=True, keys=True):
                    if tmp_attr in data:
                        del data[tmp_attr]
                    if "_tmp_time_days" in data:
                        del data["_tmp_time_days"]
                print(f"⚠️ Graph path failed for agent {self.agent_id}: {e}")
             

        
