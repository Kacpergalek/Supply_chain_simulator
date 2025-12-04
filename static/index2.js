const nav = document.querySelector(".nav-bar-list");
const navButtons = nav.querySelectorAll("button");
const content = document.getElementById("content");
// const simulation = content.querySelector(".simulation");
const statsContainer = content.querySelector(".panel-container");

// simulation.classList.add("hidden");
statsContainer.classList.add("hidden");

navButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
        const page = btn.getAttribute("data-page");

        content.querySelectorAll(".content-page").forEach(page => {
            page.classList.add("hidden");
        })

        content.querySelector(`.${page}`).classList.remove("hidden");
    });
});

async function readJSON(appRoute, query) {

    const response = await fetch(appRoute);
    const data = await response.json();

    const select = document.querySelector(query);
    select.innerHTML = "";

    data.forEach(word => {
        const option = document.createElement("option");
        option.innerHTML = `<option>${word}</option>`;
        select.appendChild(option);
    });
}

readJSON("/api/disruption_type", "#disruptionType");
readJSON("/api/disruption_severity", "#severity");
readJSON("/api/duration", "#duration");
readJSON("/api/day_of_start", "#dayOfStart");
readJSON("/api/place_of_disruption", "#placeOfDisruption");

const baseUrl = window.location.pathname;

function sendData() {
    console.log("Sending simulation parameters.")
    var text = "";
    var dict = {}
    var listOfForms = ["disruptionType", "severity", "duration", "dayOfStart", "placeOfDisruption"];
    for (index in listOfForms) {

        var e = document.getElementById(listOfForms[index]);
        text += e.options[e.selectedIndex].text;
        dict[listOfForms[index]] = e.options[e.selectedIndex].text;
    }

    $.ajax({
        url: '/api/process',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(dict),
        success: function (response) {
            alert("Data submitted successfully.")
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
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({start: true})
    })
        .then(response => response.json().then(body => ({status: response.status, body})))
        .then(({status, body}) => {
            const msg = body.message || JSON.stringify(body)
            // const el = document.getElementById('response')
            // el.innerText = msg
            alert(msg);
        })
        .catch(err => {
            document.getElementById('response').innerText = 'Error starting simulation'
            console.error(err)
        })

    let goToStatisticsBtn = document.getElementById('go-to-stat');
    goToStatisticsBtn.disabled = false;
}

function goToStatistics() {
    window.location.href = '/category/statistics';
}

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
            const iframe = document.querySelector('.map-section iframe');
            if (iframe) {
                const timestamp = new Date().getTime();
                iframe.src = `/static/latest_map.html?t=${timestamp}`;
            }
        }

        if (!firstLogReceived) firstLogReceived = true;

    };
    evtSource.onerror = function (e) {
        appendLog('Connection to log stream lost');
        evtSource.close();
    };
}

manageLogs();

//  Odświeżanie obrazu mapy co 5 sekund
/*
function refreshMap() {
    const img = document.querySelector('.map-section img');
    if (!img) return;
    const timestamp = new Date().getTime();  // cache-buster
    img.src = `/assets/latest_map.png?${timestamp}`;
}

// odświeżanie co 5 sekund
setInterval(refreshMap, 5000);
*/
// document.getElementById('statistics-btn').addEventListener('click', function (event) {
//     window.location.href = '/category/statistics';
// });

