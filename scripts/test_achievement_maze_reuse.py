#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise reusable maze setup, relocation counting, and recovery."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_maze as reusable  # noqa: E402


class Entities:
    Bush = "Bush"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Items:
    Weird_Substance = "Weird Substance"


class Unlocks:
    Mazes = "Mazes"


class ReuseSimulator:
    def __init__(self, inventory: int) -> None:
        self.inventory = inventory
        self.position = (0, 0)
        self.events = []
        self.use_item_calls = []
        self.map_calls = 0
        self.plant_result = True
        self.fail_use_call = None
        self.find_calls = 0
        self.follow_calls = 0
        self.follow_results = []

    def install(self) -> None:
        reusable.Entities = Entities
        reusable.Grounds = Grounds
        reusable.Items = Items
        reusable.Unlocks = Unlocks
        reusable.num_unlocked = lambda _unlock: 2
        reusable.num_items = lambda _item: self.inventory
        reusable.get_ground_type = lambda: Grounds.Grassland
        reusable.till = lambda: self.events.append("till")
        reusable.plant = self.plant
        reusable.use_item = self.use_item
        reusable.get_entity_type = lambda: None
        reusable.can_harvest = lambda: False
        reusable.harvest = lambda: self.events.append("harvest") or True
        reusable.move_to = self.move_to
        reusable.get_pos_x = lambda: self.position[0]
        reusable.get_pos_y = lambda: self.position[1]
        reusable.map_maze = self.map_maze
        reusable.find_treasure_path = self.find_treasure_path
        reusable.follow_maze_path = self.follow_maze_path

    def move_to(self, x: int, y: int) -> None:
        self.position = (x, y)
        self.events.append(("move_to", x, y))

    def plant(self, _entity) -> bool:
        self.events.append("plant")
        return self.plant_result

    def use_item(self, item, amount) -> bool:
        self.use_item_calls.append((item, amount))
        if self.fail_use_call == len(self.use_item_calls):
            return False
        if self.inventory < amount:
            return False
        self.inventory -= amount
        return True

    def map_maze(self, _maze_index, _start_x, _start_y):
        self.map_calls += 1
        return {"edges": {}, "tiles": []}

    def find_treasure_path(self, _maze_map, _start_x, _start_y):
        self.find_calls += 1
        return []

    def follow_maze_path(self, _path) -> bool:
        self.follow_calls += 1
        if self.follow_results:
            return self.follow_results.pop(0)
        return True


def test_exact_cost_and_three_hundred_successes() -> None:
    cost = reusable.MAZE_REGION_SIZE * 2
    simulator = ReuseSimulator(cost * (reusable.MAZE_REUSE_LIMIT + 1))
    simulator.install()

    if reusable.get_reusable_maze_substance_cost() != cost:
        raise AssertionError("reusable maze cost did not apply the maze level")
    result = reusable.run_reusable_maze_worker(0)

    if result != {
        "completed": reusable.MAZE_REUSE_LIMIT,
        "reason": reusable.MAZE_WORKER_COMPLETE,
    }:
        raise AssertionError(f"300 relocations did not complete: {result}")
    if len(simulator.use_item_calls) != reusable.MAZE_REUSE_LIMIT + 1:
        raise AssertionError("creation and relocation use count changed")
    if simulator.map_calls != 1:
        raise AssertionError("successful reuse remapped a stable maze")
    if simulator.inventory != 0:
        raise AssertionError("exact reusable maze budget was not consumed")


def test_counter_advances_only_after_successful_relocation() -> None:
    simulator = ReuseSimulator(16)
    simulator.fail_use_call = 2
    simulator.install()

    result = reusable.run_reusable_maze_worker(0, 2)
    if result["completed"] != 0:
        raise AssertionError("failed relocation advanced the success counter")
    if result["reason"] != reusable.MAZE_WORKER_RESOURCE_EXHAUSTED:
        raise AssertionError("failed relocation was not classified as resource failure")


def test_exhaustion_and_blocked_move_recovery_are_distinct() -> None:
    exhausted = ReuseSimulator(32)
    exhausted.install()
    original_find = exhausted.find_treasure_path

    def stop_finding(_maze_map, _start_x, _start_y):
        if exhausted.find_calls == 0:
            exhausted.find_calls += 1
            return []
        exhausted.find_calls += 1
        return None

    reusable.find_treasure_path = stop_finding
    result = reusable.run_reusable_maze_worker(0, 2)
    if result["completed"] != 1 or result["reason"] != reusable.MAZE_WORKER_RELOCATIONS_EXHAUSTED:
        raise AssertionError(f"relocation exhaustion changed: {result}")
    reusable.find_treasure_path = original_find

    recovered = ReuseSimulator(16)
    recovered.follow_results = [False, True]
    recovered.install()
    result = reusable.run_reusable_maze_worker(0, 1)
    if result["completed"] != 1 or result["reason"] != reusable.MAZE_WORKER_COMPLETE:
        raise AssertionError(f"blocked path recovery failed: {result}")
    if recovered.map_calls != 2:
        raise AssertionError("blocked move did not trigger one bounded remap")


def test_preflight_rejects_missing_budget_without_actions() -> None:
    simulator = ReuseSimulator(0)
    simulator.install()
    result = reusable.run_reusable_maze_worker(0, 2)
    if result["reason"] != reusable.MAZE_WORKER_RESOURCE_EXHAUSTED:
        raise AssertionError("missing Weird Substance budget was not rejected")
    if simulator.events or simulator.use_item_calls:
        raise AssertionError("resource preflight performed maze actions")


def main() -> None:
    test_exact_cost_and_three_hundred_successes()
    test_counter_advances_only_after_successful_relocation()
    test_exhaustion_and_blocked_move_recovery_are_distinct()
    test_preflight_rejects_missing_budget_without_actions()
    print("Passed reusable maze cost, 300-relocation, counter, exhaustion, and recovery tests")


if __name__ == "__main__":
    main()
