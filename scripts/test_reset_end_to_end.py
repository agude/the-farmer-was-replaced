#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the reset controller against one integrated reduced-cost model."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import reset_progression as reset  # noqa: E402


class Unlocks:
    Variables = "Variables"
    Operators = "Operators"
    Senses = "Senses"
    Loops = "Loops"
    Functions = "Functions"
    Lists = "Lists"
    Dictionaries = "Dictionaries"
    Import = "Import"
    Timing = "Timing"
    Utilities = "Utilities"
    Costs = "Costs"
    Simulation = "Simulation"
    Grass = "Grass"
    Plant = "Plant"
    Expand = "Expand"
    Trees = "Trees"
    Carrots = "Carrots"
    Watering = "Watering"
    Pumpkins = "Pumpkins"
    Cactus = "Cactus"
    Sunflowers = "Sunflowers"
    Polyculture = "Polyculture"
    Megafarm = "Megafarm"
    Mazes = "Mazes"
    Dinosaurs = "Dinosaurs"
    Fertilizer = "Fertilizer"
    Speed = "Speed"
    Hats = "Hats"
    Leaderboard = "Leaderboard"


class Items:
    Wood = "Wood"


class ReducedResetModel:
    def __init__(self) -> None:
        self.levels = {}
        self.inventory = {Items.Wood: 0}
        self.unlock_calls = []
        self.messages = []
        self.time = 0
        self.fail_next_producer = False

    def install(self) -> None:
        reset.Unlocks = Unlocks
        reset.Items = Items
        reset.num_unlocked = lambda unlock: self.levels.get(unlock, 0)
        reset.num_items = lambda item: self.inventory.get(item, 0)
        reset.get_cost = self.get_cost
        reset.unlock = self.unlock
        reset.produce_item = self.produce_item
        reset.get_time = lambda: self.time
        reset.quick_print = lambda message: self.messages.append(message)

    def get_cost(self, unlock):
        self.time += 1
        current_level = self.levels.get(unlock, 0)
        return {Items.Wood: current_level + 1}

    def unlock(self, unlock) -> bool:
        cost = self.get_cost(unlock)
        for item in cost:
            if self.inventory.get(item, 0) < cost[item]:
                return False
            self.inventory[item] -= cost[item]

        self.levels[unlock] = self.levels.get(unlock, 0) + 1
        self.unlock_calls.append((unlock, self.levels[unlock]))
        return True

    def produce_item(self, item, required_amount: int) -> bool:
        if self.fail_next_producer:
            self.fail_next_producer = False
            return False

        self.inventory[item] = self.inventory.get(item, 0) + required_amount
        return True


def test_reduced_route_reaches_leaderboard_and_resumes_after_failure() -> None:
    model = ReducedResetModel()
    model.install()
    model.fail_next_producer = True

    if reset.run_reset_progression():
        raise AssertionError("injected producer failure incorrectly completed reset")
    if not model.messages or "missing=Wood" not in model.messages[-1]:
        raise AssertionError("producer failure did not identify the missing resource")

    if not reset.run_reset_progression():
        raise AssertionError("reduced reset route did not resume after producer recovery")
    if model.levels.get(Unlocks.Leaderboard, 0) != 1:
        raise AssertionError("reduced reset route did not reach Leaderboard level 1")
    expected_steps = len(reset.get_unlock_plan())
    if len(model.unlock_calls) != expected_steps:
        raise AssertionError(
            "reduced reset route skipped a target-level purchase: "
            + str(len(model.unlock_calls))
            + "/"
            + str(expected_steps)
        )


def main() -> None:
    test_reduced_route_reaches_leaderboard_and_resumes_after_failure()
    print("Passed reduced reset route, failure diagnostic, resume, and target-level tests")


if __name__ == "__main__":
    main()
