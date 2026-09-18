#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise independent achievement maze worker scheduling."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_maze as workers  # noqa: E402


def result(reason, completed=0):
    return {"reason": reason, "completed": completed}


def test_startup_caps_workers_and_returns_spawn_failures_to_parent() -> None:
    jobs = [(0, 0, 0), (1, 4, 0), (2, 8, 0)]
    spawned = []

    def spawn(_function, job):
        spawned.append(job)
        if job[0] == 1:
            return None
        return "handle-" + str(job[0])

    workers.spawn_drone = spawn
    parent_jobs, handles = workers.start_maze_workers(jobs)
    if parent_jobs != [jobs[1], jobs[2]]:
        raise AssertionError(f"spawn failure lost parent ownership: {parent_jobs}")
    if handles != ["handle-0"] or spawned != [jobs[0], jobs[1]]:
        raise AssertionError("maze worker startup changed its spawn ownership")


def test_parent_failures_do_not_stop_healthy_parent_jobs() -> None:
    jobs = [(0, 0, 0), (1, 4, 0), (2, 8, 0)]
    calls = []
    messages = []

    def run_worker(maze_index):
        calls.append(maze_index)
        return result("failed", 7)

    workers.run_reusable_maze_worker = run_worker
    workers.quick_print = lambda message: messages.append(message)
    if not workers.run_maze_parent_jobs(jobs):
        raise AssertionError("parent scheduler reported failure after removing failed jobs")
    if calls != [2, 1, 0]:
        raise AssertionError(f"parent scheduler stopped before healthy jobs ran: {calls}")
    if len(messages) != len(jobs):
        raise AssertionError("parent scheduler did not expose every failed worker")


def test_persistent_child_replaces_completed_maze() -> None:
    calls = []
    messages = []

    def run_worker(maze_index):
        calls.append(maze_index)
        if len(calls) == 1:
            return result(workers.MAZE_WORKER_COMPLETE, 300)
        return result("blocked", 4)

    workers.run_reusable_maze_worker = run_worker
    workers.quick_print = lambda message: messages.append(message)
    if workers.run_maze_worker((5, 20, 0)):
        raise AssertionError("failed persistent child reported success")
    if calls != [5, 5] or len(messages) != 1:
        raise AssertionError("persistent child did not replace and then report its maze")


def test_scheduler_has_no_shared_correctness_state() -> None:
    source = (SAVE_DIRECTORY / "achievement_maze.py").read_text()
    if "global " in source:
        raise AssertionError("maze scheduler uses module-global correctness state")
    if "dispatch_indexed_jobs" in source:
        raise AssertionError("maze scheduler uses a farm-wide dispatch barrier")


def main() -> None:
    test_startup_caps_workers_and_returns_spawn_failures_to_parent()
    test_parent_failures_do_not_stop_healthy_parent_jobs()
    test_persistent_child_replaces_completed_maze()
    test_scheduler_has_no_shared_correctness_state()
    print(
        "Passed independent maze startup, fallback, failure isolation, replacement, and scheduler tests"
    )


if __name__ == "__main__":
    main()
