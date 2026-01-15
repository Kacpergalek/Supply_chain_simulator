const GRAPH_ENDPOINTS = {
    'fulfilled': '/api/fulfilled_demand_stats',
    'lost': '/api/lost_demand_stats',
    'cost': '/api/cost_stats',
    'loss': '/api/loss_stats',
    'time': '/api/lead_time_stats',
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

    const agents = Object.keys(obj);
    const timeSet = new Set();
    agents.forEach(agent => {
        const series = obj[agent] || {};
        Object.keys(series).forEach(t => timeSet.add(t));
    });
    const times = Array.from(timeSet).map(t => Number(t)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b);
    const nonNumeric = Array.from(timeSet).filter(t => Number.isNaN(Number(t)));
    const allTimes = times.map(String).concat(nonNumeric);
    const rows = [];
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

/* ============================ FORMAT TOGGLE ============================ */

window.currentFormat = window.currentFormat || 'json';
const formatToggleBtn = document.getElementById('format-toggle-btn');
function updateFormatButton() {
    if (!formatToggleBtn) return;
    const alt = window.currentFormat === 'json' ? 'csv' : 'json';
    formatToggleBtn.textContent = '.' + alt;
}
if (formatToggleBtn) {
    updateFormatButton();
    formatToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        window.currentFormat = window.currentFormat === 'json' ? 'csv' : 'json';
        updateFormatButton();
        displayData(window.latestRawData.dataset, window.currentFormat);
    });
}

/* ============================ DOWNLOAD STATS ============================ */

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

/* ============================= DISPLAY DATA ============================ */

displayData(document.getElementById('dataset-select').value, window.currentFormat || 'json');

/* ============================ GRAPH RENDERING ============================ */

async function plotAggregationGraph(appRoute, query, agg_type) {

    const container = document.querySelector(query);
    container.innerHTML = '';

    try {
        const data = await fetchJson(appRoute);
        const fulfilled = data[`${agg_type}_fulfilled_demand`];
        const lost = data[`${agg_type}_lost_demand`];
        const cost = data[`${agg_type}_cost`];
        const loss = data[`${agg_type}_loss`];
        const lead = data[`${agg_type}_lead_time`];

        function normalizeSeries(s) {
            // if it's already an object with x/y
            if (!s) return { x: [], y: [] };
            if (Array.isArray(s)) {
                const y = s.map(v => (v === null || v === undefined) ? null : Number(v));
                const x = y.map((_, i) => i + 1); // 1-based day index
                return { x, y };
            }
            if (typeof s === 'object') {
                // assume mapping time->value
                const times = Object.keys(s).map(k => Number(k)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b);
                if (times.length > 0) {
                    const x = times;
                    const y = times.map(t => s[String(t)]);
                    return { x, y };
                }
                // fallback: try to extract values
                const vals = Object.values(s).map(v => Number(v));
                const x = vals.map((_, i) => i + 1);
                return { x, y: vals };
            }
            return { x: [], y: [] };
        }

        const flf = normalizeSeries(fulfilled);
        const lst = normalizeSeries(lost);
        const cst = normalizeSeries(cost);
        const lss = normalizeSeries(loss);
        const ldt = normalizeSeries(lead);

        const title1 = document.createElement('h3');
        let agg_type_text;
        if (agg_type === 'avg') {
            agg_type_text = 'Average';
        } else {
            agg_type_text = 'Sum';
        }
        title1.textContent = `${agg_type_text} Demand`;
        title1.style.width = '70%';
        title1.style.textAlign = 'left';
        // container.appendChild(title1);

        const w1 = document.createElement('div');
        w1.className = 'chart-wrapper';
        w1.id = `${agg_type}-demand-chart`;
        // inline sizing to match other pages
    
        w1.style.minHeight = '360px';
        w1.style.background = 'transparent';
        container.appendChild(w1);
    

        const cap1 = document.createElement('div');
        cap1.className = 'chart-caption';
        cap1.textContent =
            'This chart shows how much demand was fulfilled versus lost over time. ' +
            'It illustrates the impact of disruptions on service level.';
        container.appendChild(cap1);

        const title2 = document.createElement('h3');
        title2.textContent = `${agg_type_text} Cost and Loss`;
        title2.style.width = '70%';
        title2.style.textAlign = 'left';
        title2.style.marginTop = '2rem';
        // container.appendChild(title2);

        const w2 = document.createElement('div');
        w2.className = 'chart-wrapper';
        w2.id = `${agg_type}-cost-loss-chart`;
       
        w2.style.minHeight = '360px';
        w2.style.background = 'transparent';
        container.appendChild(w2);
        const cap2 = document.createElement('div');
        cap2.className = 'chart-caption';
        cap2.textContent =
            'Total operational cost and additional disruption-related losses over time.';
        container.appendChild(cap2);
        const title3 = document.createElement('h3');
        title3.textContent = `${agg_type_text} Lead Time`;
        title3.style.width = '70%';
        title3.style.textAlign = 'left';
        title3.style.marginTop = '2rem';
        // container.appendChild(title3);

        const w3 = document.createElement('div');
        w3.className = 'chart-wrapper';
        w3.id = `${agg_type}-lead-time-chart`;
     
        w3.style.minHeight = '360px';
        w3.style.background = 'transparent';
        container.appendChild(w3);
        const cap3 = document.createElement('div');
        cap3.className = 'chart-caption';
        cap3.textContent =
            'Average lead time evolution reflecting delays caused by disruptions.';
        container.appendChild(cap3);
        const mode = window.currentChartStyle === 'line' ? 'lines+markers' : 'lines';
        const type = window.currentChartStyle === 'bar' ? 'bar' : undefined;

        const trace1 = { x: flf.x, y: flf.y, mode: mode, type: type, name: 'Fulfilled', line: { color: '#08A045' } };
        const trace2 = { x: lst.x, y: lst.y, mode: mode, type: type, name: 'Lost', line: { color: '#0B6E4F' } };
        const layout1 = {
            title: 'Fulfilled vs lost demand over Time',
            xaxis: { title: 'day' },
            yaxis: { title: 'value' },
            legend: { orientation: 'h', x: 0.5, xanchor: 'center' },
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: { t: 50 }
        };
        Plotly.newPlot(`${agg_type}-demand-chart`, [trace1, trace2], layout1, { responsive: true });

        const trace3 = { x: cst.x, y: cst.y, mode: mode, type: type, name: 'Cost', line: { color: '#21D375' } };
        const trace4 = { x: lss.x, y: lss.y, mode: mode, type: type, name: 'Loss', line: { color: '#6BBF59' } };
        const layout2 = {
            title: 'Cost and Additional Cost (Loss) over Time',
            xaxis: { title: 'day' },
            yaxis: { title: 'value' },
            legend: { orientation: 'h', x: 0.5, xanchor: 'center' },
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: { t: 50 }
        };
        Plotly.newPlot(`${agg_type}-cost-loss-chart`, [trace3, trace4], layout2, { responsive: true });

        const trace5 = { x: ldt.x, y: ldt.y, mode: mode, type: type, name: 'Lead time', line: { color: '#3D9970' } };
        const layout3 = {
            title: 'Lead Time over Time',
            xaxis: { title: 'Day' },
            yaxis: { title: 'Lead Time (days)' },
            legend: { orientation: 'h', x: 0.5, xanchor: 'center' },
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: { t: 50 }
        };
        Plotly.newPlot(`${agg_type}-lead-time-chart`, [trace5], layout3, { responsive: true });

        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        container.style.gap = '1rem';
        container.style.marginTop = '6rem';
    } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="color:red">Failed to render charts</div>';
    }
}

