#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify Carrot Master startup funding and runner boundaries."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
RUNNER = SAVE_DIRECTORY / "run_achievement_carrots.py"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_polyculture as polyculture  # noqa: E402


class Entities:
    Carrot = "Carrot"
    Grass = "Grass"
    Bush = "Bush"
    Tree = "Tree"


class Items:
    Hay = "Hay"
    Wood = "Wood"


def install_cost_simulator(inventory: dict[str, int]) -> None:
    polyculture.Entities = Entities
    polyculture.Items = Items
    polyculture.get_primary_positions = lambda _world_size, _mode: [(3, 3), (11, 3)]
    polyculture.max_drones = lambda: 2
    polyculture.get_cost = lambda entity: {
        Entities.Carrot: {Items.Hay: 1},
        Entities.Grass: {},
        Entities.Bush: {},
        Entities.Tree: {Items.Wood: 1},
    }[entity]
    polyculture.num_items = lambda item: inventory.get(item, 0)


def test_startup_requirement_uses_worst_dynamic_companion() -> None:
    inventory = {Items.Hay: 4, Items.Wood: 2}
    install_cost_simulator(inventory)

    required = polyculture.get_carrot_startup_requirements(32)
    if required != {Items.Hay: 4, Items.Wood: 2}:
        raise AssertionError(f"startup budget was not worst-case bounded: {required}")
    if not polyculture.can_fund_carrot_startup(32):
        raise AssertionError("exact startup budget was rejected")

    inventory[Items.Wood] = 1
    if polyculture.can_fund_carrot_startup(32):
        raise AssertionError("underfunded startup batch was accepted")


def get_runner_loop(tree: ast.Module) -> ast.While:
    loops = [node for node in tree.body if isinstance(node, ast.While)]
    if len(loops) != 1:
        raise AssertionError("Carrot runner must have exactly one top-level loop")

    loop = loops[0]
    if not isinstance(loop.test, ast.Constant) or loop.test.value is not True:
        raise AssertionError("Carrot runner must remain continuous")
    return loop


def test_runner_delegates_carrot_mode_and_preflights() -> None:
    tree = ast.parse(RUNNER.read_text())
    loop = get_runner_loop(tree)
    imports = {
        (node.module, alias.name)
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    expected_imports = {
        ("achievement_metrics", "get_item_delta"),
        ("achievement_metrics", "start_item_measurement"),
        ("achievement_polyculture", "CARROT_MODE"),
        ("achievement_polyculture", "can_fund_carrot_startup"),
        ("achievement_polyculture", "run_polculture_workers"),
    }
    if imports != expected_imports:
        raise AssertionError(f"Carrot runner imports changed: {imports}")

    preflight_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "can_fund_carrot_startup"
    ]
    if len(preflight_calls) != 1 or any(node in ast.walk(loop) for node in preflight_calls):
        raise AssertionError("Carrot startup preflight moved into the worker loop")

    worker_calls = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_polculture_workers"
    ]
    if len(worker_calls) != 1:
        raise AssertionError("Carrot runner must invoke the worker manager once per loop")
    if (
        not isinstance(worker_calls[0].args[1], ast.Name)
        or worker_calls[0].args[1].id != "CARROT_MODE"
    ):
        raise AssertionError("Carrot runner selected the wrong polyculture mode")

    if not any(isinstance(node, ast.Break) for node in ast.walk(loop)):
        raise AssertionError("Carrot runner has no failure exit")


def main() -> None:
    test_startup_requirement_uses_worst_dynamic_companion()
    test_runner_delegates_carrot_mode_and_preflights()
    print("Passed Carrot Master startup budget, mode, preflight, and runner tests")


if __name__ == "__main__":
    main()
