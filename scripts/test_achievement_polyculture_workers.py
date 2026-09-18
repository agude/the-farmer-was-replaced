#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise persistent polyculture worker ownership and spawn fallback."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_polyculture as workers  # noqa: E402


def test_scheduler_runs_one_thousand_owned_transactions() -> None:
    calls = []
    active_regions = set()

    def transaction(primary_x, primary_y, mode) -> bool:
        region = (primary_x, primary_y, mode)
        if region in active_regions:
            raise AssertionError("worker overlap detected")

        active_regions.add(region)
        calls.append(region)
        active_regions.remove(region)
        return True

    workers.perform_polculture_transaction = transaction

    if not workers.run_polculture_worker_for_cycles((0, 0, workers.HAY_MODE), 1000):
        raise AssertionError("persistent worker did not finish 1,000 transactions")
    if len(calls) != 1000:
        raise AssertionError(f"worker transaction count changed: {len(calls)}")
    if active_regions:
        raise AssertionError("worker left an active ownership record")


def test_worker_capacity_and_parent_fallback() -> None:
    workers.get_primary_positions = lambda _world_size, _mode: [
        (0, 0),
        (8, 0),
        (0, 8),
    ]
    workers.max_drones = lambda: 2
    spawned = []

    def spawn_worker(function, job):
        spawned.append((function, job))
        return "worker"

    workers.spawn_drone = spawn_worker
    jobs = workers.get_polculture_worker_jobs(32, workers.HAY_MODE)
    if jobs != [(0, 0, workers.HAY_MODE), (8, 0, workers.HAY_MODE)]:
        raise AssertionError(f"worker capacity was not bounded: {jobs}")

    parent_jobs, handles = workers.start_polculture_workers(jobs)
    if parent_jobs != [(8, 0, workers.HAY_MODE)] or handles != ["worker"]:
        raise AssertionError("persistent worker ownership changed")

    workers.spawn_drone = lambda _function, _job: None
    parent_jobs, handles = workers.start_polculture_workers(jobs)
    if parent_jobs != jobs or handles:
        raise AssertionError("spawn failure did not return work to the parent")


def test_worker_manager_has_no_global_correctness_state() -> None:
    source = (SAVE_DIRECTORY / "achievement_polyculture.py").read_text()
    if "global " in source:
        raise AssertionError("polyculture worker correctness uses module globals")
    if "dispatch_indexed_jobs" in source:
        raise AssertionError("persistent workers still use farm-wide dispatch joins")


def main() -> None:
    test_scheduler_runs_one_thousand_owned_transactions()
    test_worker_capacity_and_parent_fallback()
    test_worker_manager_has_no_global_correctness_state()
    print("Passed persistent polyculture ownership, capacity, fallback, and scheduler tests")


if __name__ == "__main__":
    main()
