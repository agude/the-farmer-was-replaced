#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the full-field achievement cactus cycle on deterministic grids."""

from __future__ import annotations

import random
import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_cactus  # noqa: E402
import cactus  # noqa: E402
import navigation  # noqa: E402
import parallel_farming  # noqa: E402


BASE_ROW_JOB = achievement_cactus.sort_full_field_row_job
BASE_COLUMN_JOB = achievement_cactus.sort_full_field_column_job


EAST = "East"
NORTH = "North"
SOUTH = "South"
WEST = "West"


class Entities:
    Cactus = "Cactus"
    Dead_Pumpkin = "Dead Pumpkin"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


def is_chain_sorted(values: list[list[int]]) -> bool:
    size = len(values)

    for row in range(size):
        for column in range(size - 1):
            if values[row][column] > values[row][column + 1]:
                return False

    for row in range(size - 1):
        for column in range(size):
            if values[row][column] > values[row + 1][column]:
                return False

    return True


class GridSimulator:
    def __init__(self, values: list[list[int]]) -> None:
        self.values = [row[:] for row in values]
        self.size = len(values)
        self.x = 0
        self.y = 0
        self.ground = []
        self.entities = []
        self.mature = []

        for _row in range(self.size):
            self.ground.append([Grounds.Grassland] * self.size)
            self.entities.append([None] * self.size)
            self.mature.append([False] * self.size)

        self.phase_events = []
        self.spawn_attempts = []
        self.harvest_calls = 0
        self.measure_calls = []
        self.move_actions = 0
        self.move_to_calls = 0
        self.lane_return_positions = []
        self.tick_count = 0
        self.debug_messages = []
        self.precondition_checked = False
        self.values_at_harvest = None
        self.row_job = BASE_ROW_JOB
        self.column_job = BASE_COLUMN_JOB

    def install(self) -> None:
        achievement_cactus.get_world_size = self.get_world_size
        achievement_cactus.move_to = self.move_to
        achievement_cactus.move = self.move
        achievement_cactus.measure = self.measure
        achievement_cactus.swap = self.swap
        achievement_cactus.East = EAST
        achievement_cactus.North = NORTH
        achievement_cactus.South = SOUTH
        achievement_cactus.West = WEST
        achievement_cactus.can_harvest = self.can_harvest
        achievement_cactus.harvest = self.harvest
        achievement_cactus.get_tick_count = self.get_tick_count
        achievement_cactus.quick_print = self.quick_print
        achievement_cactus.dispatch_indexed_jobs = parallel_farming.dispatch_indexed_jobs
        achievement_cactus.sort_full_field_row_job = self.record_row_job
        achievement_cactus.sort_full_field_column_job = self.record_column_job

        cactus.move_to = self.move_to
        cactus.get_entity_type = self.get_entity_type
        cactus.get_ground_type = self.get_ground_type
        cactus.ensure_soil = self.ensure_soil
        cactus.plant = self.plant
        cactus.can_harvest = self.can_harvest
        cactus.get_water = lambda: 1
        cactus.water_if_dry = lambda _threshold: None
        cactus.measure = self.measure
        cactus.swap = self.swap
        cactus.Entities = Entities
        cactus.Grounds = Grounds
        cactus.East = EAST
        cactus.North = NORTH
        cactus.South = SOUTH
        cactus.West = WEST

        navigation.get_world_size = self.get_world_size
        navigation.get_pos_x = self.get_pos_x
        navigation.get_pos_y = self.get_pos_y

        parallel_farming.spawn_drone = self.spawn_drone
        parallel_farming.wait_for = self.wait_for

    def get_world_size(self) -> int:
        return self.size

    def move_to(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.move_to_calls += 1

    def move(self, direction) -> bool:
        if direction == EAST:
            self.x += 1
        elif direction == WEST:
            self.x -= 1
        elif direction == NORTH:
            self.y += 1
        elif direction == SOUTH:
            self.y -= 1
        else:
            raise AssertionError(f"Unknown direction: {direction}")

        self.move_actions += 1
        return True

    def get_pos_x(self) -> int:
        return self.x

    def get_pos_y(self) -> int:
        return self.y

    def get_tick_count(self) -> int:
        return self.tick_count

    def quick_print(self, message) -> None:
        self.debug_messages.append(message)

    def current_tile(self):
        return self.y, self.x

    def get_entity_type(self):
        row, column = self.current_tile()
        return self.entities[row][column]

    def get_ground_type(self):
        row, column = self.current_tile()
        return self.ground[row][column]

    def ensure_soil(self) -> None:
        row, column = self.current_tile()
        self.ground[row][column] = Grounds.Soil

    def plant(self, entity) -> bool:
        row, column = self.current_tile()
        self.entities[row][column] = entity
        self.mature[row][column] = True
        return True

    def can_harvest(self) -> bool:
        row, column = self.current_tile()
        return self.entities[row][column] == Entities.Cactus and self.mature[row][column]

    def measure(self, direction=None) -> int:
        self.measure_calls.append(direction)

        if not self.precondition_checked:
            self.precondition_checked = True

            for row in range(self.size):
                for column in range(self.size):
                    if self.ground[row][column] != Grounds.Soil:
                        raise AssertionError("sorting began before every tile was soil")
                    if self.entities[row][column] != Entities.Cactus:
                        raise AssertionError("sorting began before every cactus was planted")
                    if not self.mature[row][column]:
                        raise AssertionError("sorting began before every cactus matured")

        neighbor_x = self.x
        neighbor_y = self.y
        if direction == EAST:
            neighbor_x += 1
        elif direction == WEST:
            neighbor_x -= 1
        elif direction == NORTH:
            neighbor_y += 1
        elif direction == SOUTH:
            neighbor_y -= 1

        return self.values[neighbor_y][neighbor_x]

    def swap(self, direction) -> None:
        neighbor_x = self.x
        neighbor_y = self.y
        if direction == EAST:
            neighbor_x += 1
        elif direction == WEST:
            neighbor_x -= 1
        elif direction == NORTH:
            neighbor_y += 1
        elif direction == SOUTH:
            neighbor_y -= 1

        current_row, current_column = self.current_tile()
        self.values[current_row][current_column], self.values[neighbor_y][neighbor_x] = (
            self.values[neighbor_y][neighbor_x],
            self.values[current_row][current_column],
        )

    def harvest(self) -> None:
        if not self.can_harvest():
            raise AssertionError("achievement cactus harvested an immature tile")
        if not is_chain_sorted(self.values):
            raise AssertionError("cactus chain was harvested before both sort phases finished")

        self.harvest_calls += 1
        self.values_at_harvest = [row[:] for row in self.values]

    def record_row_job(self, job) -> bool:
        self.phase_events.append("row")
        result = self.row_job(job)
        self.lane_return_positions.append(("row", self.x, self.y))
        return result

    def record_column_job(self, job) -> bool:
        self.phase_events.append("column")
        result = self.column_job(job)
        self.lane_return_positions.append(("column", self.x, self.y))
        return result

    def spawn_drone(self, _function, job) -> None:
        self.spawn_attempts.append(job)
        return

    def wait_for(self, _worker):
        raise AssertionError("fallback simulator should not wait for a worker")


def sorted_grid(size: int) -> list[list[int]]:
    return [[row * size + column for column in range(size)] for row in range(size)]


def reverse_grid(size: int) -> list[list[int]]:
    values = sorted_grid(size)
    values.reverse()
    for row in range(size):
        values[row].reverse()
    return values


def diagonal_grid(size: int) -> list[list[int]]:
    values = []

    for row in range(size):
        values.append(
            [size * size - 1 - ((row + column) * 10 // (2 * size - 1)) for column in range(size)]
        )

    return values


def random_grid(size: int, generator: random.Random) -> list[list[int]]:
    values = []

    for _row in range(size):
        values.append([generator.randrange(size * size) for _column in range(size)])

    return values


def run_case(name: str, values: list[list[int]]) -> None:
    simulator = GridSimulator(values)
    simulator.install()

    if not achievement_cactus.farm_achievement_cactus_cycle():
        raise AssertionError(f"{name}: full-field cycle reported failure")
    if simulator.harvest_calls != 1:
        raise AssertionError(f"{name}: expected one normal harvest, got {simulator.harvest_calls}")
    if simulator.values_at_harvest is None or not is_chain_sorted(simulator.values_at_harvest):
        raise AssertionError(f"{name}: final cactus order was not chain-sorted")
    if simulator.phase_events.index("column") < simulator.phase_events.index("row"):
        raise AssertionError(f"{name}: column sorting began before row sorting")
    if len(simulator.spawn_attempts) != 3 * (simulator.size - 1):
        raise AssertionError(f"{name}: spawn fallback skipped a phase lane")
    if simulator.move_actions == 0:
        raise AssertionError(f"{name}: lane workers did not use direct movement")
    if len(simulator.lane_return_positions) != 2 * simulator.size:
        raise AssertionError(f"{name}: a lane worker did not report its return position")
    for index in range(0, len(simulator.measure_calls), 2):
        if simulator.measure_calls[index] is not None:
            raise AssertionError(f"{name}: adjacent comparison reread its current cactus")
        if simulator.measure_calls[index + 1] not in (EAST, WEST, NORTH, SOUTH):
            raise AssertionError(f"{name}: adjacent comparison did not read one neighbor")


def test_debug_phase_totals() -> None:
    simulator = GridSimulator(sorted_grid(4))
    simulator.install()
    achievement_cactus.DEBUG_OUTPUT = True

    try:
        if not achievement_cactus.farm_achievement_cactus_cycle():
            raise AssertionError("debug cactus cycle reported failure")
    finally:
        achievement_cactus.DEBUG_OUTPUT = False

    expected_labels = (
        "Cactus planting",
        "Cactus row-sort",
        "Cactus column-sort",
        "Cactus harvest",
    )
    for label in expected_labels:
        if not any(message.startswith(label + " ticks ") for message in simulator.debug_messages):
            raise AssertionError(f"debug output omitted {label} ticks")


def main() -> None:
    size = 32
    run_case("sorted", sorted_grid(size))
    run_case("reverse", reverse_grid(size))
    run_case("diagonal", diagonal_grid(size))

    generator = random.Random(20260918)
    for case_number in range(10):
        run_case(f"random {case_number + 1}", random_grid(size, generator))

    test_debug_phase_totals()
    print(
        "Passed 13 full-field cactus grids, phase barriers, direct movement, "
        "metrics, soil/maturity, and fallback tests"
    )


if __name__ == "__main__":
    main()
