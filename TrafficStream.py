import heapq

class TrafficStream:
    """
    Maintains P15, P50 (Median), and P85 using a four-heap architecture.
    """
    def __init__(self):
        # Max-heap for the bottom 0% - 15% (stores negative values)
        self._heap_15 = []
        # Min-heap for the 15% - 50% range
        self._heap_50 = []
        # Min-heap for the 50% - 85% range
        self._heap_85 = []
        # Min-heap for the 85% - 100% range
        self._heap_100 = []

    def add_number(self, speed: int) -> None:
        if not self._heap_15 or speed <= -self._heap_15[0]:
            heapq.heappush(self._heap_15, -speed)
        elif not self._heap_50 or speed <= self._heap_50[0]:
            heapq.heappush(self._heap_50, speed)
        elif not self._heap_85 or speed <= self._heap_85[0]:
            heapq.heappush(self._heap_85, speed)
        else:
            heapq.heappush(self._heap_100, speed)

        self._rebalance()

    # def get_median(self) -> float:
    #     if len(self._left) > len(self._right):
    #         return -self._left[0]
    #     return (-self._left[0] + self._right[0]) / 2

    def _rebalance(self):
        total = len(self._heap_15) + len(self._heap_50) + len(self._heap_85) + len(self._heap_100)
        if total == 0: return

        # Target sizes for each heap based on the percentiles
        t15 = max(1, int(total * 0.15))
        t50 = max(1, int(total * 0.50) - t15)
        t85 = max(1, int(total * 0.85) - t15 - t50)
        
        # Balance 15% vs 50%
        while len(self._heap_15) > t15:
            heapq.heappush(self._heap_50, -heapq.heappop(self._heap_15))
        while len(self._heap_15) < t15 and self._heap_50:
            heapq.heappush(self._heap_15, -heapq.heappop(self._heap_50))

        # Balance 50% vs 85%
        while len(self._heap_50) > t50:
            heapq.heappush(self._heap_85, heapq.heappop(self._heap_50))
        while len(self._heap_50) < t50 and self._heap_85:
            heapq.heappush(self._heap_50, heapq.heappop(self._heap_85))

        # Balance 85% vs 100%
        while len(self._heap_85) > t85:
            heapq.heappush(self._heap_100, heapq.heappop(self._heap_85))
        while len(self._heap_85) < t85 and self._heap_100:
            heapq.heappush(self._heap_85, heapq.heappop(self._heap_100))
    
    def get_p15(self) -> float:
        if self._heap_15:
            return -self._heap_15[0]  
        else:
            return 0.0

    def get_p50(self) -> float:
        if self._heap_50:
            return self._heap_50[0]  
        else:
            return self.get_p15()
        
    def get_p85(self) -> float:
        if self._heap_85:
            return self._heap_85[0]  
        else:
            return self.get_p50()