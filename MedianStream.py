import heapq

class MedianStream:
    def __init__(self):
        # max heap (store negatives)
        self._left = []
        # min heap
        self._right = []

    def add_number(self, num: int) -> None:
        if not self._left or num <= -self._left[0]:
            heapq.heappush(self._left, -num)
        else:
            heapq.heappush(self._right, num)

        self._rebalance()

    def get_median(self) -> float:
        if len(self._left) > len(self._right):
            return -self._left[0]
        return (-self._left[0] + self._right[0]) / 2

    def _rebalance(self):
        if len(self._left) > len(self._right) + 1:
            heapq.heappush(self._right, -heapq.heappop(self._left))
        elif len(self._right) > len(self._left):
            heapq.heappush(self._left, -heapq.heappop(self._right))