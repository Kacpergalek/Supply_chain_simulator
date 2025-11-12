import os
import pickle

from flask import Flask, render_template, jsonify, send_from_directory, request
from pathlib import Path
import json
import plotly.io as pio
import plotly.graph_objs as go
from dashboard.dashboards_manager import DashboardsManager

app = Flask(__name__)
dash_manager = DashboardsManager()

RESULTS_PATH = Path('form_data')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/category/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/map")
def map():
    # full_filename = os.path.join(app.config['assets'], 'lastest_map2.png')
    path = Path(__file__).parent
    file_path = f'{path}\\assets\\latest_map2.png'
    print(file_path)
    return render_template("map.html", image=file_path)


@app.route("/api/disruption_type")
def jsonify_types():
    return jsonify(json.loads((RESULTS_PATH / "disruption_type.json").read_text()))

@app.route("/api/disruption_severity")
def jsonify_severity():
    return jsonify(json.loads((RESULTS_PATH / "disruption_severity.json").read_text()))

@app.route("/api/duration")
def jsonify_duration():
    return jsonify(json.loads((RESULTS_PATH / "duration.json").read_text()))

@app.route("/api/day_of_start")
def jsonify_start_day():
    return jsonify(json.loads((RESULTS_PATH / "day_of_start.json").read_text()))

@app.route("/api/place_of_disruption")
def jsonify_place():
    return jsonify(json.loads((RESULTS_PATH / "place_of_disruption.json").read_text()))


@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json()

    print("Received disruption data:\n", data)
    with open('parameters/disruption_parameters.pkl', 'wb') as f:
        pickle.dump(data, f)

    return jsonify(data)


@app.route("/category/dashboard/api/process", methods=["POST"])
def dashboard_process():
    data = request.get_json()

    print("Received disruption data from dashboard:\n", data)
    with open('parameters/disruption_parameters.pkl', 'wb') as f:
        pickle.dump(data, f)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=['2025-11-01', '2025-11-02', '2025-11-03'],
                             y=[100, 150, 200],
                             mode='lines+markers',
                             name='Sales'))
    
    return jsonify(fig.to_dict())


if __name__ == "__main__":
    app.run(debug=True)