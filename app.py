import pickle

from flask import Flask, render_template, jsonify, send_from_directory, request
from pathlib import Path
import json

app = Flask(__name__)

RESULTS_PATH = Path('form_data')

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/disruption_type")
def jsonify_types():
    return jsonify(json.loads((RESULTS_PATH / "disruption_type.json").read_text()))

@app.route("/api/disruption_severity")
def jsonify_severity():
    return jsonify(json.loads((RESULTS_PATH / "disruption_severity.json").read_text()))

@app.route("/api/duration")
def jsonify_nduration():
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


if __name__ == "__main__":
    app.run(debug=True)