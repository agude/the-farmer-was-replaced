#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the isolated Circular Import achievement graph without importing it."""

from __future__ import annotations

import ast
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
CYCLE_MODULES = {
    "achievement_import_cycle_a.py": "achievement_import_cycle_b",
    "achievement_import_cycle_b.py": "achievement_import_cycle_a",
}
ENTRY_POINT = "run_achievement_import.py"


def get_imported_modules(filename: str) -> list[str]:
    tree = ast.parse((SAVE_DIRECTORY / filename).read_text())
    imported_modules = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)

    return imported_modules


def test_cycle_is_exactly_two_modules() -> None:
    for filename, expected_import in CYCLE_MODULES.items():
        imports = get_imported_modules(filename)
        if imports != [expected_import]:
            raise AssertionError(f"{filename} changed the intentional cycle: {imports}")


def test_entry_point_starts_the_cycle() -> None:
    imports = get_imported_modules(ENTRY_POINT)
    if imports != ["achievement_import_cycle_a"]:
        raise AssertionError(f"entry point changed its cycle trigger: {imports}")


def test_cycle_has_no_game_work() -> None:
    forbidden_calls = {"clear", "harvest", "plant", "simulate", "spawn_drone", "use_item"}

    for filename in CYCLE_MODULES:
        tree = ast.parse((SAVE_DIRECTORY / filename).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in forbidden_calls:
                    raise AssertionError(f"{filename} performs game work")


def test_production_modules_do_not_import_cycle() -> None:
    for path in SAVE_DIRECTORY.glob("*.py"):
        if path.name in set(CYCLE_MODULES) | {ENTRY_POINT, "__builtins__.py"}:
            continue

        imports = get_imported_modules(path.name)
        for module in imports:
            if module in {"achievement_import_cycle_a", "achievement_import_cycle_b"}:
                raise AssertionError(f"{path.name} imports the isolated cycle")


def main() -> None:
    test_cycle_is_exactly_two_modules()
    test_entry_point_starts_the_cycle()
    test_cycle_has_no_game_work()
    test_production_modules_do_not_import_cycle()
    print("Passed isolated Circular Import graph and production-boundary tests")


if __name__ == "__main__":
    main()
