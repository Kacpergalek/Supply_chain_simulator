import numpy as np
import pandas as pd
import time
import datetime
import os

class StatisticsManager:
    def __init__(self):
        # lists index = agent id
        self.lost_demand = np.zeros(10)
        self.fulfilled_demand = np.zeros(10)
        self.cost = np.zeros(10)
        self.cost_after_disruption = np.zeros(10)
        self.loss = np.zeros(10)
        self.total_routes = 0
        self.changed_routes = 0
        self.dataframes = []

    def update_fulfilled_demand(self, company_id, fulfilled_demand):
        self.fulfilled_demand[company_id] += fulfilled_demand
        pass

    def update_lost_demand(self, company_id, lost_demand):
        self.lost_demand[company_id] += lost_demand
        pass

    def define_cost(self, company_id, cost):
        self.cost[company_id] = cost
        pass

    def define_total_routes(self, total_routes):
        self.total_routes = total_routes

    def increment_changed_routes(self):
        self.changed_routes += 1

    def define_cost_after_disruption(self, company_id, cost):
        self.cost_after_disruption[company_id] = cost

    def calculate_loss(self):
        #TODO
        # loss = cost_after_disruption - cost
        pass
    
    # option: b - before disruption, a - after disruption
    def add_dataframe(self, option : str, current_time : int):
        data = {
            f"{current_time}{option.lower()}_lost_demand" : self.lost_demand,
            f"{current_time}{option.lower()}_fullfilled_demand" : self.fulfilled_demand,
            f"{current_time}{option.lower()}_cost" : self.cost,
            f"{current_time}{option.lower()}_cost_after_disruption" : self.cost_after_disruption,
            f"{current_time}{option.lower()}_loss" : self.loss
        }
        df = pd.DataFrame(data=data)
        self.dataframes.append(df)


    def save_to_csv(self):
        if len(self.dataframes) > 0:
            final_df = pd.concat(self.dataframes, axis=1, ignore_index=False)
            time = time.time()
            dt = datetime.fromtimestamp(time)
            formated_time = dt.strftime("%H_%M_%S")

            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\.."))
            file_path = os.path.join(path, "saved_statistics", f"stats_{formated_time}.csv")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            final_df.to_csv(file_path, index=True)
            self.dataframes.clear()
        else:
            print("Disruption did not occur.")



    def show_kpi_panel(self):
        #TODO
        # 1) create a panel in HTML / CSS
        # 2) pull it up with the updated stats
        pass
