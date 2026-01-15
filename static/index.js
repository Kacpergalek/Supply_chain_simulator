async function readJSON(appRoute, query) {

    const response = await fetch(appRoute);
    const data = await response.json();

    const select = document.querySelector(query);
    select.innerHTML = "";

    if (Array.isArray(data)) {
        data.forEach(word => {
            const option = document.createElement("option");
            option.value = word;
            option.textContent = word;
            select.appendChild(option);
        });
    }

    else if (typeof data === 'object' && data !== null) {
        Object.entries(data).forEach(([id, city]) => {
            const option = document.createElement("option");
            option.value = id;
            option.textContent = city;
            select.appendChild(option);
        });
    }
}


readJSON("/api/disruption_type", "#disruptionType");
readJSON("/api/disruption_severity", "#severity");
readJSON("/api/place_of_disruption", "#placeOfDisruption");

function sendData() {
    console.log("Sending simulation parameters.")
    var dict = {}

    // Get values from form elements
    var disruptionType = document.getElementById("disruptionType");
    var severity = document.getElementById("severity");
    var disruptionDuration = document.getElementById("disruptionDuration");
    var simulationDuration = document.getElementById("simulationDuration");
    var dayOfStart = document.getElementById("dayOfStart");
    var placeOfDisruption = document.getElementById("placeOfDisruption");

    // For select elements, use .value. For input elements, also use .value
    if (disruptionType) {
        dict["disruptionType"] = disruptionType.options ? disruptionType.options[disruptionType.selectedIndex].value : disruptionType.value;
    }
    if (severity) {
        dict["severity"] = severity.options ? severity.options[severity.selectedIndex].value : severity.value;
    }
    if (disruptionDuration) {
        dict["disruptionDuration"] = disruptionDuration.value;
    }
    if (simulationDuration) {
        dict["simulationDuration"] = simulationDuration.value;
    }
    if (dayOfStart) {
        dict["dayOfStart"] = dayOfStart.value;
    }
    if (placeOfDisruption) {
        dict["placeOfDisruption"] = placeOfDisruption.options ? placeOfDisruption.options[placeOfDisruption.selectedIndex].value : placeOfDisruption.value;
    }



    $.ajax({
        url: '/api/process',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(dict),
        success: async function (response) {
            await new Promise(r => setTimeout(r, 500));
            alert("Data submitted successfully. You can start the simulation")
            // document.getElementById('output').innerHTML = JSON.stringify(response, null, 2);
        },
        error: function (error) {
            console.log(error);
        }
    });
}

function startSimulation() {
    fetch('/api/graph', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start: true })
    })
        .then(response => response.json().then(body => ({ status: response.status, body })))
        .then(({ status, body }) => {
            const msg = body.message || JSON.stringify(body)
            // const el = document.getElementById('response')
            // el.innerText = msg
            alert(msg);
        })
        .catch(err => {
            document.getElementById('response').innerText = 'Error starting simulation'
            console.error(err)
        })
}

function goToStatistics() {
    window.location.href = '/category/statistics';
}

document.getElementById('go-to-stat').addEventListener('click', goToStatistics);

