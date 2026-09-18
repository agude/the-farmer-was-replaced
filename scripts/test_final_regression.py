#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Run final import-safety and entry-point inventory checks."""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

IMPLEMENTATION_MODULES = (
    "achievement_config",
    "achievement_healer",
    "achievement_metrics",
    "achievement_cactus",
    "achievement_pumpkin",
    "achievement_dinosaur",
    "achievement_polyculture",
    "achievement_maze",
    "reset_farmers",
    "reset_progression",
    "leaderboard_runs",
)
SPECIAL_ENTRY_POINTS = {
    "run_leaderboard_cactus.py": "leaderboard_run",
    "run_leaderboard_reset.py": "leaderboard_run",
    "run_simulate_fastest_reset.py": "simulate",
    "run_simulation_reset.py": "simulate",
}
FORBIDDEN_IMPORT_CALLS = {
    "clear",
    "harvest",
    "leaderboard_run",
    "plant",
    "simulate",
    "spawn_drone",
    "use_item",
}


def test_implementation_modules_import_without_farm_actions() -> None:
    for module_name in IMPLEMENTATION_MODULES:
        importlib.import_module(module_name)

        source = (SAVE_DIRECTORY / (module_name + ".py")).read_text()
        tree = ast.parse(source)
        for statement in tree.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for node in ast.walk(statement):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_IMPORT_CALLS:
                    raise AssertionError(f"{module_name} performs {node.func.id} at import time")


def test_special_entry_points_are_parseable_and_explicit() -> None:
    for filename, call_name in SPECIAL_ENTRY_POINTS.items():
        source = (SAVE_DIRECTORY / filename).read_text()
        tree = ast.parse(source)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == call_name
        ]
        if len(calls) != 1:
            raise AssertionError(f"{filename} does not have one {call_name} call")


def test_runner_inventory_contains_new_continuous_entries() -> None:
    source = (SAVE_DIRECTORY.parent / "scripts" / "test_runners.py").read_text()
    for filename in (
        "run_achievement_hay.py",
        "run_achievement_carrots.py",
        "run_achievement_maze.py",
        "run_achievement_recycling.py",
    ):
        if filename not in source:
            raise AssertionError(f"runner inventory omitted {filename}")


def main() -> None:
    test_implementation_modules_import_without_farm_actions()
    test_special_entry_points_are_parseable_and_explicit()
    test_runner_inventory_contains_new_continuous_entries()
    print(
        "Passed final implementation import, special entry-point, and runner inventory regression tests"
    )


if __name__ == "__main__":
    main()
