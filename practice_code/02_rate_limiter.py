"""
Rate Limiter  ->  DESIGN_PATTERNS.md #8, PRACTICE_PROBLEMS.md #3

Stop one user from flooding your system.
Two algorithms, so you can feel the difference.
"""

import time
from collections import deque


class TokenBucket:
    """
    The usual choice.

    A bucket holds tokens. Every request spends one.
    Tokens refill at a steady rate.

    Why it is good: a user who was quiet for a while has a full bucket,
    so a short burst is allowed. Real users behave in bursts.
    """

    def __init__(self, capacity, refill_per_second):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def allow(self, cost=1):
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill = now


class SlidingWindow:
    """
    Keep the timestamp of every request in the last N seconds.
    Exact, but uses memory proportional to the number of requests.

    Fixes the fixed-window flaw: with "100 per minute", a user could send
    100 at 11:59:59 and 100 at 12:00:00 -> 200 in one second.
    """

    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps = deque()

    def allow(self):
        now = time.monotonic()

        # drop anything older than the window
        while self.timestamps and now - self.timestamps[0] > self.window_seconds:
            self.timestamps.popleft()

        if len(self.timestamps) < self.max_requests:
            self.timestamps.append(now)
            return True
        return False


class PerUserLimiter:
    """In real life you limit each user separately."""

    def __init__(self, capacity, refill_per_second):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.buckets = {}

    def allow(self, user_id):
        if user_id not in self.buckets:
            self.buckets[user_id] = TokenBucket(self.capacity, self.refill_per_second)
        return self.buckets[user_id].allow()


def demo():
    print("Token bucket: capacity 5, refills 2 per second\n")
    bucket = TokenBucket(capacity=5, refill_per_second=2)

    print("  10 requests as fast as possible:")
    results = ["OK" if bucket.allow() else "429" for _ in range(10)]
    print(f"    {' '.join(results)}")
    print("    -> first 5 pass (the bucket was full), rest are rejected")

    print("\n  wait 1 second (2 tokens refill), then 3 more requests:")
    time.sleep(1)
    results = ["OK" if bucket.allow() else "429" for _ in range(3)]
    print(f"    {' '.join(results)}")

    print("\nPer-user limiting: 3 requests each\n")
    limiter = PerUserLimiter(capacity=3, refill_per_second=1)
    for user in ["athira", "athira", "athira", "athira", "ravi"]:
        status = "OK" if limiter.allow(user) else "429"
        print(f"    {user:8} {status}")
    print("    -> ravi is unaffected by athira hitting the limit")


if __name__ == "__main__":
    demo()
