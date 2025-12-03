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