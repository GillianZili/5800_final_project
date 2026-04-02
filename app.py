import threading
import time
from collections import deque

from flask import Flask, jsonify, render_template

import simulation
from TrafficStream import TrafficStream


WINDOW_SIZE = 120
POLL_INTERVAL_SECONDS = 0.75
RECENT_EVENT_LIMIT = 8
SIMULATION_BATCH_SIZE = 600


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
        self._sequence = simulation.get_traffic_data_stream(SIMULATION_BATCH_SIZE)
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
            self._sequence = simulation.get_traffic_data_stream(SIMULATION_BATCH_SIZE)
            self._sequence_index = 0

        sample = self._sequence[self._sequence_index]
        self._sequence_index += 1
        return sample


def classify_status(p50: float) -> str:
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


@app.route("/")
def index():
    return render_template(
        "index.html",
        poll_interval_ms=int(POLL_INTERVAL_SECONDS * 1000),
    )


@app.route("/api/traffic")
def traffic_data():
    return jsonify(dashboard_state.snapshot())


@app.post("/api/reset")
def reset_traffic():
    return jsonify(dashboard_state.reset())


if __name__ == "__main__":
    app.run(debug=True)
