#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the Hay Master runner delegates to persistent polyculture workers."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
RUNNER = SAVE_DIRECTORY / "run_achievement_hay.py"


def get_loop(tree: ast.Module) -> ast.While:
    loops = [node for node in tree.body if isinstance(node, ast.While)]
    if len(loops) != 1:
        raise AssertionError("Hay runner must have exactly one top-level loop")

    loop = loops[0]
    if not isinstance(loop.test, ast.Constant) or loop.test.value is not True:
        raise AssertionError("Hay runner must remain continuous")
    return loop


def get_call_names(tree: ast.AST) -> set[str]:
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def test_runner_delegates_hay_mode() -> None:
    tree = ast.parse(RUNNER.read_text())
    loop = get_loop(tree)
    imports = {
        (node.module, alias.name)
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    expected_imports = {
        ("achievement_metrics", "get_item_delta"),
        ("achievement_metrics", "start_item_measurement"),
        ("achievement_polyculture", "HAY_MODE"),
        ("achievement_polyculture", "run_polculture_workers"),
    }
    if imports != expected_imports:
        raise AssertionError(f"Hay runner imports changed: {imports}")

    worker_calls = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_polculture_workers"
    ]
    if len(worker_calls) != 1:
        raise AssertionError("Hay runner must invoke the worker manager once per loop")

    worker_call = worker_calls[0]
    if len(worker_call.args) != 2 or not isinstance(worker_call.args[1], ast.Name):
        raise AssertionError("Hay runner did not pass a mode to the worker manager")
    if worker_call.args[1].id != "HAY_MODE":
        raise AssertionError("Hay runner selected the wrong polyculture mode")

    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "quick_print"
        for node in ast.walk(loop)
    ):
        raise AssertionError("Hay runner has no visible failure diagnostic")
    if not any(isinstance(node, ast.Break) for node in ast.walk(loop)):
        raise AssertionError("Hay runner does not exit after worker failure")


def test_runner_keeps_hot_loop_free_of_setup_actions() -> None:
    tree = ast.parse(RUNNER.read_text())
    loop = get_loop(tree)
    forbidden = {
        "clear",
        "harvest",
        "plant",
        "spawn_drone",
        "till",
        "use_item",
    }
    calls = get_call_names(loop)
    if calls & forbidden:
        raise AssertionError(f"Hay runner performs setup work in its loop: {calls & forbidden}")

    if any(isinstance(node, (ast.For, ast.AsyncFor, ast.While)) for node in ast.walk(loop.body[0])):
        raise AssertionError("Hay runner added a full-field or nested hot-loop scan")


def main() -> None:
    test_runner_delegates_hay_mode()
    test_runner_keeps_hot_loop_free_of_setup_actions()
    print("Passed Hay Master runner delegation, mode, failure, and hot-loop tests")


if __name__ == "__main__":
    main()
