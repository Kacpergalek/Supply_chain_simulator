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
    var text = "";
    var dict = {}
    var listOfForms = ["disruptionType", "severity", "duration", "dayOfStart", "placeOfDisruption"];
    for (index in listOfForms) {

        var e = document.getElementById(listOfForms[index]);
        text += e.options[e.selectedIndex].text;
        dict[listOfForms[index]] = e.options[e.selectedIndex].text;
    }

    $.ajax({
        url: baseUrl + '/api/process',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(dict),
        success: function (response) {
            document.getElementById('output').innerHTML =
                JSON.stringify("Data submitted successfully", null, 2);

            Plotly.newPlot('chart-container', response.data, response.layout);
            console.log("Chart rendered.")
        },
        error: function (error) {
            console.log(error);
        }
    });
}