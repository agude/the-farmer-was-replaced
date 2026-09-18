#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the finite Cactus leaderboard operation and launcher."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import leaderboard_runs as leaderboard  # noqa: E402


class Items:
    Cactus = "Cactus"


def test_operation_terminates_at_the_board_goal() -> None:
    inventory = {Items.Cactus: leaderboard.CACTUS_LEADERBOARD_TARGET - 1}
    calls = []
    leaderboard.Items = Items
    leaderboard.num_items = lambda item: inventory[item]

    def farm_cycle() -> bool:
        calls.append("cycle")
        inventory[Items.Cactus] += 1
        return True

    leaderboard.farm_achievement_cactus_cycle = farm_cycle
    if not leaderboard.run_leaderboard_cactus():
        raise AssertionError("operation did not report board-goal success")
    if calls != ["cycle"]:
        raise AssertionError("operation did not stop immediately at the board goal")


def test_operation_stops_on_cycle_failure() -> None:
    inventory = {Items.Cactus: 0}
    calls = []
    leaderboard.num_items = lambda item: inventory[item]

    def failed_cycle() -> bool:
        calls.append("cycle")
        return False

    leaderboard.farm_achievement_cactus_cycle = failed_cycle
    if leaderboard.run_leaderboard_cactus():
        raise AssertionError("failed cactus cycle reported success")
    if calls != ["cycle"]:
        raise AssertionError("failed cactus cycle did not terminate the operation")


def test_operation_and_launcher_boundaries() -> None:
    operation_source = (SAVE_DIRECTORY / "leaderboard_runs.py").read_text()
    operation_tree = ast.parse(operation_source)
    imports = [
        (node.module, [alias.name for alias in node.names])
        for node in operation_tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    if imports != [("achievement_cactus", ["farm_achievement_cactus_cycle"])]:
        raise AssertionError(f"leaderboard operation imports changed: {imports}")
    if "run_achievement_cactus" in operation_source:
        raise AssertionError("leaderboard operation imports an executable achievement runner")

    operation = next(
        node
        for node in operation_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_leaderboard_cactus"
    )
    if not any(
        isinstance(node, ast.While) and isinstance(node.test, ast.Compare)
        for node in ast.walk(operation)
    ):
        raise AssertionError("leaderboard operation lost its target loop")

    launcher_source = (SAVE_DIRECTORY / "run_leaderboard_cactus.py").read_text()
    launcher_tree = ast.parse(launcher_source)
    calls = [
        node
        for node in ast.walk(launcher_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "leaderboard_run"
    ]
    if len(calls) != 1:
        raise AssertionError("leaderboard launcher must make one leaderboard_run call")
    call = calls[0]
    if len(call.args) != 3:
        raise AssertionError("leaderboard launcher changed the leaderboard_run signature")
    if not (
        isinstance(call.args[0], ast.Attribute)
        and isinstance(call.args[0].value, ast.Name)
        and call.args[0].value.id == "Leaderboards"
        and call.args[0].attr == "Cactus"
    ):
        raise AssertionError("leaderboard launcher selected the wrong board")
    if not isinstance(call.args[1], ast.Name) or call.args[1].id != "LEADERBOARD_FILE":
        raise AssertionError("leaderboard launcher changed the submitted file setting")
    if not isinstance(call.args[2], ast.Name) or call.args[2].id != "LEADERBOARD_SPEEDUP":
        raise AssertionError("leaderboard launcher lost configurable speedup")


def main() -> None:
    test_operation_terminates_at_the_board_goal()
    test_operation_stops_on_cycle_failure()
    test_operation_and_launcher_boundaries()
    print("Passed Cactus leaderboard target, termination, import, file, and speedup tests")


if __name__ == "__main__":
    main()
