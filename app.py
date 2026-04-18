import threading
import time
from collections import deque

from flask import Flask, jsonify, render_template

import data_loader
from TrafficStream import TrafficStream


WINDOW_SIZE = 120
POLL_INTERVAL_SECONDS = 0.75
RECENT_EVENT_LIMIT = 8
SIMULATION_BATCH_SIZE = 600

ROUTE_NAMES = ["I-101", "I-580", "I-680"]
NUM_ROUTES = len(ROUTE_NAMES)


class TrafficDashboardState:
    """Owns the live simulation loop and the latest dashboard snapshot."""

    def __init__(self, window_size: int, interval_seconds: float):
        self.window_size = window_size
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._sequence = []
        self._sequence_index = 0
        self._recent_events = deque(maxlen=RECENT_EVENT_LIMIT)
        self._reset_locked()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def snapshot(self) -> dict:
        with self._lock:
            return self._snapshot_locked()

    def reset(self) -> dict:
        with self._lock:
            self._reset_locked()
            return self._snapshot_locked()

    def _reset_locked(self) -> None:
        self._stream = TrafficStream(window_size=self.window_size)
        self._sequence = data_loader.get_traffic_data_stream(SIMULATION_BATCH_SIZE)
        self._sequence_index = 0
        self._recent_events.clear()
        self._step = 0
        self._timestamp = ""
        self._phase = "Waiting for stream"
        self._status = "Starting"
        self._speed = 0.0
        self._p15 = 0.0
        self._p50 = 0.0
        self._p85 = 0.0
        self._active_window_count = 0

    def _snapshot_locked(self) -> dict:
        return {
            "step": self._step,
            "timestamp": self._timestamp,
            "p15": self._p15,
            "p50": self._p50,
            "p85": self._p85,
            "phase": self._phase,
            "status": self._status,
            "speed": self._speed,
            "window_size": self.window_size,
            "active_window_count": self._active_window_count,
            "recent_events": list(self._recent_events),
        }

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                speed, phase = self._next_sample_locked()
                self._stream.add_number(speed)
                self._step += 1
                self._timestamp = time.strftime("%H:%M:%S")
                self._phase = phase
                self._speed = round(speed, 1)
                self._p15 = round(self._stream.get_p15(), 1)
                self._p50 = round(self._stream.get_p50(), 1)
                self._p85 = round(self._stream.get_p85(), 1)
                self._active_window_count = min(self._step, self.window_size)
                self._status = classify_status(self._p50)
                self._recent_events.appendleft(
                    {
                        "step": self._step,
                        "speed": self._speed,
                        "phase": self._phase,
                        "status": self._status,
                    }
                )
            time.sleep(self.interval_seconds)

    def _next_sample_locked(self):
        if self._sequence_index >= len(self._sequence):
            self._sequence = data_loader.get_traffic_data_stream(SIMULATION_BATCH_SIZE)
            self._sequence_index = 0
        sample = self._sequence[self._sequence_index]
        self._sequence_index += 1
        return sample


class MultiRouteDashboardState:
    """Manages N parallel TrafficStream instances, one per route."""

    def __init__(self, num_routes, window_size, interval_seconds):
        self.num_routes = num_routes
        self.window_size = window_size
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._reset_locked()

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def snapshot(self):
        with self._lock:
            return self._snapshot_locked()

    def reset(self):
        with self._lock:
            self._reset_locked()
            return self._snapshot_locked()

    def _reset_locked(self):
        self._streams = [
            TrafficStream(window_size=self.window_size)
            for _ in range(self.num_routes)
        ]
        self._sequences = [
            data_loader.get_route_traffic_stream(i, SIMULATION_BATCH_SIZE)
            for i in range(self.num_routes)
        ]
        self._seq_indices = [0] * self.num_routes
        self._step = 0
        self._timestamp = ""
        self._route_data = [self._empty_route(i) for i in range(self.num_routes)]
        self._recommended = 0

    def _empty_route(self, route_id):
        return {
            "id": route_id,
            "name": ROUTE_NAMES[route_id],
            "speed": 0.0,
            "p15": 0.0,
            "p50": 0.0,
            "p85": 0.0,
            "phase": "Waiting",
            "status": "Starting",
        }

    def _snapshot_locked(self):
        return {
            "step": self._step,
            "timestamp": self._timestamp,
            "routes": list(self._route_data),
            "recommended": self._recommended,
        }

    def _run_loop(self):
        while not self._stop_event.is_set():
            with self._lock:
                self._step += 1
                self._timestamp = time.strftime("%H:%M:%S")
                for i in range(self.num_routes):
                    speed, phase = self._next_sample(i)
                    self._streams[i].add_number(speed)
                    p15 = round(self._streams[i].get_p15(), 1)
                    p50 = round(self._streams[i].get_p50(), 1)
                    p85 = round(self._streams[i].get_p85(), 1)
                    self._route_data[i] = {
                        "id": i,
                        "name": ROUTE_NAMES[i],
                        "speed": round(speed, 1),
                        "p15": p15,
                        "p50": p50,
                        "p85": p85,
                        "phase": phase,
                        "status": classify_status(p50),
                    }
                best = max(
                    range(self.num_routes),
                    key=lambda r: self._route_data[r]["p50"],
                )
                self._recommended = best
            time.sleep(self.interval_seconds)

    def _next_sample(self, route_id):
        idx = self._seq_indices[route_id]
        seq = self._sequences[route_id]
        if idx >= len(seq):
            # Wrap around to the beginning of the same route data
            self._seq_indices[route_id] = 0
            idx = 0
        sample = seq[idx]
        self._seq_indices[route_id] = idx + 1
        return sample


def classify_status(p50):
    if p50 >= 55:
        return "Free Flow"
    if p50 >= 30:
        return "Moderate"
    return "Congested"


app = Flask(__name__)

dashboard_state = TrafficDashboardState(
    window_size=WINDOW_SIZE,
    interval_seconds=POLL_INTERVAL_SECONDS,
)
dashboard_state.start()

route_state = MultiRouteDashboardState(
    num_routes=NUM_ROUTES,
    window_size=WINDOW_SIZE,
    interval_seconds=POLL_INTERVAL_SECONDS,
)
route_state.start()


@app.route("/")
def index():
    return render_template(
        "index.html",
        poll_interval_ms=int(POLL_INTERVAL_SECONDS * 1000),
    )


@app.route("/routes")
def routes_page():
    return render_template(
        "routes.html",
        poll_interval_ms=int(POLL_INTERVAL_SECONDS * 1000),
        route_names=ROUTE_NAMES,
    )


@app.route("/api/traffic")
def traffic_data():
    return jsonify(dashboard_state.snapshot())


@app.post("/api/reset")
def reset_traffic():
    return jsonify(dashboard_state.reset())


@app.route("/api/routes")
def routes_data():
    return jsonify(route_state.snapshot())


@app.post("/api/routes/reset")
def reset_routes():
    return jsonify(route_state.reset())


if __name__ == "__main__":
    app.run(debug=True)
