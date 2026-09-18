#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the selectable Cactus Master runner boundary."""

from __future__ import annotations

import ast
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "Save0" / "run_achievement_cactus.py"


def test_runner_is_a_thin_continuous_wrapper() -> None:
    tree = ast.parse(RUNNER.read_text())
    imports = []

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            imports.append((node.module, [alias.name for alias in node.names]))

    if ("achievement_cactus", ["farm_achievement_cactus_cycle"]) not in imports:
        raise AssertionError("Cactus Master runner does not import its achievement operation")
    if ("achievement_metrics", ["get_item_delta"]) not in imports:
        raise AssertionError("Cactus Master runner does not import its delta helper")
    if ("achievement_metrics", ["start_item_measurement"]) not in imports:
        raise AssertionError("Cactus Master runner does not start its own measurement")

    loops = [node for node in tree.body if isinstance(node, ast.While)]
    if (
        len(loops) != 1
        or not isinstance(loops[0].test, ast.Constant)
        or loops[0].test.value is not True
    ):
        raise AssertionError("Cactus Master runner is not continuously cycling")

    calls = [
        node.func.id
        for node in ast.walk(loops[0])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    if "farm_achievement_cactus_cycle" not in calls:
        raise AssertionError("Cactus Master runner never starts a cycle")
    if "quick_print" not in calls or not any(
        isinstance(node, ast.Break) for node in ast.walk(loops[0])
    ):
        raise AssertionError("Cactus Master runner has no visible cycle failure exit")


def test_runner_does_not_fertilize_the_final_harvest() -> None:
    tree = ast.parse(RUNNER.read_text())
    forbidden_calls = {"fertilize_before_harvest", "use_item"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in forbidden_calls:
                raise AssertionError(f"Cactus Master runner performs {node.func.id}")


def main() -> None:
    test_runner_is_a_thin_continuous_wrapper()
    test_runner_does_not_fertilize_the_final_harvest()
    print("Passed Cactus Master runner, delta, failure-exit, and harvest-policy tests")


if __name__ == "__main__":
    main()
