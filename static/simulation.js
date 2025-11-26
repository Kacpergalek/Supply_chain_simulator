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
        appendLog(e.data);
    };
    evtSource.onerror = function (e) {
        appendLog('Connection to log stream lost');
        evtSource.close();
    };
}

manageLogs();

//  Odświeżanie obrazu mapy co 5 sekund
function refreshMap() {
    const img = document.querySelector('.map-section img');
    if (!img) return;
    const timestamp = new Date().getTime();  // cache-buster
    img.src = `/assets/latest_map.png?${timestamp}`;
}

// odświeżanie co 5 sekund
setInterval(refreshMap, 5000);

// document.getElementById('statistics-btn').addEventListener('click', function (event) {
//     window.location.href = '/category/statistics';
// });