/* ============================ CHART STYLE TOGGLE ============================ */

window.currentChartStyle = window.currentChartStyle || 'Line';
const chartStyleToggleBtn = document.getElementById('chart-style-toggle-btn');
function updateChartStyleButton() {
    if (!chartStyleToggleBtn) return;
    const alt = window.currentChartStyle === 'Line' ? 'Bar' : 'Line';
    chartStyleToggleBtn.textContent = alt + " chart"
}

if (chartStyleToggleBtn) {
    chartStyleToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        window.currentChartStyle = window.currentChartStyle === 'Line' ? 'Bar' : 'Line';
        updateChartStyleButton();
        updateGraphs();
    });
}

/* ============================ AGGREGATION TOGGLE ============================ */

async function updateGraphs() {

    const avgContainer = document.getElementById('average');
    const sumContainer = document.getElementById('sum');
    if (window.currentAggragate === 'Average') {
        avgContainer.style.display = 'block';
        sumContainer.style.display = 'none';
        aggToggleBtn.textContent = 'Sum'; // Offer option to switch to Sum

        plotAggregationGraph("/api/average_stats", '#average', "avg");
    } else {
        avgContainer.style.display = 'none';
        sumContainer.style.display = 'block';
        aggToggleBtn.textContent = 'Average'; // Offer option to switch to Average

        plotAggregationGraph("/api/sum_stats", '#sum', "sum"); // ensure this matches your python dict keys e.g. sum_fulfilled_demand
    }
}

window.currentAggragate = window.currentAggragate || 'Average';
const aggToggleBtn = document.getElementById('agg-toggle-btn');
function updateAggregateButton() {
    if (!aggToggleBtn) return;
    aggToggleBtn.textContent = window.currentAggragate === 'Average' ? 'Sum' : 'Average';
}

if (aggToggleBtn) {
    updateAggregateButton();
    aggToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        window.currentAggragate = window.currentAggragate === 'Average' ? 'Sum' : 'Average';
        updateAggregateButton();
        updateGraphs();
    });
}

/* ============================ RENDER GRAPH ON LOAD ============================ */

plotAggregationGraph("/api/average_stats", '#average', "avg");

/* ============================ BACK TO SIMULATION ============================ */
document.getElementById('back-btn').addEventListener('click', function (e) {
    window.location.href = '/';
})