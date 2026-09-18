#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the finite Healer entry point without executing game code."""

from __future__ import annotations

import ast
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "Save0" / "run_achievement_healer.py"


def get_operation() -> ast.FunctionDef:
    tree = ast.parse(RUNNER.read_text())

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_healer":
            return node

    raise AssertionError("Healer entry point has no run_healer operation")


def get_call_names(operation: ast.FunctionDef) -> list[str]:
    return [
        node.func.id
        for node in ast.walk(operation)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]


def test_preflight_happens_before_planting() -> None:
    operation = get_operation()
    statements = operation.body
    first_plant = next(
        index
        for index, statement in enumerate(statements)
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "plant"
            for node in ast.walk(statement)
        )
    )
    preflight_source = ast.unparse(ast.Module(body=statements[:first_plant], type_ignores=[]))

    if "Items.Fertilizer" not in preflight_source:
        raise AssertionError("Fertilizer was not checked before modifying the field")
    if "Items.Weird_Substance" not in preflight_source:
        raise AssertionError("Weird Substance was not checked before modifying the field")


def test_same_grass_plant_is_fertilized_and_cured() -> None:
    operation = get_operation()
    source = ast.unparse(operation)
    calls = get_call_names(operation)

    if calls.count("use_item") != 2:
        raise AssertionError("Healer must use exactly one fertilizer and one Weird Substance")
    if "plant(Entities.Grass)" not in source:
        raise AssertionError("Healer does not establish the harmless grass test plant")
    if source.count("get_entity_type() != Entities.Grass") < 3:
        raise AssertionError("Healer does not verify the same living plant at each stage")


def test_failures_are_visible_and_field_is_not_cleared() -> None:
    operation = get_operation()
    calls = get_call_names(operation)

    if calls.count("quick_print") < 2:
        raise AssertionError("Healer has no direct diagnostics for failure and success")
    if "clear" in calls or "harvest" in calls:
        raise AssertionError("Healer must not clear or harvest the field")


def main() -> None:
    test_preflight_happens_before_planting()
    test_same_grass_plant_is_fertilized_and_cured()
    test_failures_are_visible_and_field_is_not_cleared()
    print("Passed Healer preflight, same-plant, failure, and isolation tests")


if __name__ == "__main__":
    main()
