"""
Retry with Backoff and Jitter  ->  DESIGN_PATTERNS.md #10

A call failed. Retrying immediately makes an overloaded service worse.

Backoff:  wait longer each time  -> 1s, 2s, 4s, 8s
Jitter:   add randomness         -> stops 10,000 clients retrying
                                     at the exact same millisecond

Without jitter you get a "thundering herd": everyone retries together,
knocks the service over again, and the cycle repeats.
"""

import random
import time
from functools import wraps


def retry(max_attempts=4, base_delay=0.1, max_delay=10.0, jitter=True):
    """
    Decorator. Retries the function with exponential backoff.

    WARNING: only use this on idempotent operations.
    Retrying "charge the card" without an idempotency key charges twice.
    See 09_message_queue.py for that.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error

                    if attempt == max_attempts - 1:
                        break  # that was our last try

                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if jitter:
                        # full jitter: pick anywhere between 0 and the delay
                        delay = random.uniform(0, delay)

                    print(f"      attempt {attempt + 1} failed, waiting {delay:.2f}s")
                    time.sleep(delay)

            raise last_error

        return wrapper

    return decorator


def show_delay_growth():
    print("How the delay grows (base 1s):\n")
    print("  attempt   no jitter   with jitter (random each run)")
    for attempt in range(5):
        plain = min(1.0 * (2 ** attempt), 30)
        jittered = random.uniform(0, plain)
        print(f"    {attempt + 1}        {plain:>5.1f}s       {jittered:>5.2f}s")
    print("\n  Jitter spreads retries out instead of bunching them together.")


# a service that fails twice, then works
_calls = {"count": 0}


@retry(max_attempts=4, base_delay=0.1)
def flaky_fetch():
    _calls["count"] += 1
    if _calls["count"] < 3:
        raise ConnectionError("temporary failure")
    return "data received"


@retry(max_attempts=3, base_delay=0.05)
def always_broken():
    raise ConnectionError("permanently down")


def demo():
    show_delay_growth()

    print("\n\nRetrying a service that fails twice then recovers:\n")
    result = flaky_fetch()
    print(f"      -> {result} after {_calls['count']} attempts")

    print("\n\nRetrying a service that never recovers:\n")
    try:
        always_broken()
    except ConnectionError as error:
        print(f"      -> gave up after 3 attempts: {error}")
    print("\n  Giving up matters. Retrying forever is how you stay down.")


if __name__ == "__main__":
    demo()
