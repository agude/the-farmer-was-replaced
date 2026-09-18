#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the continuous Maze Master runner boundary."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
RUNNER = SAVE_DIRECTORY / "run_achievement_maze.py"


def test_runner_delegates_parallel_workers_and_reports_delta() -> None:
    source = RUNNER.read_text()
    tree = ast.parse(source)
    loops = [node for node in tree.body if isinstance(node, ast.While)]
    if len(loops) != 1:
        raise AssertionError("Maze runner must have one top-level loop")
    loop = loops[0]
    if not isinstance(loop.test, ast.Constant) or loop.test.value is not True:
        raise AssertionError("Maze runner must remain continuous")

    imports = {
        (node.module, alias.name)
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    expected_imports = {
        ("achievement_maze", "run_maze_workers"),
        ("achievement_metrics", "get_elapsed_time"),
        ("achievement_metrics", "get_item_delta"),
        ("achievement_metrics", "get_items_per_minute"),
        ("achievement_metrics", "start_item_measurement"),
        ("achievement_metrics", "start_time_measurement"),
    }
    if imports != expected_imports:
        raise AssertionError(f"Maze runner imports changed: {imports}")

    worker_calls = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_maze_workers"
    ]
    if len(worker_calls) != 1:
        raise AssertionError("Maze runner must invoke the parallel manager once per loop")
    if not any(isinstance(node, ast.Break) for node in ast.walk(loop)):
        raise AssertionError("Maze runner has no visible failure exit")

    forbidden = {
        "clear",
        "farm_mazes",
        "harvest",
        "plant",
        "spawn_drone",
        "use_item",
    }
    calls = {
        node.func.id
        for node in ast.walk(loop)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if calls & forbidden:
        raise AssertionError(f"Maze runner performs unrelated work: {calls & forbidden}")
    if "Items.Gold" not in source or "get_item_delta" not in source:
        raise AssertionError("Maze runner lost Gold delta accounting")
    if "get_elapsed_time" not in source or "starting_time" not in source:
        raise AssertionError("Maze runner lost elapsed-time diagnostics")
    if "elapsed_seconds" not in source or " seconds" not in source:
        raise AssertionError("Maze runner does not label game time in seconds")
    if "get_items_per_minute" not in source or "gold_per_minute" not in source:
        raise AssertionError("Maze runner lost Gold rate diagnostics")
    if "elapsed_ticks" in source or " ticks" in source:
        raise AssertionError("Maze runner mislabels game time as ticks")


def main() -> None:
    test_runner_delegates_parallel_workers_and_reports_delta()
    print("Passed Maze Master manager, Gold delta, elapsed-time, failure, and hot-loop tests")


if __name__ == "__main__":
    main()
