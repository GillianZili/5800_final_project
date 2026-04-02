const config = window.dashboardConfig || { pollIntervalMs: 1000 };
const maxPoints = 24;

const chartContext = document.getElementById("trafficChart");
const p15Value = document.getElementById("p15-value");
const p50Value = document.getElementById("p50-value");
const p85Value = document.getElementById("p85-value");
const phaseText = document.getElementById("phase-text");
const statusText = document.getElementById("status-text");
const speedText = document.getElementById("speed-text");
const windowText = document.getElementById("window-text");
const timestampText = document.getElementById("timestamp-text");
const phaseBadge = document.getElementById("phase-badge");
const statusBadge = document.getElementById("status-badge");
const eventsList = document.getElementById("events-list");
const resetButton = document.getElementById("reset-button");

const labels = [];
const p15Series = [];
const p50Series = [];
const p85Series = [];

const trafficChart = new Chart(chartContext, {
    type: "line",
    data: {
        labels,
        datasets: [
            {
                label: "P15",
                data: p15Series,
                borderColor: "#5eead4",
                backgroundColor: "rgba(94, 234, 212, 0.12)",
                tension: 0.35,
                borderWidth: 2,
                pointRadius: 0,
            },
            {
                label: "P50",
                data: p50Series,
                borderColor: "#7cc5ff",
                backgroundColor: "rgba(124, 197, 255, 0.16)",
                tension: 0.35,
                borderWidth: 3,
                pointRadius: 0,
            },
            {
                label: "P85",
                data: p85Series,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.12)",
                tension: 0.35,
                borderWidth: 2,
                pointRadius: 0,
            },
        ],
    },
    options: {
        maintainAspectRatio: false,
        animation: {
            duration: 260,
            easing: "easeOutQuart",
        },
        interaction: {
            mode: "index",
            intersect: false,
        },
        plugins: {
            legend: {
                labels: {
                    color: "#d5deee",
                    usePointStyle: true,
                    boxWidth: 10,
                },
            },
        },
        scales: {
            x: {
                ticks: {
                    color: "#93a7c7",
                },
                grid: {
                    color: "rgba(157, 179, 214, 0.08)",
                },
            },
            y: {
                ticks: {
                    color: "#93a7c7",
                },
                grid: {
                    color: "rgba(157, 179, 214, 0.08)",
                },
                title: {
                    display: true,
                    text: "Speed (mph)",
                    color: "#d5deee",
                },
            },
        },
    },
});

function statusClass(status) {
    if (status === "Free Flow") {
        return "free";
    }
    if (status === "Moderate") {
        return "moderate";
    }
    if (status === "Congested") {
        return "congested";
    }
    return "neutral";
}

function updateBadge(element, status) {
    element.className = `badge status-badge ${statusClass(status)}`;
    element.textContent = status;
}

function pushPoint(step, p15, p50, p85) {
    labels.push(`S${step}`);
    p15Series.push(p15);
    p50Series.push(p50);
    p85Series.push(p85);

    if (labels.length > maxPoints) {
        labels.shift();
        p15Series.shift();
        p50Series.shift();
        p85Series.shift();
    }

    trafficChart.update();
}

function renderEvents(events) {
    eventsList.innerHTML = "";

    if (!events.length) {
        eventsList.innerHTML = '<div class="event-row"><div class="event-left"><span class="event-speed">Waiting for data</span><span class="event-phase">The simulation will appear here as soon as samples arrive.</span></div></div>';
        return;
    }

    events.forEach((event) => {
        const row = document.createElement("div");
        row.className = "event-row";

        const left = document.createElement("div");
        left.className = "event-left";
        left.innerHTML = `
            <span class="event-speed">${event.speed.toFixed(1)} mph</span>
            <span class="event-phase">${event.phase}</span>
            <span class="event-meta">Step ${event.step}</span>
        `;

        const status = document.createElement("span");
        status.className = `badge status-badge event-status ${statusClass(event.status)}`;
        status.textContent = event.status;

        row.appendChild(left);
        row.appendChild(status);
        eventsList.appendChild(row);
    });
}

let lastStep = 0;

function renderSnapshot(data) {
    p15Value.textContent = data.p15.toFixed(1);
    p50Value.textContent = data.p50.toFixed(1);
    p85Value.textContent = data.p85.toFixed(1);
    phaseText.textContent = data.phase;
    statusText.textContent = data.status;
    speedText.textContent = `${data.speed.toFixed(1)} mph`;
    windowText.textContent = `${data.active_window_count} / ${data.window_size}`;
    timestampText.textContent = data.timestamp || "--:--:--";
    phaseBadge.textContent = data.phase;
    updateBadge(statusBadge, data.status);
    document.body.dataset.status = data.status;
    renderEvents(data.recent_events);

    if (data.step > lastStep) {
        pushPoint(data.step, data.p15, data.p50, data.p85);
        lastStep = data.step;
    }
}

async function fetchSnapshot() {
    const response = await fetch("/api/traffic");
    if (!response.ok) {
        throw new Error("Failed to load traffic snapshot");
    }
    const data = await response.json();
    renderSnapshot(data);
}

async function resetSimulation() {
    resetButton.disabled = true;
    resetButton.textContent = "Restarting...";

    try {
        const response = await fetch("/api/reset", { method: "POST" });
        if (!response.ok) {
            throw new Error("Reset failed");
        }

        labels.length = 0;
        p15Series.length = 0;
        p50Series.length = 0;
        p85Series.length = 0;
        trafficChart.update();
        lastStep = 0;

        const data = await response.json();
        renderSnapshot(data);
    } catch (error) {
        console.error(error);
    } finally {
        resetButton.disabled = false;
        resetButton.textContent = "Restart Simulation";
    }
}

resetButton.addEventListener("click", resetSimulation);

fetchSnapshot().catch((error) => console.error(error));
setInterval(() => {
    fetchSnapshot().catch((error) => console.error(error));
}, config.pollIntervalMs);
