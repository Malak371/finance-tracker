import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """In-memory limiter: at most `limit` events per key within `window` seconds.

    Good enough for a single-instance deployment; a multi-instance one would need Redis.
    """

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _recent(self, key: str) -> deque[float]:
        events = self._events[key]
        cutoff = time.monotonic() - self.window
        while events and events[0] <= cutoff:
            events.popleft()
        return events

    def is_limited(self, key: str) -> bool:
        return len(self._recent(key)) >= self.limit

    def record(self, key: str) -> None:
        self._recent(key).append(time.monotonic())

    def allow(self, key: str) -> bool:
        """Record an event for `key` unless it is already over the limit."""
        if self.is_limited(key):
            return False
        self.record(key)
        return True

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest event in the window expires."""
        events = self._recent(key)
        if not events:
            return 0
        return max(1, round(events[0] + self.window - time.monotonic()))

    def clear(self, key: str) -> None:
        self._events.pop(key, None)

    def reset(self) -> None:
        self._events.clear()
