import pandas as pd
import time

class StatisticsManager:
    def __init__(self):
        self.lost_demand = {} # Dict: {'company' : number}
        self.fulfilled_demand = {} # Dict: {'company' : number}
        self.cost = {} # Dict: {'company' : float}
        self.cost_after_disruption = {} # Dict: {'company' : float}
        self.loss = {}
        self.total_routes = []
        self.changed_routes = []

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