#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify the disjoint achievement maze worker layout."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
PROBE_RUNNER = SAVE_DIRECTORY / "run_achievement_maze_probe.py"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_maze as layout  # noqa: E402


class RectangleMazeSimulator:
    def __init__(self, bounds, start) -> None:
        self.lower_x, self.lower_y, self.upper_x, self.upper_y = bounds
        self.position = start

    def install(self) -> None:
        layout.North = "North"
        layout.East = "East"
        layout.South = "South"
        layout.West = "West"
        layout.can_move = self.can_move
        layout.move = self.move
        layout.get_pos_x = lambda: self.position[0]
        layout.get_pos_y = lambda: self.position[1]

    def next_position(self, direction):
        x, y = self.position
        if direction == "North":
            return x, y + 1
        if direction == "East":
            return x + 1, y
        if direction == "South":
            return x, y - 1
        return x - 1, y

    def can_move(self, direction) -> bool:
        x, y = self.next_position(direction)
        return self.lower_x <= x <= self.upper_x and self.lower_y <= y <= self.upper_y

    def move(self, direction) -> bool:
        if not self.can_move(direction):
            return False
        self.position = self.next_position(direction)
        return True


def test_anchors_and_bounds() -> None:
    expected_anchors = []
    for row in range(layout.MAZE_REGION_ROWS):
        for column in range(layout.MAZE_REGION_COLUMNS):
            expected_anchors.append(
                (
                    column * layout.MAZE_REGION_SIZE,
                    row * layout.MAZE_REGION_SIZE,
                )
            )

    actual_anchors = [layout.get_maze_anchor(index) for index in range(layout.MAZE_REGION_COUNT)]
    if actual_anchors != expected_anchors:
        raise AssertionError(f"maze anchors changed: {actual_anchors}")

    for index, (anchor_x, anchor_y) in enumerate(actual_anchors):
        bounds = layout.get_maze_bounds(index)
        if bounds != (
            anchor_x,
            anchor_y,
            anchor_x + layout.MAZE_REGION_SIZE - 1,
            anchor_y + layout.MAZE_REGION_SIZE - 1,
        ):
            raise AssertionError(f"maze bounds changed for {index}: {bounds}")

        for x in range(bounds[0], bounds[2] + 1):
            for y in range(bounds[1], bounds[3] + 1):
                if not layout.is_maze_coordinate(x, y, index):
                    raise AssertionError(f"coordinate {(x, y)} left maze {index}")


def test_centered_bounds_cover_edges_and_corners() -> None:
    cases = {
        (16, 16): (12, 12, 19, 19),
        (0, 0): (0, 0, 7, 7),
        (31, 0): (24, 0, 31, 7),
        (0, 31): (0, 24, 7, 31),
        (31, 31): (24, 24, 31, 31),
        (0, 16): (0, 12, 7, 19),
        (31, 16): (24, 12, 31, 19),
        (16, 0): (12, 0, 19, 7),
        (16, 31): (12, 24, 19, 31),
    }

    for creation, expected in cases.items():
        actual = layout.get_maze_bounds_for_creation(creation[0], creation[1], 8, 32)
        if actual != expected:
            raise AssertionError(f"wrong centered bounds for {creation}: {actual}")


def test_safe_creation_coordinates_reproduce_requested_regions() -> None:
    regions = ((0, 0), (8, 0), (0, 8), (24, 24))

    for lower_x, lower_y in regions:
        creation = layout.get_safe_maze_creation_coordinate(lower_x, lower_y, 8, 32)
        expected_creation = (lower_x + 4, lower_y + 4)
        if creation != expected_creation:
            raise AssertionError(f"unsafe creation coordinate for {(lower_x, lower_y)}")

        bounds = layout.get_maze_bounds_for_creation(creation[0], creation[1], 8, 32)
        expected_bounds = (lower_x, lower_y, lower_x + 7, lower_y + 7)
        if bounds != expected_bounds:
            raise AssertionError(f"creation coordinate shifted region: {bounds}")


