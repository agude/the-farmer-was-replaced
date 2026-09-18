#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the synchronized full-field achievement pumpkin cycle."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_pumpkin  # noqa: E402
import parallel_farming  # noqa: E402


class Entities:
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Items:
    Water = "Water"


class Worker:
    def __init__(self, function, job_value) -> None:
        self.function = function
        self.job_value = job_value

    def run(self):
        return self.function(self.job_value)


class DispatchSimulator:
    def __init__(self, child_capacity: int) -> None:
        self.child_capacity = child_capacity
        self.active_workers = []
        self.events = []

    def install(self) -> None:
        parallel_farming.spawn_drone = self.spawn_drone
        parallel_farming.wait_for = self.wait_for

    def spawn_drone(self, function, job_value):
        self.events.append(("spawn", job_value))

        if len(self.active_workers) >= self.child_capacity:
            return None

        worker = Worker(function, job_value)
        self.active_workers.append(worker)
        return worker

    def wait_for(self, worker):
        self.events.append(("wait", worker.job_value))
        result = worker.run()
        self.active_workers.remove(worker)
        return result


class PumpkinSimulator:
    def __init__(self, size: int, dead_positions=None, fail_position=None) -> None:
        self.size = size
        self.dead_positions = dead_positions or []
        self.fail_position = fail_position
        self.position = (0, 0)
        self.entities = {}
        self.mature = {}
        self.ground = {}
        self.water = {}
        self.inventory = {Items.Water: 1000}
        self.events = []
        self.harvest_calls = 0

        for x in range(size):
            for y in range(size):
                self.entities[(x, y)] = None
                self.mature[(x, y)] = False
                self.ground[(x, y)] = Grounds.Grassland
                self.water[(x, y)] = 0

        for position in self.dead_positions:
            self.entities[position] = Entities.Dead_Pumpkin

    def install(self) -> None:
        achievement_pumpkin.get_world_size = lambda: self.size
        achievement_pumpkin.move_to = self.move_to
        achievement_pumpkin.get_entity_type = self.get_entity_type
        achievement_pumpkin.can_harvest = self.can_harvest
        achievement_pumpkin.plant = self.plant
        achievement_pumpkin.get_ground_type = self.get_ground_type
        achievement_pumpkin.till = self.till
        achievement_pumpkin.get_water = self.get_water
        achievement_pumpkin.num_items = self.num_items
        achievement_pumpkin.use_item = self.use_item
        achievement_pumpkin.harvest = self.harvest
        achievement_pumpkin.Entities = Entities
        achievement_pumpkin.Grounds = Grounds
        achievement_pumpkin.Items = Items
        achievement_pumpkin.dispatch_indexed_jobs = parallel_farming.dispatch_indexed_jobs

        achievement_pumpkin.ensure_soil = self.ensure_soil

    def move_to(self, x: int, y: int) -> None:
        self.position = (x, y)
        self.events.append(("move", x, y))

    def get_entity_type(self):
        return self.entities[self.position]

    def can_harvest(self) -> bool:
        return self.entities[self.position] == Entities.Pumpkin and self.mature[self.position]

    def plant(self, entity) -> bool:
        self.events.append(("plant", self.position, entity))
        if self.position == self.fail_position:
            return False

        self.entities[self.position] = entity
        self.mature[self.position] = True
        return True

    def get_ground_type(self):
        return self.ground[self.position]

    def ensure_soil(self) -> None:
        self.ground[self.position] = Grounds.Soil
        self.events.append(("soil", self.position))

    def till(self) -> None:
        self.ground[self.position] = Grounds.Soil
        self.events.append(("till", self.position))

    def get_water(self) -> int:
        return self.water[self.position]

    def num_items(self, item) -> int:
        return self.inventory[item]

    def use_item(self, item) -> bool:
        self.events.append(("water", self.position))
        if self.inventory[item] <= 0:
            return False

        self.inventory[item] -= 1
        self.water[self.position] = 1
        return True

    def harvest(self) -> None:
        if not self.can_harvest():
            raise AssertionError("pumpkin harvest started before final row was ready")

        self.harvest_calls += 1
        self.events.append("harvest")


def test_rows_cover_full_world_and_repair_dead_pumpkins() -> None:
    simulator = PumpkinSimulator(4, dead_positions=[(1, 2)])
    dispatch = DispatchSimulator(0)
    dispatch.install()
    simulator.install()

    if not achievement_pumpkin.farm_achievement_pumpkin_cycle():
        raise AssertionError("full-field pumpkin cycle reported failure")

    if simulator.harvest_calls != 1:
        raise AssertionError("pumpkin coordinator harvested more than once")
    planted_positions = [event[1] for event in simulator.events if event[0] == "plant"]
    if (1, 2) not in planted_positions:
        raise AssertionError("dead pumpkin was not replaced directly")
    if "harvest" in [event for event in simulator.events if isinstance(event, tuple)]:
        raise AssertionError("row repair harvested before replanting")

    expected_positions = []
    for x in range(4):
        for y in range(4):
            expected_positions.append((x, y))
    if sorted(planted_positions) != expected_positions:
        raise AssertionError("rows did not cover every empty/dead tile")


def test_water_is_used_once_after_planting() -> None:
    simulator = PumpkinSimulator(1)
    dispatch = DispatchSimulator(0)
    dispatch.install()
    simulator.install()

    if not achievement_pumpkin.farm_achievement_pumpkin_cycle():
        raise AssertionError("single-tile pumpkin cycle reported failure")

    water_events = [event for event in simulator.events if event[0] == "water"]
    if len(water_events) != 1:
        raise AssertionError(f"expected one post-plant water use, got {water_events}")


def test_failed_row_blocks_bulk_harvest() -> None:
    simulator = PumpkinSimulator(4, fail_position=(0, 1))
    dispatch = DispatchSimulator(2)
    dispatch.install()
    simulator.install()

    if achievement_pumpkin.farm_achievement_pumpkin_cycle():
        raise AssertionError("failed pumpkin row reported success")
    if simulator.harvest_calls != 0:
        raise AssertionError("failed row did not block the bulk harvest")
    if dispatch.events.count(("wait", 1)) == 0:
        raise AssertionError("coordinator did not join the failed worker")


def main() -> None:
    test_rows_cover_full_world_and_repair_dead_pumpkins()
    test_water_is_used_once_after_planting()
    test_failed_row_blocks_bulk_harvest()
    print("Passed synchronized pumpkin rows, dead repair, watering, barrier, and failure tests")


if __name__ == "__main__":
    main()
