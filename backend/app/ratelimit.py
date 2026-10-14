import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """In-memory limiter: at most `limit` events per key within `window` seconds.

    Good enough for a single-instance deployment; a multi-instance one would need Redis.
    """

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        events = self._events[key]
        while events and events[0] <= now - self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True

    def reset(self) -> None:
        self._events.clear()
