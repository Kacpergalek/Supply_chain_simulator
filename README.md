# Supply Chain Disruption Simulation

## Project goal 🎯

The goal of the project is to construct an interactive simulation of trade flows on a world map to show how
disruptions (e.g., natural disasters, wars, transport blockages) affect supply chains, and then propose and compare
strategies to minimize losses (e.g., rerouting, buffers, alternative suppliers).

## Key features 🔑

* **Spatial modeling** - the program will have a built-in point grid based on real-world OpenStreetMap geographic data.
* **Agent system** - the project will utilize an AB model, with agent classes representing different types of nodes – raw material suppliers, goods sellers, and import points.
* **Flow** - goods can flow out of or into each node. Both nodes and edges will have all the attributes defined necessary to create a delivery path and calculate the flow cost.
* **Disruptions** - a reduction in the capacity of an edge or node, resulting in delayed deliveries or incomplete demand, and suppliers suffering losses.
* **Results analysis** - we compare scenarios and various methods for minimizing losses.

## Monitored metrics 📈
* **Fulfilled demand** to **lost demand**
* **Delivery time** before and after the disruption
* Company **losses**
* Heatmap of **nodes** and **edges** that are **most sensitive** to disruptions

## Setup Instructions 🔧

### 1. Clone the repository

```bash
git clone <repository-url>
cd Supply_Chain_Simulator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application 🏃

### 1. Run the program and wait for it to initialize

```bash
python app.py
```
The application will be available at `http://localhost:5173`

### 2. Tune parameters and submit the form

### 3. Start the simulation

### 4. Check out the results

## Changing internal parameters 🪛

### Changing agent localization
Go to "data/input_data/agent_data/agent_localization_data" and pick which cities you want to use.
You can choose any city from the available countries in Europe, since global cities are only connected via airports.

### Adding cities
You can choose any city from the available countries in Europe. If you want to select a city to be an exporter you must search for factory or
retail store data in that city. Delete .pkl files from "data/input_data/store_data" or "data/input_data/factory_data" and run
the program. It's going to take a while to load all the data.

## File structure 📝
work in progress

## Contributors ✋
**Berenike Banek** - berenike@student.agh.edu.pl  
**Konrad Ćwięka** - kcwieka@student.agh.edu.pl  
**Kacper Gałek** - kagalek@student.agh.edu.pl
