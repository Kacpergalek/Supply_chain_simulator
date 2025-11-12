function startSimulation() {
    fetch('/api/graph', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({start: true})
    })
        .then(response => response.json().then(body => ({status: response.status, body})))
        .then(({status, body}) => {
            const msg = body.message || JSON.stringify(body)
            const el = document.getElementById('response')
            el.innerText = msg
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
    appendLog(e.data);
};
evtSource.onerror = function (e) {
    appendLog('Connection to log stream lost');
    evtSource.close();
};