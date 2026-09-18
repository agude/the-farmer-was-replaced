#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the finite Healer operation against modeled field states."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_healer  # noqa: E402


class Entities:
    Grass = "Grass"
    Tree = "Tree"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Items:
    Fertilizer = "Fertilizer"
    Weird_Substance = "Weird Substance"


class HealerSimulator:
    def __init__(self, ground: str, entity: str | None) -> None:
        self.world_size = 3
        self.position = (1, 1)
        self.ground = ground
        self.entity = entity
        self.inventory = {
            Items.Fertilizer: 1,
            Items.Weird_Substance: 1,
        }
        self.events: list[str] = []

    def install(self) -> None:
        achievement_healer.East = "East"
        achievement_healer.West = "West"
        achievement_healer.North = "North"
        achievement_healer.South = "South"
        achievement_healer.Entities = Entities
        achievement_healer.Grounds = Grounds
        achievement_healer.Items = Items
        achievement_healer.get_world_size = lambda: self.world_size
        achievement_healer.move = self.move
        achievement_healer.get_entity_type = lambda: self.entity
        achievement_healer.get_ground_type = lambda: self.ground
        achievement_healer.till = self.till
        achievement_healer.clear = self.clear
        achievement_healer.plant = self.plant
        achievement_healer.num_items = lambda item: self.inventory[item]
        achievement_healer.use_item = self.use_item
        achievement_healer.quick_print = self.quick_print

    def move(self, direction: str) -> bool:
        x, y = self.position
        if direction == "East":
            x = (x + 1) % self.world_size
        elif direction == "West":
            x = (x - 1) % self.world_size
        elif direction == "North":
            y = (y + 1) % self.world_size
        else:
            y = (y - 1) % self.world_size
        self.position = (x, y)
        return True

    def till(self) -> None:
        self.events.append("till")
        self.ground = Grounds.Grassland

    def clear(self) -> None:
        self.events.append("clear")
        self.entity = None

    def plant(self, entity: str) -> bool:
        self.events.append("plant")
        if self.ground != Grounds.Grassland or self.entity is not None:
            return False
        self.entity = entity
        return True

    def use_item(self, item: str) -> bool:
        self.events.append("use_item")
        if self.inventory[item] <= 0:
            return False
        self.inventory[item] -= 1
        return True

    def quick_print(self, message: str) -> None:
        self.events.append(message)


def test_soil_tile_is_tilled_before_grass_is_planted() -> None:
    simulator = HealerSimulator(Grounds.Soil, None)
    simulator.install()

    if not achievement_healer.prepare_healer_tile():
        raise AssertionError("Soil tile preparation failed")
    if simulator.events != ["till", "plant"]:
        raise AssertionError(f"Soil tile used the wrong setup sequence: {simulator.events}")


def test_grassland_tile_is_planted_without_tilling() -> None:
    simulator = HealerSimulator(Grounds.Grassland, None)
    simulator.install()

    if not achievement_healer.prepare_healer_tile():
        raise AssertionError("Grassland tile preparation failed")
    if simulator.events != ["plant"]:
        raise AssertionError(f"Grassland tile was tilled unexpectedly: {simulator.events}")


def test_occupied_tile_is_cleared_before_replacement() -> None:
    simulator = HealerSimulator(Grounds.Grassland, Entities.Tree)
    simulator.install()

    if not achievement_healer.prepare_healer_tile():
        raise AssertionError("Occupied tile preparation failed")
    if simulator.events != ["clear", "plant"]:
        raise AssertionError(f"Occupied tile used the wrong setup sequence: {simulator.events}")


def test_existing_grass_is_reused_and_setup_is_idempotent() -> None:
    simulator = HealerSimulator(Grounds.Grassland, Entities.Grass)
    simulator.install()

    if not achievement_healer.prepare_healer_tile():
        raise AssertionError("Existing Grass tile was rejected")
    if not achievement_healer.prepare_healer_tile():
        raise AssertionError("Repeated Grass setup was rejected")
    if simulator.events:
        raise AssertionError(f"Existing Grass was modified: {simulator.events}")


def test_resource_preflight_does_not_modify_the_field() -> None:
    simulator = HealerSimulator(Grounds.Soil, None)
    simulator.install()
    simulator.inventory[Items.Fertilizer] = 0

    if achievement_healer.run_healer():
        raise AssertionError("Missing Fertilizer reported a successful run")
    if simulator.events != ["Healer failed: Fertilizer is unavailable"]:
        raise AssertionError(f"Resource preflight modified the field: {simulator.events}")


def test_runner_is_a_thin_finite_entry_point() -> None:
    runner = (SAVE_DIRECTORY / "run_achievement_healer.py").read_text()
    tree = ast.parse(runner)
    imports = [
        (node.module, [alias.name for alias in node.names])
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    if imports != [("achievement_healer", ["run_healer"])]:
        raise AssertionError(f"Healer runner imports changed: {imports}")
    if any(isinstance(node, (ast.For, ast.AsyncFor, ast.While)) for node in ast.walk(tree)):
        raise AssertionError("Healer runner must be finite")


def test_run_uses_both_curing_items() -> None:
    simulator = HealerSimulator(Grounds.Soil, None)
    simulator.install()

    if not achievement_healer.run_healer():
        raise AssertionError("Successful modeled Healer run reported failure")
    if simulator.events != ["till", "plant", "use_item", "use_item", "Healer complete"]:
        raise AssertionError(f"Healer used an unexpected sequence: {simulator.events}")


def main() -> None:
    test_soil_tile_is_tilled_before_grass_is_planted()
    test_grassland_tile_is_planted_without_tilling()
    test_occupied_tile_is_cleared_before_replacement()
    test_existing_grass_is_reused_and_setup_is_idempotent()
    test_resource_preflight_does_not_modify_the_field()
    test_runner_is_a_thin_finite_entry_point()
    test_run_uses_both_curing_items()
    print("Passed Healer ground, occupied-tile, idempotence, and finite-runner tests")


if __name__ == "__main__":
    main()
