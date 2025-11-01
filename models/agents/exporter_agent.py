from .base_agent import BaseAgent
import math

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



    def find_cheapest_path(self, graph, source_node, dest_node, params=None):
        """
        Zwraca dict z kluczami:
          - 'path': list of node ids (przybliżone lub rzeczywiste)
          - 'total_weight': suma wag (zgodnie z params)
          - 'total_distance_km': odległość w km (estymowana lub suma krawędzi)
          - 'estimated_lead_time_days': est. czas (prosty model)
          - 'estimated_cost': est. koszt (prosty model)
          - 'method': 'graph' lub 'heuristic'
        Params default: {'alpha':1.0, 'beta':0.0, 'gamma':0.0}
        """
        if params is None:
            params = {'alpha': 1.0, 'beta': 0.0, 'gamma': 0.0}

        alpha = float(params.get('alpha', 1.0))
        beta = float(params.get('beta', 0.0))
        gamma = float(params.get('gamma', 0.0))


        if graph is not None and nx is not None:
            
            def edge_weight(u, v, data):
                # distance_km
                dist_m = data.get('length', None) or data.get('distance_m', None) or data.get('distance', None)
                if dist_m is None:
                    # fallback - jeśli nie ma length, użyj 1
                    dist_km = 1.0
                else:
                    # NetworkX/OSMnx zwykle trzyma 'length' w metrach
                    if dist_m > 10000:  # heurystyka: jeżeli już w km (mała szansa)
                        # jeśli wartość jest w metrach zostaw
                        dist_km = dist_m / 1000.0
                    else:
                        # zakładamy, że 'length' to metry
                        dist_km = float(dist_m) / 1000.0

                cost_attr = data.get('cost', 0.0)    
                risk_attr = data.get('risk', 0.0)     

                weight = alpha * dist_km + beta * float(cost_attr) + gamma * float(risk_attr)
                return weight

 
            tmp_attr = "_tmp_combined_weight"

            for u, v, data in graph.edges(data=True):
                data[tmp_attr] = edge_weight(u, v, data)

            try:
                path = nx.shortest_path(graph, source=source_node, target=dest_node, weight=tmp_attr)
                # sumaryczne metryki:
                total_weight = 0.0
                total_dist_km = 0.0
                total_cost = 0.0
                total_risk = 0.0
                for i in range(len(path) - 1):
                    u = path[i]; v = path[i + 1]
                    ed = graph.get_edge_data(u, v)
                    # w multigraph może być dict, weź pierwszy klucz
                    if isinstance(ed, dict) and len(ed) > 0:
                        # ed może być {0: {...}} for MultiGraph
                        if 0 in ed and isinstance(ed[0], dict):
                            ed_data = ed[0]
                        else:
                            # when simple graph ed is attributes dict
                            if 'length' in ed:
                                ed_data = ed
                            else:
                                # ed might be nested; choose first
                                first_key = list(ed.keys())[0]
                                ed_data = ed[first_key] if isinstance(ed[first_key], dict) else ed
                    else:
                        ed_data = ed

                    dist_m = ed_data.get('length', ed_data.get('distance', 0.0))
                    dist_km = float(dist_m) / 1000.0 if dist_m is not None else 0.0
                    cost_e = float(ed_data.get('cost', 0.0))
                    risk_e = float(ed_data.get('risk', 0.0))
                    w = alpha * dist_km + beta * cost_e + gamma * risk_e
                    total_weight += w
                    total_dist_km += dist_km
                    total_cost += cost_e
                    total_risk += risk_e

                # cleanup tmp_attr to avoid side-effects
                for u, v, data in graph.edges(data=True):
                    if tmp_attr in data:
                        del data[tmp_attr]

                # estimate lead time: prosty model: assume average speed 60 km/day
                avg_speed_km_per_day = 60.0
                est_days = total_dist_km / avg_speed_km_per_day if avg_speed_km_per_day > 0 else None

                return {
                    'method': 'graph',
                    'path': path,
                    'total_weight': total_weight,
                    'total_distance_km': total_dist_km,
                    'estimated_lead_time_days': est_days,
                    'estimated_cost': total_cost
                }
            except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
                # brak ścieżki w grafie -> fallback to heuristic
                pass

        # ---------------------------
        # fallback (brak grafu lub brak ścieżki)
        # ---------------------------
        # W ciemno: estymacja po odległości Haversine (na podstawie node ids nie mamy lat/lon; więc
        # oczekujemy, że user może przekazać opcjonalnie mapping node->(lat,lon) w params['coords_map'].
        coords_map = None
        if params and isinstance(params, dict):
            coords_map = params.get('coords_map', None)

        if coords_map and source_node in coords_map and dest_node in coords_map:
            lat1, lon1 = coords_map[source_node]
            lat2, lon2 = coords_map[dest_node]
            dist_km = self._haversine_km(lon1, lat1, lon2, lat2)
        else:
            # jeśli nie ma coords, nie znamy odległości; użyjemy 1.0 km jako placeholder
            dist_km = 1.0

        # estymowany "weight" i cost: prosty model
        est_weight = alpha * dist_km + beta * 0.0 + gamma * 0.0
        # est_cost: załóżmy cena transportu = 0.1 * distance_km * volume_factor
        est_cost = 0.1 * dist_km
        # est_lead_time: przyjmijmy 60 km/day
        est_days = dist_km / 60.0

        return {
            'method': 'heuristic',
            'path': [source_node, dest_node],
            'total_weight': est_weight,
            'total_distance_km': dist_km,
            'estimated_lead_time_days': est_days,
            'estimated_cost': est_cost
        }

    @staticmethod
    def _haversine_km(lon1, lat1, lon2, lat2):
        """
        Prosty wzór Haversine zwracający odległość w kilometrach.
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2.0)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2.0)**2
        c = 2 * math.asin(math.sqrt(a))
        R = 6371.0  # Earth radius in kilometers
        return R * c

    
