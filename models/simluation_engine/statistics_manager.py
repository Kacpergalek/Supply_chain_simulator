import numpy as np
import pandas as pd
from datetime import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))
from utils.stats_paths import get_old_csvs

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
    
    
    def add_dataframe(self, current_time : int):
        data = {
            f"{current_time}_lost_demand" : self.lost_demand,
            f"{current_time}_fulfilled_demand" : self.fulfilled_demand,
            f"{current_time}_cost" : self.cost,
            f"{current_time}_cost_after_disruption" : self.cost_after_disruption,
            f"{current_time}_loss" : self.loss
        }
        df = pd.DataFrame(data=data)
        self.dataframes.append(df)


    def save_to_csv(self):
        if len(self.dataframes) > 0:
            final_df = pd.concat(self.dataframes, axis=1, ignore_index=False)
            dt = datetime.now()
            formated_time = dt.strftime("%d_%m_%Y__%H_%M_%S")

            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\.."))
            file_path = os.path.join(path, "saved_statistics", f"stats_{formated_time}.csv")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            final_df.to_csv(file_path, index=True)
            self.dataframes.clear()
            print("Stats have been saved.")
        else:
            print("Disruption did not occur.")


    def delete_old_csv(self, days_ago=5):
        file_paths = get_old_csvs(days_ago=days_ago)
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"File cannot be removed: {str(e)}")


    def show_kpi_panel(self):
        #TODO
        # 1) create a panel in HTML / CSS
        # 2) pull it up with the updated stats
        pass
