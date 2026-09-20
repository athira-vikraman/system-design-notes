"""
Message Queue with Workers  ->  DESIGN_PATTERNS.md #5, PRACTICE_PROBLEMS.md #4

The user should not wait while you send an email or resize a video.
Put the job on a queue, reply immediately, let workers do it later.

This also shows two things interviewers always ask about:
  - retries for jobs that fail
  - a dead letter queue for jobs that keep failing
"""

import queue
import threading
import time


class Job:
    def __init__(self, job_id, kind, payload):
        self.id = job_id
        self.kind = kind
        self.payload = payload
        self.attempts = 0

    def __repr__(self):
        return f"Job({self.id}, {self.kind})"


class MessageQueue:
    def __init__(self, max_attempts=3):
        self.queue = queue.Queue()
        self.dead_letter = []      # jobs that failed too many times
        self.completed = []
        self.max_attempts = max_attempts
        self.handlers = {}
        self.lock = threading.Lock()
        self._stop = threading.Event()

    def register(self, kind, handler):
        self.handlers[kind] = handler

    def publish(self, job):
        """Called by the API. Returns instantly."""
        self.queue.put(job)

    def _worker(self, name):
        while not self._stop.is_set():
            try:
                job = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue

            job.attempts += 1
            try:
                self.handlers[job.kind](job.payload)
                with self.lock:
                    self.completed.append(job)
                print(f"  [{name}] done    {job.id} ({job.kind})")

            except Exception as error:
                if job.attempts < self.max_attempts:
                    print(f"  [{name}] retry   {job.id} attempt {job.attempts}: {error}")
                    self.queue.put(job)  # back on the queue
                else:
                    with self.lock:
                        self.dead_letter.append(job)
                    print(f"  [{name}] DEAD    {job.id} after {job.attempts} attempts")

            finally:
                self.queue.task_done()

    def start_workers(self, count=3):
        self.workers = []
        for i in range(count):
            thread = threading.Thread(target=self._worker, args=(f"worker-{i+1}",), daemon=True)
            thread.start()
            self.workers.append(thread)

    def wait_and_stop(self):
        self.queue.join()
        self._stop.set()
        for thread in self.workers:
            thread.join(timeout=1)


# ---------- handlers: the actual slow work ----------

def send_email(payload):
    time.sleep(0.05)  # pretend network call


def resize_image(payload):
    time.sleep(0.08)


_flaky_state = {"failures": 0}


def call_broken_service(payload):
    """Fails the first 2 times, then works. Shows retries succeeding."""
    _flaky_state["failures"] += 1
    if _flaky_state["failures"] <= 2:
        raise ConnectionError("provider timeout")


def always_fails(payload):
    raise ValueError("bad payload")


def demo():
    mq = MessageQueue(max_attempts=3)
    mq.register("email", send_email)
    mq.register("resize", resize_image)
    mq.register("flaky", call_broken_service)
    mq.register("broken", always_fails)

    print("API publishing 8 jobs (returns instantly)...\n")
    start = time.monotonic()

    jobs = [
        Job("j1", "email", {"to": "a@x.com"}),
        Job("j2", "email", {"to": "b@x.com"}),
        Job("j3", "resize", {"file": "photo1.jpg"}),
        Job("j4", "resize", {"file": "photo2.jpg"}),
        Job("j5", "flaky", {}),
        Job("j6", "email", {"to": "c@x.com"}),
        Job("j7", "broken", {}),
        Job("j8", "resize", {"file": "photo3.jpg"}),
    ]
    for job in jobs:
        mq.publish(job)

    publish_time = time.monotonic() - start
    print(f"  8 jobs queued in {publish_time*1000:.1f} ms")
    print("  -> this is what the user waits for. Nothing else.\n")

    print("Workers processing in the background:\n")
    mq.start_workers(count=3)
    mq.wait_and_stop()

    total = time.monotonic() - start
    print(f"\n  completed   : {len(mq.completed)}")
    print(f"  dead letter : {len(mq.dead_letter)}  {mq.dead_letter}")
    print(f"  total work  : {total:.2f}s, but the user waited {publish_time*1000:.1f} ms")
    print("\n  j5 failed twice and then succeeded on retry.")
    print("  j7 failed 3 times and went to the dead letter queue")
    print("  for a human to look at, instead of retrying forever.")


if __name__ == "__main__":
    demo()
