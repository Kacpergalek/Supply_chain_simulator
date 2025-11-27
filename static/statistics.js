// Helper: map dataset => output endpoint
const GRAPH_ENDPOINTS = {
    'fulfilled': '/api/fulfilled_demand_stats',
    'lost': '/api/lost_demand_stats',
    'cost': '/api/cost_stats',
    'loss': '/api/loss_stats',
    'final': '/api/final_stats'
};

async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Fetch failed: ' + res.status);
    return await res.json();
}

function renderPrettyJson(containerSelector, dataObj) {
    const container = document.querySelector(containerSelector);
    container.innerHTML = '';
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(dataObj, null, 2);
    container.appendChild(pre);
}

function jsonTimeseriesToWideCsv(obj) {
    // obj: { "Agent 0": {"0": 0.0, "1": 1.2}, "Agent 1": {...} }
    // produce CSV with header: Agent 0,Agent 1,... and rows ordered by numeric time index
    const agents = Object.keys(obj);
    // gather all time keys
    const timeSet = new Set();
    agents.forEach(agent => {
        const series = obj[agent] || {};
        Object.keys(series).forEach(t => timeSet.add(t));
    });
    // sort times numerically
    const times = Array.from(timeSet).map(t => Number(t)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b);
    // if there were non-numeric keys (unlikely), include them in insertion order after numeric
    const nonNumeric = Array.from(timeSet).filter(t => Number.isNaN(Number(t)));
    const allTimes = times.map(String).concat(nonNumeric);

    const rows = [];
    // header: agents only (no time column) to match saved_statistics format
    rows.push(agents.join(','));

    allTimes.forEach(time => {
        const row = agents.map(agent => {
            const series = obj[agent] || {};
            const v = series[time];
            return v === undefined ? '' : String(v);
        });
        rows.push(row.join(','));
    });

    return rows.join('\n');
}

async function displayData(dataset, format) {
    const endpoint = GRAPH_ENDPOINTS[dataset];
    if (!endpoint) {
        document.querySelector('#stats').textContent = 'Dataset not available';
        return;
    }
    try {
        const data = await fetchJson(endpoint);
        window.latestRawData = { source: 'graph', dataset, format, data };
        if (format === 'json') {
            renderPrettyJson('#stats', data);
        } else {
            // csv (wide format matching saved_statistics)
            const csv = jsonTimeseriesToWideCsv(data);
            document.querySelector('#stats').innerHTML = `<pre>${csv}</pre>`;
        }
    } catch (err) {
        console.error(err);
        document.querySelector('#stats').textContent = 'Failed to load data: ' + err.message;
    }
}

// initialize format toggle (button shows the alternative format)
window.currentFormat = window.currentFormat || 'json';
const formatToggleBtn = document.getElementById('format-toggle-btn');
function updateFormatButton() {
    // if button is not present on this page, silently skip updating
    if (!formatToggleBtn) return;
    const alt = window.currentFormat === 'json' ? 'csv' : 'json';
    formatToggleBtn.textContent = '.' + alt;
}
// initialize only if element exists
if (formatToggleBtn) {
    updateFormatButton();
    formatToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        // toggle current format
        window.currentFormat = window.currentFormat === 'json' ? 'csv' : 'json';
        updateFormatButton();
        // re-render currently displayed content immediately
        displayData(window.latestRawData.dataset, window.currentFormat);
    });
}

displayData(document.getElementById('dataset-select').value, window.currentFormat || 'json');

document.getElementById('download-stats').addEventListener('click', function (event) {
    event.preventDefault();
    const obj = window.latestRawData;
    if (!obj) {
        alert('No data loaded to download. Click Display first.');
        return;
    }

    if (obj.format === 'json') {
        const jsonText = JSON.stringify(obj.data, null, 2);
        const blob = new Blob([jsonText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${obj.dataset}_${obj.source}.json`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
    } else {
        // csv
        let csv;
        if (typeof obj.data === 'string') csv = obj.data;
        else csv = jsonTimeseriesToWideCsv(obj.data);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${obj.dataset}_${obj.source}.csv`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
    }
});

document.getElementById('dataset-select').addEventListener('change', function (event) {
    displayData(event.target.value, window.currentFormat || 'json');
});