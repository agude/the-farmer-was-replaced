#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the guarded Fastest Reset submitted window and launcher."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import reset_progression as reset  # noqa: E402


class Unlocks:
    Grass = "Grass"
    Plant = "Plant"
    Leaderboard = "Leaderboard"


def test_progression_stops_when_leaderboard_is_already_unlocked() -> None:
    reset.Unlocks = Unlocks
    reset.num_unlocked = lambda unlock: 1 if unlock == Unlocks.Leaderboard else 0
    reset.get_unlock_plan = lambda: (_ for _ in ()).throw(
        AssertionError("reset progression continued after Leaderboard")
    )
    if not reset.run_reset_progression():
        raise AssertionError("already-unlocked Leaderboard was not a success")


def test_submitted_window_is_guarded_and_has_one_success_condition() -> None:
    source = (SAVE_DIRECTORY / "reset_progression.py").read_text()
    tree = ast.parse(source)
    if "leaderboard_run" in source:
        raise AssertionError("submitted reset window can start a nested leaderboard run")
    if "is_blank_reset_environment" not in source:
        raise AssertionError("submitted reset window lost its blank-state guard")

    progression = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_reset_progression"
    )
    leaderboard_checks = [
        node
        for node in ast.walk(progression)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id == "Unlocks"
            and value.attr == "Leaderboard"
            for value in ast.walk(node)
        )
    ]
    if not leaderboard_checks:
        raise AssertionError("reset progression has no Leaderboard success condition")


def test_launcher_selects_fastest_reset_and_submitted_window() -> None:
    source = (SAVE_DIRECTORY / "run_leaderboard_reset.py").read_text()
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "leaderboard_run"
    ]
    if len(calls) != 1:
        raise AssertionError("Fastest Reset launcher must make one leaderboard_run call")
    call = calls[0]
    if len(call.args) != 3:
        raise AssertionError("Fastest Reset launcher changed leaderboard_run arguments")
    if not (
        isinstance(call.args[0], ast.Attribute)
        and isinstance(call.args[0].value, ast.Name)
        and call.args[0].value.id == "Leaderboards"
        and call.args[0].attr == "Fastest_Reset"
    ):
        raise AssertionError("Fastest Reset launcher selected the wrong board")
    if not isinstance(call.args[1], ast.Name) or call.args[1].id != "LEADERBOARD_FILE":
        raise AssertionError("Fastest Reset launcher changed the submitted window")
    if not isinstance(call.args[2], ast.Name) or call.args[2].id != "LEADERBOARD_SPEEDUP":
        raise AssertionError("Fastest Reset launcher lost configurable speedup")


def main() -> None:
    test_progression_stops_when_leaderboard_is_already_unlocked()
    test_submitted_window_is_guarded_and_has_one_success_condition()
    test_launcher_selects_fastest_reset_and_submitted_window()
    print("Passed guarded reset window, Leaderboard termination, and Fastest Reset launcher tests")


if __name__ == "__main__":
    main()
