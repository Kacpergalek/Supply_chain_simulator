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

## Contributors ✋
**Berenike Banek** - berenike@student.agh.edu.pl  
**Konrad Ćwięka** - kcwieka@student.agh.edu.pl 
**Kacper Gałek** - [email]
