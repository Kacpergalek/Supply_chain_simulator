import pandas as pd
import os 
from datetime import datetime
import plotly.io as pio
import plotly.graph_objs as go

class DashboardsManager():
    def __init__(self):
        pass


    def get_stats(self):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = os.path.join(path, "saved_statistics")
        files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
        dt_now = datetime.now()

        min_time = float("inf")
        full_path = ""
        for file in files:
            str_time = file[6:26]
            file_dt = datetime.strptime(str_time, "%d_%m_%Y__%H_%M_%S")
            diff = abs((dt_now - file_dt).total_seconds())
            if min_time > diff:
                min_time = diff
                full_path = os.path.join(path, file)
        if full_path == "":
            raise Exception("There is no data")
        df = pd.read_csv(full_path)
        return df

            


    def fulfilled_loss_demand(self):
        df = self.get_stats()
        fulfilled_demand = []
        loss_demand = []
        for col in df.columns:
            if col.endswith("fulfilled_demand"):
                total = df[col].sum()
                fulfilled_demand.append(total)
            elif col.endswith("loss_demand"):
                total = df[col].sum()
                loss_demand.append(total)

        return fulfilled_demand, loss_demand


    def demand_scatter(self):
        fulfilled_demand, loss_demand = self.fulfilled_loss_demand()
        timesteps = list(range(1, len(fulfilled_demand) + 1))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timesteps,
            y=fulfilled_demand,
            mode='lines+markers',
            name='Fulfilled Demand',
            line=dict(color='green')
        ))

        fig.add_trace(go.Scatter(
            x=timesteps,
            y=loss_demand,
            mode='lines+markers',
            name='Loss Demand',
            line=dict(color='red')
        ))

        fig.update_layout(
            title="Fulfilled vs Loss Demand over Timesteps",
            xaxis_title="Current Timestep",
            yaxis_title="Demand Value",
            template="plotly_white"
        )

        return fig
    
    def demand_bar_graph(self):
        fulfilled_demand, loss_demand = self.fulfilled_loss_demand()
        timesteps = list(range(1, len(fulfilled_demand) + 1))
        
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=timesteps,
            y=fulfilled_demand,
            name="Fulfilled Demand",
            marker_color="green"
        ))

        fig.add_trace(go.Bar(
            x=timesteps,
            y=loss_demand,
            name="Loss Demand",
            marker_color="red"
        ))


        fig.update_layout(
            title="Fulfilled vs Loss Demand per Timestep",
            xaxis_title="Timestep",
            yaxis_title="Demand Value",
            barmode="group",  # obok siebie (można zmienić na 'stack' dla nakładania)
            template="plotly_white"
        )
        return fig