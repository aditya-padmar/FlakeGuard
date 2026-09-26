"""Tests with timing-related flakiness patterns."""
import os
import random
import threading
import time


class TestTimingIssues:
    """Tests exhibiting timing and race condition flakiness."""

    def test_worker_thread_race(self):
        """Worker thread race condition where wait timeout can expire before thread finishes."""
        results = []
        done = threading.Event()

        def worker():
            time.sleep(random.uniform(0.0, 0.06))
            results.append("ok")
            done.set()

        t = threading.Thread(target=worker)
        t.start()

        done.wait(timeout=0.03)
        # CRITICAL: Take snapshot before join
        snapshot = list(results)
        t.join()

        jitter_val = os.environ.get("FG_JITTER_MS")
        assert snapshot == ["ok"], (
            f"Suspected cause: timing race condition in worker thread. "
            f"Observed snapshot: {snapshot}, FG_JITTER_MS: {jitter_val}"
        )

    def test_wait_is_deterministic_control(self):
        """Stable control test with pure in-process computation."""
        values = [i * 2 for i in range(10)]
        assert sum(values) == 90
