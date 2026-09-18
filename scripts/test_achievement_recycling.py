#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the finite Recycling achievement launcher."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
RUNNER = SAVE_DIRECTORY / "run_achievement_recycling.py"


def test_finite_single_worker_wrapper() -> None:
    source = RUNNER.read_text()
    tree = ast.parse(source)
    imports = [
        (node.module, [alias.name for alias in node.names])
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    if imports != [("achievement_maze", ["run_reusable_maze_worker"])]:
        raise AssertionError(f"Recycling imports changed: {imports}")
    if any(isinstance(node, (ast.For, ast.AsyncFor, ast.While)) for node in ast.walk(tree)):
        raise AssertionError("Recycling runner must be finite")

    worker_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_reusable_maze_worker"
    ]
    if len(worker_calls) != 1:
        raise AssertionError("Recycling runner must perform one reusable maze run")
    if [ast.literal_eval(argument) for argument in worker_calls[0].args] != [0, 300]:
        raise AssertionError("Recycling runner changed its small-maze reuse limit")

    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if calls != {"run_reusable_maze_worker", "quick_print", "str"}:
        raise AssertionError(f"Recycling runner performs unrelated work: {calls}")
    if "farm_mazes" in source or "Items.Gold" in source:
        raise AssertionError("Recycling runner contains unrelated gold farming")


def main() -> None:
    test_finite_single_worker_wrapper()
    print("Passed finite Recycling worker, 300-limit, single-diagnostic, and isolation tests")


if __name__ == "__main__":
    main()
