async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Fetch failed: ' + res.status);
    return await res.json();
}

async function plotAggregationGraph(appRoute, query, agg_type) {

    const container = document.querySelector(query);
    container.innerHTML = '';

    try {
        const data = await fetchJson(appRoute);
        const fulfilled = data[`${agg_type}_fulfilled_demand`];
        const lost = data[`${agg_type}_lost_demand`];
        const cost = data[`${agg_type}_cost`];
        const loss = data[`${agg_type}_loss`];

        function normalizeSeries(s) {
            // if it's already an object with x/y
            if (!s) return {x: [], y: []};
            if (Array.isArray(s)) {
                const y = s.map(v => (v === null || v === undefined) ? null : Number(v));
                const x = y.map((_, i) => i + 1); // 1-based day index
                return {x, y};
            }
            if (typeof s === 'object') {
                // assume mapping time->value
                const times = Object.keys(s).map(k => Number(k)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b);
                if (times.length > 0) {
                    const x = times;
                    const y = times.map(t => s[String(t)]);
                    return {x, y};
                }
                // fallback: try to extract values
                const vals = Object.values(s).map(v => Number(v));
                const x = vals.map((_, i) => i + 1);
                return {x, y: vals};
            }
            return {x: [], y: []};
        }

        const flf = normalizeSeries(fulfilled);
        const lst = normalizeSeries(lost);
        const cst = normalizeSeries(cost);
        const lss = normalizeSeries(loss);

        const w1 = document.createElement('div');
        w1.className = 'chart-wrapper';
        w1.id = `${agg_type}-demand-chart`;
        // inline sizing to match other pages
        w1.style.width = '90%';
        w1.style.maxWidth = '1000px';
        w1.style.minHeight = '360px';
        w1.style.background = 'transparent';
        container.appendChild(w1);

        const w2 = document.createElement('div');
        w2.className = 'chart-wrapper';
        w2.id = `${agg_type}-cost-chart`;
        w2.style.width = '90%';
        w2.style.maxWidth = '1000px';
        w2.style.minHeight = '360px';
        w2.style.background = 'transparent';
        container.appendChild(w2);

        const w3 = document.createElement('div');
        w3.className = 'chart-wrapper';
        w3.id = `${agg_type}-loss-chart`;
        w3.style.width = '90%';
        w3.style.maxWidth = '1000px';
        w3.style.minHeight = '360px';
        w3.style.background = 'transparent';
        container.appendChild(w3);

        // green palette
        const trace1 = {x: flf.x, y: flf.y, mode: 'lines+markers', name: 'Fulfilled', line: {color: '#08A045'}};
        const trace2 = {x: lst.x, y: lst.y, mode: 'lines+markers', name: 'Lost', line: {color: '#0B6E4F'}};
        const layout1 = {
            title: 'Fulfilled vs lost demand',
            xaxis: {title: 'day'},
            yaxis: {title: 'value'},
            legend: {orientation: 'h', x: 0.5, xanchor: 'center'},
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: {t: 50}
        };
        Plotly.newPlot(`${agg_type}-demand-chart`, [trace1, trace2], layout1, {responsive: true});

        const trace3 = {x: cst.x, y: cst.y, mode: 'lines+markers', name: 'Cost', line: {color: '#21D375'}};
        const layout2 = {
            title: 'Cost',
            xaxis: {title: 'day'},
            yaxis: {title: 'value'},
            legend: {orientation: 'h', x: 0.5, xanchor: 'center'},
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: {t: 50}
        };
        Plotly.newPlot(`${agg_type}-cost-chart`, [trace3], layout2, {responsive: true});

        const trace4 = {x: lss.x, y: lss.y, mode: 'lines+markers', name: 'Loss', line: {color: '#6BBF59'}};
        const layout3 = {
            title: 'Loss',
            xaxis: {title: 'day'},
            yaxis: {title: 'value'},
            legend: {orientation: 'h', x: 0.5, xanchor: 'center'},
            plot_bgcolor: '#f5f5f5',
            paper_bgcolor: 'transparent',
            margin: {t: 50}
        };
        Plotly.newPlot(`${agg_type}-loss-chart`, [trace4], layout3, {responsive: true});

        // ensure container is centered and spaced and pushed below navbar
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

// window.currentFormat = window.currentFormat || 'Average';
// const formatToggleBtn = document.getElementById('format-toggle-btn');
//
// function updateFormatButton() {
//     // if button is not present on this page, silently skip updating
//     if (!formatToggleBtn) return;
//     formatToggleBtn.textContent = window.currentFormat === 'Average' ? 'Sum' : 'Average';
// }
//
// // initialize only if element exists
// if (formatToggleBtn) {
//     updateFormatButton();
//     formatToggleBtn.addEventListener('click', function (e) {
//         e.preventDefault();
//         // toggle current format
//         window.currentFormat = window.currentFormat === 'Average' ? 'Sum' : 'Average';
//         updateFormatButton();
//     });
// }
//
// async function plotGraph(format) {
//     if (format === 'Average') {
//         plotAggregationGraph("/api/average_stats", '#average', "avg");
//     } else if (format === 'Sum') {
//         plotAggregationGraph("/api/sum_stats", '#sum', "sum");
//     }
// }
//
// document.addEventListener('DOMContentLoaded', () => {
//     plotGraph(window.currentFormat);
// });

document.addEventListener('DOMContentLoaded', () => {
    // 1. Select elements safely inside DOMContentLoaded
    const formatToggleBtn = document.getElementById('format-toggle-btn');
    const avgContainer = document.getElementById('average');
    const sumContainer = document.getElementById('sum');

    // Default state
    window.currentFormat = 'Average';

    async function updateUI() {
        // 2. Logic to show/hide containers and update button text
        if (window.currentFormat === 'Average') {
            // Show Average, Hide Sum
            avgContainer.style.display = 'block';
            sumContainer.style.display = 'none';
            formatToggleBtn.textContent = 'Sum'; // Offer option to switch to Sum

            // Render if empty (or re-render to be safe)
            await plotAggregationGraph("/api/average_stats", '#average', "avg");
        } else {
            // Show Sum, Hide Average
            avgContainer.style.display = 'none';
            sumContainer.style.display = 'block';
            formatToggleBtn.textContent = 'Average'; // Offer option to switch to Average

            await plotAggregationGraph("/api/sum_stats", '#sum', "sum"); // ensure this matches your python dict keys e.g. sum_fulfilled_demand
        }
    }

    if (formatToggleBtn) {
        // Initial load
        updateUI();

        formatToggleBtn.addEventListener('click', function (e) {
            e.preventDefault();
            // 3. Toggle state
            window.currentFormat = window.currentFormat === 'Average' ? 'Sum' : 'Average';
            // 4. Call the update function to trigger changes
            updateUI();
        });
    }
});