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
import planting  # noqa: E402


class Entities:
    Grass = "Grass"
    Bush = "Bush"
    Tree = "Tree"
    Treasure = "Treasure"


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
        self.map_sizes = []
        self.plant_result = True
        self.fail_use_call = None
        self.find_calls = 0
        self.follow_calls = 0
        self.follow_results = []
        self.treasure_present = False
        self.treasure_position = None
        self.other_entities = {}
        self.missing_treasure = False

    def install(self) -> None:
        reusable.Entities = Entities
        reusable.Grounds = Grounds
        reusable.Items = Items
        reusable.Unlocks = Unlocks
        planting.Entities = Entities
        planting.Grounds = Grounds
        reusable.num_unlocked = lambda _unlock: 2
        reusable.num_items = lambda _item: self.inventory
        reusable.get_world_size = lambda: 32
        reusable.get_ground_type = lambda: Grounds.Grassland
        planting.get_ground_type = reusable.get_ground_type
        reusable.till = lambda: self.events.append("till")
        planting.till = reusable.till
        reusable.plant = self.plant
        reusable.use_item = self.use_item
        reusable.get_entity_type = self.get_entity_type
        reusable.clear = self.clear
        reusable.can_harvest = lambda: False
        reusable.harvest = self.harvest
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
        self.other_entities[self.position] = _entity
        return self.plant_result

    def get_entity_type(self):
        if self.position in self.other_entities:
            return self.other_entities[self.position]
        if (
            self.treasure_present
            and not self.missing_treasure
            and self.position == self.treasure_position
        ):
            return Entities.Treasure
        return None

    def clear(self) -> None:
        self.events.append("clear")
        self.other_entities.clear()
        self.treasure_present = False
        self.position = (0, 0)

    def harvest(self) -> bool:
        self.events.append("harvest")
        if self.position in self.other_entities:
            self.other_entities.pop(self.position)
            return True
        if self.get_entity_type() != Entities.Treasure:
            return False
        self.treasure_present = False
        return True

    def use_item(self, item, amount) -> bool:
        self.use_item_calls.append((item, amount))
        if self.fail_use_call == len(self.use_item_calls):
            return False
        if self.inventory < amount:
            return False
        self.inventory -= amount
        self.other_entities.pop(self.position, None)
        if len(self.use_item_calls) == 1:
            self.treasure_present = True
            self.treasure_position = self.position
        else:
            if self.position[0] == 2:
                self.treasure_position = (3, self.position[1])
            else:
                self.treasure_position = (2, self.position[1])
        return True

    def map_maze(
        self,
        _maze_index,
        _start_x,
        _start_y,
        _world_size,
        _maze_size,
    ):
        self.map_calls += 1
        self.map_sizes.append(_maze_size)
        if not self.treasure_present:
            self.treasure_present = True
            self.treasure_position = self.position
        return {"edges": {}, "tiles": []}

    def find_treasure_path(self, _maze_map, _start_x, _start_y):
        self.find_calls += 1
        if self.get_entity_type() == Entities.Treasure:
            return []
        return ["East"] if self.treasure_position[0] > self.position[0] else ["West"]

    def follow_maze_path(self, _path) -> bool:
        self.follow_calls += 1
        if self.follow_results:
            return self.follow_results.pop(0)
        if _path:
            direction = _path[0]
            if direction == "East":
                self.position = (self.position[0] + 1, self.position[1])
            else:
                self.position = (self.position[0] - 1, self.position[1])
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
    if set(simulator.map_sizes) != {reusable.MAZE_REGION_SIZE}:
        raise AssertionError("maze geometry used Weird Substance cost instead of side length")
    if simulator.map_calls != 1:
        raise AssertionError("successful reuse remapped a stable maze")
    if simulator.follow_calls != reusable.MAZE_REUSE_LIMIT + 1:
        raise AssertionError("reusable maze did not follow every relocation and final path")
    if simulator.events.count("harvest") != 1:
        raise AssertionError("reusable maze did not harvest the final treasure exactly once")
    if simulator.inventory != 0:
        raise AssertionError("exact reusable maze budget was not consumed")


def test_probe_harvests_one_tile_without_farm_clear_or_soil() -> None:
    simulator = ReuseSimulator(16)
    simulator.other_entities[(4, 4)] = "old entity"
    simulator.other_entities[(9, 9)] = "neighbor"
    simulator.install()

    if not reusable.create_probe_maze(4, 4, 8):
        raise AssertionError("probe maze setup failed from an occupied Grassland tile")
    if simulator.other_entities.get((9, 9)) != "neighbor":
        raise AssertionError("probe maze setup removed an unrelated farm entity")
    if simulator.position != (4, 4):
        raise AssertionError("probe maze setup reset the drone position")
    if "clear" in simulator.events or "till" in simulator.events:
        raise AssertionError("probe maze setup used farm clear or Soil preparation")


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


def test_missing_treasure_is_not_counted_as_a_relocation() -> None:
    simulator = ReuseSimulator(16)
    simulator.missing_treasure = True
    simulator.install()

    result = reusable.run_reusable_maze_worker(0, 1)
    if result != {"completed": 0, "reason": reusable.MAZE_WORKER_TREASURE_MISSING}:
        raise AssertionError(f"missing treasure was counted: {result}")


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
    test_probe_harvests_one_tile_without_farm_clear_or_soil()
    test_counter_advances_only_after_successful_relocation()
    test_exhaustion_and_blocked_move_recovery_are_distinct()
    test_missing_treasure_is_not_counted_as_a_relocation()
    test_preflight_rejects_missing_budget_without_actions()
    print(
        "Passed reusable maze setup, cost, 300-relocation, counter, exhaustion, and recovery tests"
    )


if __name__ == "__main__":
    main()