def test_adjacent_regions_do_not_overlap() -> None:
    first = layout.get_maze_bounds_for_creation(4, 4, 8, 32)
    second = layout.get_maze_bounds_for_creation(12, 4, 8, 32)

    if first[2] >= second[0]:
        raise AssertionError(f"adjacent regions overlap: {first}, {second}")


def test_placement_probe_is_disabled_by_configuration() -> None:
    source = PROBE_RUNNER.read_text()
    if "ENABLE_MAZE_PLACEMENT_PROBE" not in source:
        raise AssertionError("maze placement probe has no configuration gate")
    if "if ENABLE_MAZE_PLACEMENT_PROBE" not in source:
        raise AssertionError("maze placement probe runs without explicit enablement")


def test_probe_maps_centered_and_edge_adjusted_bounds() -> None:
    cases = (
        ((0, 0, 7, 7), (4, 4)),
        ((0, 12, 7, 19), (0, 16)),
    )

    for bounds, start in cases:
        simulator = RectangleMazeSimulator(bounds, start)
        simulator.install()
        observed = layout.map_observed_maze_bounds()
        if observed != bounds:
            raise AssertionError(f"probe mapped {observed}, expected {bounds}")
        if simulator.position != start:
            raise AssertionError("probe did not return to its creation coordinate")


def test_worker_prefixes_are_disjoint() -> None:
    full_jobs = layout.get_maze_worker_jobs(layout.MAZE_REGION_COUNT)
    for worker_count in range(1, layout.MAZE_REGION_COUNT + 1):
        jobs = layout.get_maze_worker_jobs(worker_count)
        if jobs != full_jobs[:worker_count]:
            raise AssertionError(f"worker prefix changed at count {worker_count}")

        owned_coordinates = set()
        for maze_index, start_x, start_y in jobs:
            if (start_x, start_y) != layout.get_maze_start_position(maze_index):
                raise AssertionError(f"worker creation point changed for maze {maze_index}")
            if (start_x, start_y) == layout.get_maze_anchor(maze_index):
                raise AssertionError(f"worker still starts at the lower-left bound {maze_index}")

            bounds = layout.get_maze_bounds(maze_index)
            for x in range(bounds[0], bounds[2] + 1):
                for y in range(bounds[1], bounds[3] + 1):
                    coordinate = (x, y)
                    if coordinate in owned_coordinates:
                        raise AssertionError(f"maze regions overlap at {coordinate}")
                    owned_coordinates.add(coordinate)

        expected_area = worker_count * layout.MAZE_REGION_SIZE**2
        if len(owned_coordinates) != expected_area:
            raise AssertionError(f"maze coverage changed at count {worker_count}")


def test_invalid_and_outside_coordinates() -> None:
    for maze_index in (-1, layout.MAZE_REGION_COUNT):
        if layout.get_maze_anchor(maze_index) is not None:
            raise AssertionError("invalid maze index returned an anchor")
        if layout.get_maze_start_position(maze_index) is not None:
            raise AssertionError("invalid maze index returned a start")

    if layout.get_maze_index(0, layout.MAZE_WORLD_HEIGHT) is not None:
        raise AssertionError("unused lower world rows have a maze owner")
    if layout.get_maze_index(layout.MAZE_WORLD_WIDTH, 0) is not None:
        raise AssertionError("outside world columns have a maze owner")
    if layout.get_maze_worker_jobs(0):
        raise AssertionError("zero workers produced a maze job")
    if len(layout.get_maze_worker_jobs(layout.MAZE_REGION_COUNT + 1)) != layout.MAZE_REGION_COUNT:
        raise AssertionError("worker jobs exceeded the available maze regions")


def main() -> None:
    test_anchors_and_bounds()
    test_centered_bounds_cover_edges_and_corners()
    test_safe_creation_coordinates_reproduce_requested_regions()
    test_adjacent_regions_do_not_overlap()
    test_placement_probe_is_disabled_by_configuration()
    test_probe_maps_centered_and_edge_adjusted_bounds()
    test_worker_prefixes_are_disjoint()
    test_invalid_and_outside_coordinates()
    print("Passed disjoint 4x4 maze anchors, bounds, coverage, and worker-prefix tests")


if __name__ == "__main__":
    main()
