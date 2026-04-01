import heapq
import math
from collections import deque


class TrafficStream:
    """
    Tracks P15, P50, and P85 over a sliding window.

    The window is split into four ordered partitions:
    0-15%, 15-50%, 50-85%, and 85-100%.

    Interior partitions keep both min and max heap views so we can rebalance
    across percentile boundaries while using lazy deletion for expired entries.
    """

    _SEG_15 = "p15"
    _SEG_50 = "p50"
    _SEG_85 = "p85"
    _SEG_100 = "p100"

    def __init__(self, window_size: int = 4000):
        if window_size <= 0:
            raise ValueError("window_size must be positive")

        self.window_size = window_size
        self._next_id = 0
        self._window = deque()
        self._segment_of = {}
        self._sizes = {
            self._SEG_15: 0,
            self._SEG_50: 0,
            self._SEG_85: 0,
            self._SEG_100: 0,
        }

        self._heap_15_max = []
        self._heap_50_min = []
        self._heap_50_max = []
        self._heap_85_min = []
        self._heap_85_max = []
        self._heap_100_min = []

    def add_number(self, speed: float) -> None:
        entry_id = self._next_id
        self._next_id += 1
        self._window.append((entry_id, speed))

        segment = self._pick_segment(speed)
        self._assign(entry_id, speed, segment)

        if len(self._window) > self.window_size:
            old_id, _ = self._window.popleft()
            self._expire(old_id)

        self._normalize()

    def get_p15(self) -> float:
        if not self._window:
            return 0.0
        return self._peek_max(self._SEG_15) or 0.0

    def get_p50(self) -> float:
        if not self._window:
            return 0.0

        value = self._peek_max(self._SEG_50)
        if value is not None:
            return value
        return self.get_p15()

    def get_p85(self) -> float:
        if not self._window:
            return 0.0

        value = self._peek_max(self._SEG_85)
        if value is not None:
            return value
        return self.get_p50()

    def _expire(self, entry_id: int) -> None:
        segment = self._segment_of.pop(entry_id, None)
        if segment is not None:
            self._sizes[segment] -= 1

    def _pick_segment(self, speed: float) -> str:
        p15 = self._peek_max(self._SEG_15)
        if p15 is None or speed <= p15:
            return self._SEG_15

        p50 = self._peek_max(self._SEG_50)
        if p50 is None or speed <= p50:
            return self._SEG_50

        p85 = self._peek_max(self._SEG_85)
        if p85 is None or speed <= p85:
            return self._SEG_85

        return self._SEG_100

    def _assign(self, entry_id: int, value: float, segment: str) -> None:
        self._segment_of[entry_id] = segment
        self._sizes[segment] += 1

        if segment == self._SEG_15:
            heapq.heappush(self._heap_15_max, (-value, entry_id))
        elif segment == self._SEG_50:
            heapq.heappush(self._heap_50_min, (value, entry_id))
            heapq.heappush(self._heap_50_max, (-value, entry_id))
        elif segment == self._SEG_85:
            heapq.heappush(self._heap_85_min, (value, entry_id))
            heapq.heappush(self._heap_85_max, (-value, entry_id))
        else:
            heapq.heappush(self._heap_100_min, (value, entry_id))

    def _normalize(self) -> None:
        self._prune_all()
        self._restore_order()
        self._rebalance_sizes()
        self._restore_order()

    def _rebalance_sizes(self) -> None:
        total = len(self._window)
        if total == 0:
            return

        target_15 = min(total, int(total * 0.15) + 1)
        target_50 = min(total, int(total * 0.50) + 1)
        target_85 = min(total, int(total * 0.85) + 1)

        segment_targets = {
            self._SEG_15: target_15,
            self._SEG_50: target_50 - target_15,
            self._SEG_85: target_85 - target_50,
            self._SEG_100: total - target_85,
        }

        while self._sizes[self._SEG_15] > segment_targets[self._SEG_15]:
            self._move_boundary(self._SEG_15, self._SEG_50, direction="max")
        while self._sizes[self._SEG_15] < segment_targets[self._SEG_15]:
            self._move_boundary(self._SEG_50, self._SEG_15, direction="min")

        while self._sizes[self._SEG_50] > segment_targets[self._SEG_50]:
            self._move_boundary(self._SEG_50, self._SEG_85, direction="max")
        while self._sizes[self._SEG_50] < segment_targets[self._SEG_50]:
            self._move_boundary(self._SEG_85, self._SEG_50, direction="min")

        while self._sizes[self._SEG_85] > segment_targets[self._SEG_85]:
            self._move_boundary(self._SEG_85, self._SEG_100, direction="max")
        while self._sizes[self._SEG_85] < segment_targets[self._SEG_85]:
            self._move_boundary(self._SEG_100, self._SEG_85, direction="min")

    def _restore_order(self) -> None:
        changed = True
        while changed:
            changed = False
            changed |= self._swap_if_needed(self._SEG_15, self._SEG_50)
            changed |= self._swap_if_needed(self._SEG_50, self._SEG_85)
            changed |= self._swap_if_needed(self._SEG_85, self._SEG_100)

    def _swap_if_needed(self, left: str, right: str) -> bool:
        swapped = False

        while (
            self._sizes[left] > 0
            and self._sizes[right] > 0
            and self._peek_max(left) > self._peek_min(right)
        ):
            left_id, left_value = self._pop_max(left)
            right_id, right_value = self._pop_min(right)
            self._assign(left_id, left_value, right)
            self._assign(right_id, right_value, left)
            swapped = True

        return swapped

    def _move_boundary(self, source: str, target: str, direction: str) -> None:
        if self._sizes[source] == 0:
            return

        if direction == "max":
            entry_id, value = self._pop_max(source)
        else:
            entry_id, value = self._pop_min(source)
        self._assign(entry_id, value, target)

    def _pop_min(self, segment: str):
        heap = self._min_heap(segment)
        self._prune_min(segment)
        value, entry_id = heapq.heappop(heap)
        self._segment_of.pop(entry_id, None)
        self._sizes[segment] -= 1
        return entry_id, value

    def _pop_max(self, segment: str):
        heap = self._max_heap(segment)
        self._prune_max(segment)
        value, entry_id = heapq.heappop(heap)
        self._segment_of.pop(entry_id, None)
        self._sizes[segment] -= 1
        return entry_id, -value

    def _peek_min(self, segment: str):
        if self._sizes[segment] == 0:
            return None
        self._prune_min(segment)
        heap = self._min_heap(segment)
        if not heap:
            return None
        return heap[0][0]

    def _peek_max(self, segment: str):
        if self._sizes[segment] == 0:
            return None
        self._prune_max(segment)
        heap = self._max_heap(segment)
        if not heap:
            return None
        return -heap[0][0]

    def _prune_all(self) -> None:
        self._prune_max(self._SEG_15)
        self._prune_min(self._SEG_50)
        self._prune_max(self._SEG_50)
        self._prune_min(self._SEG_85)
        self._prune_max(self._SEG_85)
        self._prune_min(self._SEG_100)

    def _prune_min(self, segment: str) -> None:
        heap = self._min_heap(segment)
        while heap and self._segment_of.get(heap[0][1]) != segment:
            heapq.heappop(heap)

    def _prune_max(self, segment: str) -> None:
        heap = self._max_heap(segment)
        while heap and self._segment_of.get(heap[0][1]) != segment:
            heapq.heappop(heap)

    def _min_heap(self, segment: str):
        if segment == self._SEG_50:
            return self._heap_50_min
        if segment == self._SEG_85:
            return self._heap_85_min
        if segment == self._SEG_100:
            return self._heap_100_min
        raise ValueError(f"{segment} does not expose a min heap")

    def _max_heap(self, segment: str):
        if segment == self._SEG_15:
            return self._heap_15_max
        if segment == self._SEG_50:
            return self._heap_50_max
        if segment == self._SEG_85:
            return self._heap_85_max
        raise ValueError(f"{segment} does not expose a max heap")
