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
}

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

// 🔹 Odświeżanie obrazu mapy co 5 sekund
/*
function refreshMap() {
    const iframe = document.querySelector('.map-section iframe');
    if (!iframe) return;
    const timestamp = new Date().getTime();  // cache-buster
    iframe.src = `/static/latest_map.html?${timestamp}`;
}

// odświeżanie co 5 sekund
setInterval(refreshMap, 5000);*/
