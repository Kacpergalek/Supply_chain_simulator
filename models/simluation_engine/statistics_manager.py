import numpy as np
import pandas as pd
from datetime import datetime
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
        self.demand_df = pd.DataFrame(columns=[f"Agent {i}" for i in range(10)])
        self.final_df = pd.DataFrame(columns=[f"Agent {i}" for i in range(10)])
        self.routes_df = pd.DataFrame(columns=['total routes', 'changed routes'])

    def update_fulfilled_demand(self, company_id, fulfilled_demand):
        self.fulfilled_demand[company_id] += fulfilled_demand

    def update_lost_demand(self, company_id, lost_demand):
        self.lost_demand[company_id] += lost_demand

    def define_cost(self, company_id, cost):
        self.cost[company_id] = cost
        self.cost_after_disruption[company_id] = cost

    def define_cost_after_disruption(self, company_id, cost):
        self.cost_after_disruption[company_id] = cost

    def define_total_routes(self, total_routes):
        self.total_routes = total_routes

    def increment_changed_routes(self):
        self.changed_routes += 1

    def calculate_loss(self, deliveries):
        for delivery in [d for d in deliveries if d.disrupted]:
            self.loss[delivery.delivery_id] +=\
                ((self.cost_after_disruption[delivery.delivery_id] - self.cost[delivery.delivery_id])
                 / delivery.lead_time)

    def add_dataframe(self, current_time: int):
        columns = [f"Agent {i}" for i in range(10)]
        if current_time < 10:
            current_time = f"0{current_time}"
        demand_df = pd.DataFrame(np.array([self.fulfilled_demand, self.lost_demand]),
                                 columns=columns,
                                 index=[f"{current_time}_fulfilled_demand", f"{current_time}_lost_demand"])

        self.demand_df = pd.concat([self.demand_df, demand_df], axis=0, ignore_index=False)

    def create_final_snapshot(self):
        columns = [f"Agent {i}" for i in range(10)]
        self.final_df = pd.DataFrame(np.array([self.fulfilled_demand, self.lost_demand, self.cost,
                                               self.cost_after_disruption, self.loss]), columns=columns,
                                     index=["fulfilled_demand", "lost_demand", "cost", "cost_after_disruption", "loss"])

        routes_df = pd.DataFrame([[self.total_routes, self.changed_routes]], columns=['total routes', 'changed routes'])
        self.routes_df = pd.concat([self.routes_df, routes_df], axis=0, ignore_index=True)

    def save_statistics(self):
        self.save_to_csv(self.demand_df, 'demand')
        self.save_to_csv(self.final_df, 'stats')
        self.save_to_csv(self.routes_df, 'routes')

    def save_to_csv(self, df: pd.DataFrame, filename: str):
        if len(df.columns) > 0 and len(df.index) > 0:
            # dataframe already contains the rows we need — just use a copy
            final_df = df.copy()
            dt = datetime.now()
            formated_time = dt.strftime("%d_%m_%Y__%H_%M_%S")

            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\.."))
            file_path = os.path.join(path, "saved_statistics", f"{filename}_{formated_time}.csv")
            file_path_json = os.path.join(path, "saved_statistics", f"{filename}_{formated_time}.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            final_df.to_csv(file_path, index=True)
            final_df.to_json(file_path_json, orient='columns', index=True)
            # reset dataframe to empty with same columns
            df = pd.DataFrame(columns=[f"Agent {i}" for i in range(10)])

# if __name__ == "__main__":
#     sm = StatisticsManager()
#     sm.define_cost(0, 10)
#     sm.define_cost_after_disruption(0, 15)
#     sm.update_fulfilled_demand(0, 10)
#     sm.update_lost_demand(0, 5)
#     sm.increment_changed_routes()
#     sm.add_dataframe(0)
#     sm.add_dataframe(1)
#     sm.add_dataframe(2)
#     sm.create_final_snapshot()
#     print(sm.final_df)
#     print(sm.routes_df)
#     # sm.save_statistics()
