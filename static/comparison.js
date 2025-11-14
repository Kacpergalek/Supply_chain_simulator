async function readJSON(appRoute, query) {
    const response = await fetch(appRoute);
    if (!response.ok) {
        console.error('Failed to load stats', response.status);
        return null;
    }
    const data = await response.json();

    // store latest data globally for plotting
    window.latestStats = data;

    const select = document.querySelector(query);
    select.innerHTML = "";

    // data is expected to be an object with keys like 'Agent 0'
    Object.entries(data).forEach(([agentName, statsObj]) => {
        const div = document.createElement('div');
        div.className = 'agent-entry';
        let inner = `<h4>${agentName}</h4><ul>`;
        Object.entries(statsObj).forEach(([k, v]) => {
            inner += `<li><strong>${k}:</strong> ${v}</li>`;
        });
        inner += `</ul>`;
        div.innerHTML = inner;
        select.appendChild(div);
    });
    return data;
}

function getDemandStats() {
    readJSON("/api/demand_stats", "#stats");
}

function getCostStats() {
    readJSON("/api/cost_stats", "#stats");
}

function getRouteStats() {
    readJSON("/api/route_stats", "#stats");
}

function downloadJSONFile(route) {
    (async () => {
        // prefer data already loaded by readJSON
        let data = window.latestStats;
        // if (!data) {
        //     try {
        //         const resp = await fetch('/api/' + route);
        //         if (!resp.ok) {
        //             alert('No stats available to download.');
        //             return;
        //         }
        //         data = await resp.json();
        //     } catch (err) {
        //         console.error('Failed to fetch latest stats', err);
        //         alert('Failed to fetch latest stats.');
        //         return;
        //     }
        // }

        const jsonText = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonText], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = route + '.json';
        document.body.appendChild(a);
        a.click();
        // Revoke after a short delay so download starts reliably
        setTimeout(() => {
            URL.revokeObjectURL(url);
            a.remove();
        }, 1000);
    })();
}

document.getElementById("download-stats").addEventListener("click", () => {
    downloadJSONFile('stats');
});

document.getElementById("activate-btn").addEventListener("click", () => {
    const data = window.latestStats;
    if (!data) {
        alert('No stats loaded yet.');
        return;
    }

    // build arrays for agents and two metrics: fulfilled_demand and lost_demand
    const agents = [];
    const fulfilled = [];
    const lost = [];
    Object.entries(data).forEach(([agentName, stats]) => {
        agents.push(agentName);
        fulfilled.push(stats.fulfilled_demand || 0);
        lost.push(stats.lost_demand || 0);
    });

    const trace1 = {x: agents, y: fulfilled, name: 'Fulfilled Demand', type: 'bar'};
    const trace2 = {x: agents, y: lost, name: 'Lost Demand', type: 'bar'};
    const layout = {barmode: 'group', title: 'Fulfilled vs Lost Demand by Agent'};
    Plotly.newPlot('chart-container', [trace1, trace2], layout);
    console.log('Chart rendered.');
});