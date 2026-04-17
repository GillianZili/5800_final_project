const cfg = window.routeConfig || { pollIntervalMs: 1000, routeNames: [], numRoutes: 3 };
const maxPoints = 30;
const ROUTE_COLORS = ["#5eead4", "#7cc5ff", "#f59e0b"];
const MAX_SPEED = 80;

// --- Chart setup ---
const chartCtx = document.getElementById("routeChart");
const labels = [];
const datasets = cfg.routeNames.map((name, i) => ({
    label: name,
    data: [],
    borderColor: ROUTE_COLORS[i],
    backgroundColor: ROUTE_COLORS[i] + "20",
    tension: 0.35,
    borderWidth: i === 0 ? 3 : 2,
    pointRadius: 0,
}));

const routeChart = new Chart(chartCtx, {
    type: "line",
    data: { labels, datasets },
    options: {
        maintainAspectRatio: false,
        animation: { duration: 260, easing: "easeOutQuart" },
        interaction: { mode: "index", intersect: false },
        plugins: {
            legend: { labels: { color: "#d5deee", usePointStyle: true, boxWidth: 10 } },
        },
        scales: {
            x: { ticks: { color: "#93a7c7" }, grid: { color: "rgba(157,179,214,0.08)" } },
            y: {
                ticks: { color: "#93a7c7" },
                grid: { color: "rgba(157,179,214,0.08)" },
                title: { display: true, text: "P50 Speed (mph)", color: "#d5deee" },
                min: 0,
                max: MAX_SPEED,
            },
        },
    },
});

// --- State ---
let lastStep = 0;
let prevRecommended = -1;
const logEntries = [];
const MAX_LOG = 20;

// --- DOM helpers ---
function statusClass(status) {
    if (status === "Free Flow") return "free";
    if (status === "Moderate") return "moderate";
    if (status === "Congested") return "congested";
    return "neutral";
}

function updateRouteCard(route, isRec) {
    const i = route.id;
    document.getElementById(`p50-${i}`).textContent = route.p50.toFixed(1);
    document.getElementById(`p15-${i}`).textContent = route.p15.toFixed(1);
    document.getElementById(`p85-${i}`).textContent = route.p85.toFixed(1);
    document.getElementById(`speed-${i}`).textContent = route.speed.toFixed(1) + " mph";
    document.getElementById(`phase-${i}`).textContent = route.phase;

    const badge = document.getElementById(`status-${i}`);
    badge.className = `badge status-badge ${statusClass(route.status)}`;
    badge.textContent = route.status;

    const bar = document.getElementById(`bar-${i}`);
    const pct = Math.min(100, Math.max(0, (route.p50 / MAX_SPEED) * 100));
    bar.style.width = pct + "%";
    bar.className = "rc-bar";
    if (route.status === "Moderate") bar.classList.add("moderate");
    if (route.status === "Congested") bar.classList.add("congested");

    const card = document.getElementById(`card-${i}`);
    card.classList.toggle("is-recommended", isRec);
}

function updateMap(routes, recommended) {
    for (let i = 0; i < routes.length; i++) {
        const path = document.getElementById(`route-path-${i}`);
        const sc = statusClass(routes[i].status);
        path.setAttribute("data-status", sc === "neutral" ? "" : sc);
        path.classList.remove("recommended", "active", "inactive");
        if (i === recommended) {
            path.classList.add("recommended", "active");
        } else {
            path.classList.add("inactive");
        }
    }
}

function addLogEntry(step, fromName, toName) {
    logEntries.unshift({ step, fromName, toName });
    if (logEntries.length > MAX_LOG) logEntries.pop();

    const list = document.getElementById("log-list");
    list.innerHTML = "";
    logEntries.forEach((e) => {
        const div = document.createElement("div");
        div.className = "log-entry";
        div.innerHTML = `
            <span><span class="log-from">${e.fromName}</span> → <span class="log-to">${e.toName}</span></span>
            <span class="log-step">Step ${e.step}</span>
        `;
        list.appendChild(div);
    });
}

// --- Main render ---
function render(data) {
    const { step, routes, recommended } = data;

    routes.forEach((r) => updateRouteCard(r, r.id === recommended));
    updateMap(routes, recommended);

    const recBadge = document.getElementById("rec-badge");
    recBadge.textContent = "Recommended: " + (routes[recommended]?.name || "—");

    // Log route switches
    if (prevRecommended !== -1 && prevRecommended !== recommended) {
        addLogEntry(
            step,
            cfg.routeNames[prevRecommended] || `Route ${prevRecommended}`,
            cfg.routeNames[recommended] || `Route ${recommended}`
        );
    }
    prevRecommended = recommended;

    // Chart
    if (step > lastStep) {
        labels.push(`S${step}`);
        routes.forEach((r, i) => datasets[i].data.push(r.p50));
        if (labels.length > maxPoints) {
            labels.shift();
            datasets.forEach((ds) => ds.data.shift());
        }
        routeChart.update();
        lastStep = step;
    }
}

// --- Polling ---
async function poll() {
    try {
        const res = await fetch("/api/routes");
        if (!res.ok) return;
        const data = await res.json();
        render(data);
    } catch (e) {
        console.error(e);
    }
}

document.getElementById("reset-btn").addEventListener("click", async () => {
    const btn = document.getElementById("reset-btn");
    btn.disabled = true;
    btn.textContent = "Restarting…";
    try {
        const res = await fetch("/api/routes/reset", { method: "POST" });
        if (!res.ok) throw new Error("reset failed");
        labels.length = 0;
        datasets.forEach((ds) => (ds.data.length = 0));
        routeChart.update();
        lastStep = 0;
        prevRecommended = -1;
        logEntries.length = 0;
        document.getElementById("log-list").innerHTML =
            '<p class="log-empty">Waiting for route switches…</p>';
        const data = await res.json();
        render(data);
    } catch (e) {
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.textContent = "Restart Simulation";
    }
});

poll();
setInterval(poll, cfg.pollIntervalMs);
