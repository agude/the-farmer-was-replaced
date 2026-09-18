#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the finite Dinosaur Master harvest-burst operation."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_dinosaur  # noqa: E402


class Entities:
    Apple = "Apple"


class Hats:
    Dinosaur_Hat = "Dinosaur Hat"
    Straw_Hat = "Straw Hat"


class Items:
    Bone = "Bone"
    Cactus = "Cactus"


class Unlocks:
    Dinosaurs = "Dinosaurs"


class DinosaurSimulator:
    def __init__(
        self,
        world_size: int = 4,
        cactus: int = 100,
        unlocked: int = 1,
        apple_present: bool = True,
        bone_gain: int = 1000000,
    ) -> None:
        self.world_size = world_size
        self.inventory = {Items.Bone: 0, Items.Cactus: cactus}
        self.unlocked = unlocked
        self.apple_present = apple_present
        self.bone_gain = bone_gain
        self.events = []

    def install(self) -> None:
        achievement_dinosaur.get_world_size = lambda: self.world_size
        achievement_dinosaur.get_cost = lambda _entity: {Items.Cactus: 1}
        achievement_dinosaur.num_unlocked = lambda _unlock: self.unlocked
        achievement_dinosaur.num_items = self.num_items
        achievement_dinosaur.clear = self.clear
        achievement_dinosaur.change_hat = self.change_hat
        achievement_dinosaur.get_entity_type = self.get_entity_type
        achievement_dinosaur.traverse_dinosaur_cycle = self.traverse_dinosaur_cycle
        achievement_dinosaur.Entities = Entities
        achievement_dinosaur.Hats = Hats
        achievement_dinosaur.Items = Items
        achievement_dinosaur.Unlocks = Unlocks
        achievement_dinosaur.ACHIEVEMENT_BONES_TARGET = 1000000

    def num_items(self, item) -> int:
        return self.inventory[item]

    def clear(self) -> None:
        self.events.append("clear")

    def change_hat(self, hat) -> None:
        self.events.append(("hat", hat))
        if hat == Hats.Straw_Hat and ("hat", Hats.Dinosaur_Hat) in self.events:
            self.inventory[Items.Bone] += self.bone_gain

    def get_entity_type(self):
        self.events.append("check apple")
        if self.apple_present:
            return Entities.Apple

        return "Grass"

    def traverse_dinosaur_cycle(self, _size: int) -> bool:
        self.events.append("traverse")
        return False


def test_preflight_precedes_clear() -> None:
    cases = (
        DinosaurSimulator(world_size=3),
        DinosaurSimulator(unlocked=0),
        DinosaurSimulator(cactus=15),
    )

    for simulator in cases:
        simulator.install()
        if achievement_dinosaur.run_achievement_dinosaur_once():
            raise AssertionError("invalid dinosaur preflight reported success")
        if "clear" in simulator.events:
            raise AssertionError(f"dinosaur preflight cleared the field: {simulator.events}")


def test_missing_apple_restores_hat() -> None:
    simulator = DinosaurSimulator(apple_present=False)
    simulator.install()

    if achievement_dinosaur.run_achievement_dinosaur_once():
        raise AssertionError("missing apple reported a successful dinosaur burst")
    if simulator.events != [
        "clear",
        ("hat", Hats.Dinosaur_Hat),
        "check apple",
        ("hat", Hats.Straw_Hat),
    ]:
        raise AssertionError(f"missing apple did not restore the straw hat: {simulator.events}")


def test_successful_run_removes_hat_once_and_checks_bone_delta() -> None:
    simulator = DinosaurSimulator()
    simulator.install()

    if not achievement_dinosaur.run_achievement_dinosaur_once():
        raise AssertionError("successful dinosaur burst reported failure")

    expected_events = [
        "clear",
        ("hat", Hats.Dinosaur_Hat),
        "check apple",
        "traverse",
        ("hat", Hats.Straw_Hat),
    ]
    if simulator.events != expected_events:
        raise AssertionError(f"dinosaur burst sequence changed: {simulator.events}")
    if simulator.inventory[Items.Bone] != 1000000:
        raise AssertionError("dinosaur burst did not credit the final hat removal")


def test_runner_is_finite_and_does_not_import_general_farmer() -> None:
    runner = (SAVE_DIRECTORY / "run_achievement_dinosaur.py").read_text()
    tree = ast.parse(runner)
    imports = [
        (node.module, [alias.name for alias in node.names])
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]

    if imports != [("achievement_dinosaur", ["run_achievement_dinosaur_once"])]:
        raise AssertionError(f"dinosaur achievement runner imports changed: {imports}")
    if "dinosaurs" in runner:
        raise AssertionError("dinosaur achievement runner imports the general farmer")
    if any(isinstance(node, ast.While) for node in ast.walk(tree)):
        raise AssertionError("dinosaur achievement runner is not finite")


def main() -> None:
    test_preflight_precedes_clear()
    test_missing_apple_restores_hat()
    test_successful_run_removes_hat_once_and_checks_bone_delta()
    test_runner_is_finite_and_does_not_import_general_farmer()
    print("Passed Dinosaur Master preflight, route burst, bone delta, and finite-runner tests")


if __name__ == "__main__":
    main()
