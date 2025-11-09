import pandas as pd
import time

class StatisticsManager:
    def __init__(self):
        #TODO change dicts to lists probably
        self.lost_demand = {} # Dict: {'str(company_id)' : number}
        self.fulfilled_demand = {} # Dict: {'str(company_id)' : number}
        self.cost = {} # Dict: {'str(company_id)' : float}
        self.cost_after_disruption = {} # Dict: {'str(company_id)' : float}
        self.loss = {}
        self.total_routes = 0
        self.changed_routes = 0

    def update_fulfilled_demand(self, company_id, fulfilled_demand):
        self.fulfilled_demand[str(company_id)] += fulfilled_demand
        pass

    def update_lost_demand(self, company_id, lost_demand):
        self.lost_demand[str(company_id)] += lost_demand
        pass

    def define_cost(self, company_id, cost):
        self.cost[str(company_id)] = cost
        pass

    def define_total_routes(self, total_routes):
        self.total_routes = total_routes

    def increment_changed_routes(self):
        self.changed_routes += 1

    def define_cost_after_disruption(self, company_id, cost):
        self.cost_after_disruption[str(company_id)] = cost

    def calculate_loss(self):
        #TODO
        # loss = cost_after_disruption - cost
        pass

    def create_dataframe(self):
        #TODO
        # add all stats to dataframe
        df = pd.DataFrame()
        return df

    def show_kpi_panel(self):
        #TODO
        # 1) create a panel in HTML / CSS
        # 2) pull it up with the updated stats
        pass

    def save_to_csv(self, df):
        timestamp = time.strftime("%H_%M_%S")
        df.to_csv(f'../../saved_statistics/stats_{timestamp}.csv', index=False)
        pass