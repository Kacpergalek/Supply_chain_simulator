import datetime
import os
import pickle
import sys
import logging
import queue
import time

from flask import Flask, render_template, jsonify, send_from_directory, request, url_for, Response, stream_with_context
from pathlib import Path
import json
import plotly.io as pio
import plotly.graph_objs as go
from dashboard.dashboards_manager import DashboardsManager
from models.simluation_engine.engine import Simulation
from network.graph_reader import GraphManager
from network.countries import europe_countries
import threading
from network.empty_visualization import plot_empty_map

app = Flask(__name__)
dash_manager = DashboardsManager()
plot_empty_map()
RESULTS_PATH = Path('form_data')
STATS_PATH = Path('saved_statistics')
ASSETS_DIR = Path(__file__).parent / "assets"
# reader = GraphManager()
# map = {}
# for country in europe_countries:
#     graph = reader.load_pickle_graph(f"{country}_motorway.pkl")
#     if graph:
#         map[country] = graph



# --- Logging queue + SSE setup ---
log_queue = queue.Queue()


class QueueLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put(msg)
        except Exception:
            pass


# attach handler to root logger so logs from modules are captured
handler = QueueLogHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
sim = Simulation()

# Filter handler so only simulation-related records are queued


class SimulationFilter(logging.Filter):
    def filter(self, record):
        # accept records from the simulation engine module or from the
        # temporary 'simulation_stream' logger used to capture print()
        name = getattr(record, "name", "")
        return name.startswith("models.simluation_engine") or name == "simulation_stream"


handler.addFilter(SimulationFilter())

# Also print logs to the original stdout so Flask/Werkzeug startup messages
# and other logs remain visible in the terminal.
console_handler = logging.StreamHandler(stream=sys.__stdout__)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)


class StreamToLogger:
    """Fake file-like stream that redirects writes to logging"""

    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, msg):
        msg = msg.rstrip('\n')
        if msg:
            self.logger.log(self.level, msg)

    def flush(self):
        pass

# NOTE: we do NOT redirect global stdout here. We'll redirect stdout/stderr
# only inside the simulation thread so only simulation prints are captured.


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/category/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.route('/events')
def events():
    def stream():
        while True:
            try:
                msg = log_queue.get(timeout=1.0)
                # SSE data field
                yield f"data: {msg}\n\n"
            except queue.Empty:
                # keep-alive comment
                yield ': keep-alive\n\n'

    return Response(stream_with_context(stream()), mimetype='text/event-stream')


@app.route("/category/graph")
def graph():
    image_url = url_for('assets', filename='latest_map.png')
    return render_template("graph.html", image=image_url)

@app.route("/category/comparison")
def comparison():
    return render_template("comparison.html")


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

@app.route("/api/cost_stats")
def jsonify_cost_stats():
    data = None
    for file in os.listdir(STATS_PATH):
        if file.endswith('.json') and file.startswith('stats'):
            data = json.loads((STATS_PATH / file).read_text())

    if data is None:
        return jsonify({}), 404

    return jsonify(data)

@app.route("/api/demand_stats")
def jsonify_demand_stats():
    data = None
    for file in os.listdir(STATS_PATH):
        if file.endswith('.json') and file.startswith('demand'):
            data = json.loads((STATS_PATH / file).read_text())

    if data is None:
        return jsonify({}), 404

    return jsonify(data)

@app.route("/api/route_stats")
def jsonify_route_stats():
    data = None
    for file in os.listdir(STATS_PATH):
        if file.endswith('.json') and file.startswith('route'):
            data = json.loads((STATS_PATH / file).read_text())

    if data is None:
        return jsonify({}), 404

    return jsonify(data)


@app.route('/api/stats/download')
def download_latest_stats():
    # return the latest JSON file as an attachment for download
    latest_file = None
    latest_dt = None
    for file in os.listdir(STATS_PATH):
        if not file.endswith('.json'):
            continue
        name = file.replace('.json', '')
        try:
            ts = name.split('stats_')[-1]
            dt = datetime.strptime(ts, "%d_%m_%Y__%H_%M_%S")
        except Exception:
            continue
        if latest_dt is None or dt > latest_dt:
            latest_dt = dt
            latest_file = file

    if latest_file is None:
        return jsonify({}), 404

    return send_from_directory(STATS_PATH, latest_file, as_attachment=True)


@app.route('/api/process', methods=['POST'])
def process():
    # sim.reset()
    data = request.get_json()

    with open('parameters/disruption_parameters.pkl', 'wb') as f:
        pickle.dump(data, f)

    return jsonify(data)


@app.route("/category/dashboard/api/process", methods=["POST"])
def dashboard_process():
    data = request.get_json()

    # print("Received disruption data from dashboard:\n", data)
    with open('parameters/disruption_parameters.pkl', 'wb') as f:
        pickle.dump(data, f)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=['2025-11-01', '2025-11-02', '2025-11-03'],
                             y=[100, 150, 200],
                             mode='lines+markers',
                             name='Sales'))

    return jsonify(fig.to_dict())


@app.route('/api/graph', methods=['POST'])
def simulation():
    data = request.get_json()
    start_flag = False
    if isinstance(data, dict):
        start_flag = bool(data.get("start", False))

    # app.logger.info("Start simulation? %s", start_flag)

    if start_flag:
        def run_simulation():
            # redirect stdout/stderr to a dedicated simulation logger so
            # only outputs from the simulation are queued and streamed
            sim_logger = logging.getLogger('simulation_stream')
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            sys.stdout = StreamToLogger(sim_logger, level=logging.INFO)
            sys.stderr = StreamToLogger(sim_logger, level=logging.ERROR)
            try:
                # sim = Simulation(max_time=15, time_resolution="day")
                sim.inject_parameters(max_time=15, time_resolution="day")
                sim.run()
            except Exception as e:
                app.logger.exception("Simulation failed: %s", e)
            finally:
                # restore original streams
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

        thread = threading.Thread(target=run_simulation, daemon=True)
        thread.start()
        return jsonify({"message": "Simulation started successfully. Please wait."}), 200

    return jsonify({"message": "No action taken"}), 400


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