const map = L.map('map').setView([49.5, 15.5], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let graphNodes = {};
let routeLayers = [];
let exporterMarkers = [];
let importerMarkers = [];
let disruptedMarkers = [];
let highlightMarker = null;
let lastRoutes = [];

// 1. Pobierz bazowe dane edges + nodes
Promise.all([
    fetch('/api/edges').then(r => r.json()),
    fetch('/api/nodes').then(r => r.json())
]).then(([edges, nodes]) => {
    graphNodes = nodes;

    console.log("✅ Bazowa sieć dróg załadowana.");
    fetch('/api/map_state')
        .then(res => res.json())
        .then(state => updateMap(state))
        .catch(err => console.error("❌ Błąd pobierania map_state:", err));
});

// 2. Aktualizacja dynamicznych warstw
function updateMap(state) {
    console.log("Routes przy update:", state.routes);

    //routeLayers.forEach(l => map.removeLayer(l));
    exporterMarkers.forEach(m => map.removeLayer(m));
    importerMarkers.forEach(m => map.removeLayer(m));
    disruptedMarkers.forEach(m => map.removeLayer(m));

    //routeLayers = [];
    exporterMarkers = [];
    importerMarkers = [];
    disruptedMarkers = [];

    function getColor(i, total) {
        const hue = (i * (360 / total)) % 360;
        return `hsl(${hue}, 60%, 55%)`;
    }

    // trasy agentów
    state.routes.forEach((path, i) => {
        const coords = path.filter(n => graphNodes[n])
            .map(n => [graphNodes[n].y, graphNodes[n].x]);
        const oldPath = lastRoutes[i];
        const changed = !oldPath || JSON.stringify(oldPath) !== JSON.stringify(path);

        if (changed && coords.length >= 2) {
            // jeśli istnieje stara warstwa, usuń ją
            if (routeLayers[i]) {
                map.removeLayer(routeLayers[i]);
            }

            let drawnCoords = [];
            let polyline = null;
            let step = 0;

            const interval = setInterval(() => {
                if (step >= coords.length) {
                    clearInterval(interval);
                    return;
                }

                drawnCoords.push(coords[step]);
                step++;

                if (polyline) map.removeLayer(polyline);
                polyline = L.polyline(drawnCoords, {
                    color: getColor(i, state.routes.length),
                    weight: 3
                }).addTo(map);

                routeLayers[i] = polyline; // 🔧 ZMIANA – zapisujemy warstwę pod indeksem
            }, 5);
        }
    });

    // 🔧 ZMIANA – zapamiętujemy aktualne trasy
    lastRoutes = state.routes.map(r => [...r]);

    // eksporterzy
    state.exporters.forEach(n => {
        if (graphNodes[n]) {
            const marker = L.circleMarker([graphNodes[n].y, graphNodes[n].x], {
                radius: 6, color: "green", fillColor: "green", fillOpacity: 1
            }).bindTooltip(graphNodes[n].city || "Exporter").addTo(map);
            exporterMarkers.push(marker);
        }
    });

    // importerzy
    state.importers.forEach(n => {
        if (graphNodes[n]) {
            const marker = L.circleMarker([graphNodes[n].y, graphNodes[n].x], {
                radius: 6, color: "red", fillColor: "red", fillOpacity: 1
            }).bindTooltip(graphNodes[n].city || "Importer").addTo(map);
            importerMarkers.push(marker);
        }
    });
    // importer-exporter (pomarańczowy)
    state.both.forEach(n => {
        if (graphNodes[n]) {
            const marker = L.circleMarker([graphNodes[n].y, graphNodes[n].x], {
                radius: 7,
                color: "orange",
                fillColor: "orange",
                fillOpacity: 1
            }).bindTooltip(graphNodes[n].city || "Importer/Exporter").addTo(map);
            importerMarkers.push(marker);
        }
    });

    // disrupted nodes
    state.disrupted.forEach(n => {
        if (graphNodes[n]) {
            const marker = L.marker([graphNodes[n].y, graphNodes[n].x], {
                icon: L.divIcon({ html: "<b style='color:black'>X</b>", className: '' })
            }).bindTooltip("Disrupted").addTo(map);
            disruptedMarkers.push(marker);
        }
    });

    console.log("✅ Mapa zaktualizowana.");
}

// 3. Highlight node (formularz)
function highlightNode(nodeId) {
    if (highlightMarker) map.removeLayer(highlightMarker);
    const n = graphNodes[nodeId];
    if (!n) return;
    highlightMarker = L.circleMarker([n.y, n.x], {
        radius: 8, color: "yellow", fillColor: "yellow", fillOpacity: 1
    }).bindTooltip("Selected node").addTo(map);
}

document.querySelector("#placeOfDisruption").addEventListener("change", function () {
    let nodeId = parseInt(this.value);          // 🔥 poprawka 1: zawsze liczba
    const node = graphNodes[String(nodeId)];    // 🔥 poprawka 2: zawsze poprawny klucz

    if (!node) return;

    if (highlightMarker) map.removeLayer(highlightMarker);

    highlightMarker = L.circleMarker([node.y, node.x], {
        radius: 8,
        color: "yellow",
        fillColor: "yellow",
        fillOpacity: 1
    }).bindTooltip("Selected node").addTo(map);
});

async function manageLogs() {
    // open SSE connection for real-time logs
    const loggerEl = document.getElementById('logger');

    function appendLog(text) {
        const p = document.createElement('div');
        p.textContent = text;
        loggerEl.appendChild(p);
        // auto-scroll to bottom
        loggerEl.scrollTop = loggerEl.scrollHeight;
    }

    let firstLogReceived = false;
    const evtSource = new EventSource('/events');
    evtSource.onmessage = function (e) {
        // e.data contains one log line
        //appendLog(e.data);
        const msg = e.data;
        appendLog(msg);

        // >>> DODANE: jeśli backend wysłał MAP_UPDATE, odśwież iframe
        if (msg.includes("MAP_UPDATE")) {

            fetch('/api/map_state')
                .then(res => res.json())
                .then(state => updateMap(state))
                .catch(err => console.error("❌ Błąd pobierania map_state:", err));
        }

        if (!firstLogReceived) firstLogReceived = true;

    };
    evtSource.onerror = function (e) {
        appendLog('Connection to log stream lost');
        evtSource.close();
    };
}
// === 🔥 Aktualizacja mapy po wyborze węzła ===

// =========================== SLIDE-IN LOG PANEL =============================

const toggleBtn = document.getElementById("log-panel-toggle");
const logPanel = document.getElementById("log-panel");

toggleBtn.addEventListener("click", () => {
    const isOpen = logPanel.classList.contains("open");
    if (isOpen) {
        logPanel.classList.remove("open");
        toggleBtn.textContent = "Logs ▼";
    } else {
        logPanel.classList.add("open");
        toggleBtn.textContent = "Logs ▲";
    }
});

manageLogs();

/* ========================== Slider Value Updates ========================== */

// Update slider display values
const simulationDurationSlider = document.getElementById('simulationDuration');
const severitySlider = document.getElementById('severity');
const disruptionDurationSlider = document.getElementById('disruptionDuration');

if (simulationDurationSlider) {
    simulationDurationSlider.addEventListener('input', function () {
        document.getElementById('simulationDurationValue').textContent = this.value;
    });
}

if (severitySlider) {
    severitySlider.addEventListener('input', function () {
        document.getElementById('severityValue').textContent = parseFloat(this.value).toFixed(2);
    });
}

if (disruptionDurationSlider) {
    disruptionDurationSlider.addEventListener('input', function () {
        document.getElementById('disruptionDurationValue').textContent = this.value;
    });
}

/* ========================== Number Input Functions ========================== */

function incrementDayOfStart() {
    const input = document.getElementById('dayOfStart');
    input.value = parseInt(input.value) + 1;
}

function decrementDayOfStart() {
    const input = document.getElementById('dayOfStart');
    const newValue = parseInt(input.value) - 1;
    if (newValue >= parseInt(input.min)) {
        input.value = newValue;
    }
}
