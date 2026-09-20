"""
Circuit Breaker  ->  DESIGN_PATTERNS.md #9

A service is down. Every call to it hangs for 30 seconds until it times out.
Your threads fill up waiting, and now YOUR service is down too.
That is a cascading failure.

The fix: after N failures, stop calling. Fail instantly instead.
Check again after a while.

    CLOSED  --too many failures-->  OPEN
      ^                              |
      |                        after timeout
      |                              v
      +------ success ------- HALF_OPEN --failure--> OPEN
"""

import time


class CircuitOpenError(Exception):
    """Raised instead of calling a service we believe is broken."""


class CircuitBreaker:
    CLOSED = "CLOSED"        # normal
    OPEN = "OPEN"            # broken, do not call
    HALF_OPEN = "HALF_OPEN"  # testing whether it recovered

    def __init__(self, failure_threshold=3, recovery_timeout=2.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = self.CLOSED
        self.failures = 0
        self.opened_at = None

    def call(self, func, *args, **kwargs):
        if self.state == self.OPEN:
            if time.monotonic() - self.opened_at >= self.recovery_timeout:
                self.state = self.HALF_OPEN  # time to try one request
            else:
                raise CircuitOpenError("Circuit is open, not calling the service")

        try:
            result = func(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise

        self._on_success()
        return result

    def _on_success(self):
        self.failures = 0
        self.state = self.CLOSED

    def _on_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = self.OPEN
            self.opened_at = time.monotonic()


class FlakyService:
    """Pretend service. Broken until we decide to fix it."""

    def __init__(self):
        self.working = False
        self.calls_received = 0

    def fetch(self):
        self.calls_received += 1
        if not self.working:
            raise ConnectionError("service unavailable")
        return "data"


def demo():
    service = FlakyService()
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    print("Service is DOWN. Making 6 calls.\n")
    for i in range(1, 7):
        try:
            breaker.call(service.fetch)
            print(f"  call {i}: ok")
        except CircuitOpenError:
            print(f"  call {i}: blocked instantly   [{breaker.state}]")
        except ConnectionError:
            print(f"  call {i}: failed              [{breaker.state}]")

    print(f"\n  The service only received {service.calls_received} calls, not 6.")
    print("  The circuit breaker absorbed the rest and failed fast.")

    print("\nWaiting for the recovery timeout, then the service comes back...\n")
    time.sleep(1.1)
    service.working = True

    for i in range(1, 4):
        try:
            result = breaker.call(service.fetch)
            print(f"  call {i}: {result}                [{breaker.state}]")
        except CircuitOpenError:
            print(f"  call {i}: blocked             [{breaker.state}]")

    print("\n  -> one test request succeeded, so the circuit closed again")


if __name__ == "__main__":
    demo()
