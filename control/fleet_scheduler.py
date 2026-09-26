"""Bounded synchronous scheduling over durable claims/backoff.

Call tick from a supervised loop. Adapters must enforce their own timeout (SSH:
25s); the deadline stops starting new operations, not an in-flight remote effect.
"""
import time
from control.fleet_store import positive
from control.fleet_worker import FleetWorker


class FleetScheduler:
    def __init__(self, store, adapters, *, monotonic=time.monotonic):
        self.store = store
        self.worker = FleetWorker(store, adapters)
        self.monotonic = monotonic

    def tick(self, *, limit=10, budget=30):
        positive(limit, 100)
        positive(budget, 300)
        deadline = self.monotonic()+budget
        self.store.expire(limit=100)
        results = []
        for _ in range(limit):
            if self.monotonic() >= deadline:
                break
            claim = self.store.claim_work(hold=60)
            if claim is None:
                break
            lease, token = claim
            result = self.worker.process(lease)
            self.store.finish_work(lease, token, result)
            results.append((lease.lease_id, result))
        return results
