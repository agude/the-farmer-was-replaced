#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the intentional Stack Overflow entry point without executing it."""

from __future__ import annotations

import ast
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "Save0" / "run_achievement_stack_overflow.py"
FORBIDDEN_GAME_ACTIONS = {
    "change_hat",
    "clear",
    "harvest",
    "plant",
    "simulate",
    "spawn_drone",
    "use_item",
}


def test_direct_unbounded_recursion() -> None:
    source = RUNNER.read_text()
    tree = ast.parse(source)
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "overflow"
        ),
        None,
    )

    if function is None:
        raise AssertionError("Stack Overflow runner has no overflow function")

    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "overflow"
        for node in ast.walk(function)
    ):
        raise AssertionError("Stack Overflow runner is not recursive")

    if "runtime error is intentional" not in source:
        raise AssertionError("Stack Overflow runner lacks its intentional-error comment")


def test_no_field_or_inventory_actions() -> None:
    tree = ast.parse(RUNNER.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_GAME_ACTIONS:
                raise AssertionError(f"Stack Overflow runner performs {node.func.id}")


def main() -> None:
    test_direct_unbounded_recursion()
    test_no_field_or_inventory_actions()
    print("Passed intentional Stack Overflow recursion and isolation tests")


if __name__ == "__main__":
    main()
