import pandas as pd
import time

class StatisticsManager:
    def __init__(self):
        self.lost_demand = {} # Dict: {'company' : number}
        self.fulfilled_demand = {} # Dict: {'company' : number}
        self.cost = {} # Dict: {'company' : float}
        self.cost_after_disruption = {} # Dict: {'company' : float}
        self.loss = {}
        self.total_routes = 0
        self.changed_routes = 0

    def update_fulfilled_demand(self, company, fulfilled_demand):
        self.fulfilled_demand[company] += fulfilled_demand
        pass

    def update_lost_demand(self, company, lost_demand):
        self.lost_demand[company] += lost_demand
        pass

    def define_cost(self, company, cost):
        self.cost[company] = cost
        pass

    def define_cost_after_disruption(self, company, cost):
        self.cost_after_disruption[company] = cost

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