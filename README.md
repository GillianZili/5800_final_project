# Traffic Percentile Dashboard

A lightweight traffic analytics demo built with Python and Flask.

This project simulates changing traffic conditions, feeds vehicle speeds into a sliding-window percentile tracker, and visualizes the live results in a browser dashboard. The system tracks:

- `P15`
- `P50`
- `P85`

using a custom four-heap `TrafficStream` implementation with lazy deletion for sliding-window updates.

## Quick Start

Run the dashboard locally with:

```bash
cd 5800_final_project
python3 -m pip install flask
python3 app.py
```

Then open:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

If you want the terminal-only version instead:

```bash
python3 main.py
```

## Features

- Sliding-window percentile tracking over recent traffic samples
- Lazy deletion so expired samples do not affect live statistics
- Simulated traffic phases:
  - `Off-Peak (Fast)`
  - `Accident/Congest`
  - `Recovery Phase`
- Real-time Flask dashboard
- Live Chart.js line chart for `P15`, `P50`, and `P85`
- Metric cards for current percentile values
- Current phase and traffic status badges
- Recent events log
- Restart simulation button

## Project Structure

```text
5800_final_project/
├── app.py
├── main.py
├── simulation.py
├── TrafficStream.py
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

## How It Works

### 1. Traffic Simulation

`simulation.py` generates a sequence of traffic speeds across three phases. Each sample includes:

- vehicle speed
- traffic phase label

### 2. Sliding-Window Percentiles

`TrafficStream.py` maintains `P15`, `P50`, and `P85` using a four-part heap structure. It keeps only the active window of recent values and removes expired values through lazy deletion.

This means the dashboard reflects current traffic conditions rather than the full history of the simulation.

### 3. Flask Dashboard

`app.py` runs a background loop that:

1. pulls the next simulated traffic sample
2. inserts it into `TrafficStream`
3. computes the latest percentile values
4. exposes the data through Flask routes

Routes:

- `/` renders the dashboard UI
- `/api/traffic` returns the latest live traffic snapshot as JSON
- `/api/reset` restarts the simulation state

### 4. Frontend

The frontend uses:

- plain HTML in `templates/index.html`
- CSS styling in `static/style.css`
- JavaScript polling and Chart.js updates in `static/app.js`

The browser polls the backend regularly and updates the chart, metrics, badges, and recent-events panel.

## Run Locally

### Requirements

- Python 3.10+ recommended
- `pip`

### Install Dependencies

From the project folder:

```bash
cd 5800_final_project
python3 -m pip install flask
```

### Start the App

```bash
python3 app.py
```

Then open:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Optional Console Run

If you want to run the non-web version:

```bash
python3 main.py
```

This prints milestone percentile statistics in the terminal.

## Traffic Status Logic

The dashboard derives a simple status label from `P50`:

- `Free Flow` if `P50 >= 55`
- `Moderate` if `P50 >= 30`
- `Congested` otherwise

## Notes / Assumptions

- The dashboard continuously cycles through regenerated simulation batches so the demo keeps running.
- The frontend uses the Chart.js CDN instead of bundling local assets.
- No database, authentication, websocket, or task queue is used; the app is intentionally lightweight for local presentation and class demo use.

## Demo Summary

This project demonstrates:

- streaming percentile analytics
- sliding-window statistics
- lazy deletion in heap-based data structures
- simple full-stack integration with Flask and JavaScript
