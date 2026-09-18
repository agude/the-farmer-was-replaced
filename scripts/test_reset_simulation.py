#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the isolated Fastest Reset simulation launcher."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
LAUNCHER = SAVE_DIRECTORY / "run_simulate_fastest_reset.py"
SEED_MATRIX_LAUNCHER = SAVE_DIRECTORY / "run_simulation_reset.py"


def test_simulation_uses_one_configurable_empty_start() -> None:
    source = LAUNCHER.read_text()
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "simulate"
    ]
    if len(calls) != 1:
        raise AssertionError("reset rehearsal must make one simulate call")

    call = calls[0]
    expected_arguments = [
        "SIMULATION_FILE",
        "SIMULATION_UNLOCKS",
        "SIMULATION_ITEMS",
        "SIMULATION_GLOBALS",
        "SIMULATION_SEED",
        "SIMULATION_SPEEDUP",
    ]
    actual_arguments = [
        argument.id if isinstance(argument, ast.Name) else None for argument in call.args
    ]
    if actual_arguments != expected_arguments:
        raise AssertionError(f"reset rehearsal arguments changed: {actual_arguments}")

    assignments = {
        statement.targets[0].id: statement.value
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    for name in ("SIMULATION_UNLOCKS", "SIMULATION_ITEMS", "SIMULATION_GLOBALS"):
        value = assignments.get(name)
        if not isinstance(value, ast.Dict) or value.keys:
            raise AssertionError(f"{name} is not an empty simulation input")
    if not isinstance(assignments["SIMULATION_SEED"], ast.Constant):
        raise AssertionError("simulation seed is not fixed in one obvious location")
    if not isinstance(assignments["SIMULATION_SPEEDUP"], ast.Constant):
        raise AssertionError("simulation speedup is not configurable in one obvious location")


def test_launcher_prints_once_and_does_not_nest_simulation() -> None:
    source = LAUNCHER.read_text()
    tree = ast.parse(source)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "quick_print"
    ]
    if len(print_calls) != 1:
        raise AssertionError("reset rehearsal must print the simulated runtime once")
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if calls - {"simulate", "quick_print"}:
        raise AssertionError(f"reset rehearsal performs live or nested work: {calls}")

    forbidden_text = {"leaderboard_run", "clear", "plant", "harvest", "unlock("}
    if any(token in source for token in forbidden_text):
        raise AssertionError("reset rehearsal is coupled to live or leaderboard execution")


def test_seed_matrix_runs_all_required_seeds() -> None:
    source = SEED_MATRIX_LAUNCHER.read_text()
    tree = ast.parse(source)
    assignments = {
        statement.targets[0].id: statement.value
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }
    seeds = assignments.get("SIMULATION_SEEDS")
    if not isinstance(seeds, ast.List) or [element.value for element in seeds.elts] != list(
        range(1, 11)
    ):
        raise AssertionError("seed matrix does not contain exactly seeds 1 through 10")

    loops = [node for node in tree.body if isinstance(node, ast.For)]
    if len(loops) != 1:
        raise AssertionError("seed matrix must use one bounded seed loop")
    loop = loops[0]
    if not isinstance(loop.target, ast.Name) or loop.target.id != "simulation_seed":
        raise AssertionError("seed matrix loop target changed")
    if not isinstance(loop.iter, ast.Name) or loop.iter.id != "SIMULATION_SEEDS":
        raise AssertionError("seed matrix loop does not use SIMULATION_SEEDS")

    calls = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "simulate"
    ]
    if len(calls) != 1 or len(calls[0].args) != 6:
        raise AssertionError("seed matrix must make one six-argument simulate call")
    for argument in calls[0].args[1:4]:
        if not isinstance(argument, ast.Dict) or argument.keys:
            raise AssertionError("seed matrix does not provide fresh empty simulation state")
    if not isinstance(calls[0].args[4], ast.Name) or calls[0].args[4].id != "simulation_seed":
        raise AssertionError("seed matrix does not pass the loop seed to simulate")

    print_calls = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "quick_print"
    ]
    if len(print_calls) != 1:
        raise AssertionError("seed matrix must print one result for every seed")


def main() -> None:
    test_simulation_uses_one_configurable_empty_start()
    test_launcher_prints_once_and_does_not_nest_simulation()
    test_seed_matrix_runs_all_required_seeds()
    print("Passed isolated Fastest Reset inputs, speedup, output, and ten-seed launcher tests")


if __name__ == "__main__":
    main()
