import pandas as pd
import time
import datetime

class StatisticsManager:
    def __init__(self):
        # list index = agent id
        self.lost_demand = []
        self.fulfilled_demand = []
        self.cost = []
        self.cost_after_disruption = []
        self.loss = []
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
        data = {
            "lost_demand" : self.lost_demand,
            "fullfilled_demand" : self.fulfilled_demand,
            "cost" : self.cost,
            "cost_after_disruption" : self.cost_after_disruption,
            "loss" : self.loss
        }
        df = pd.DataFrame(data=data)
        return df
    
    def save_to_csv(self):
        df = self.create_dataframe()
        time = time.time()
        dt = datetime.fromtimestamp(time)
        formated_time = dt.strftime("%H_%M_%S")
        df.to_csv(f'../../saved_statistics/stats_{formated_time}.csv', index=True)


    def show_kpi_panel(self):
        #TODO
        # 1) create a panel in HTML / CSS
        # 2) pull it up with the updated stats
        pass
