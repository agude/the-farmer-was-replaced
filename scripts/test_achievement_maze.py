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
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_maze as layout  # noqa: E402


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


def test_worker_prefixes_are_disjoint() -> None:
    full_jobs = layout.get_maze_worker_jobs(layout.MAZE_REGION_COUNT)
    for worker_count in range(1, layout.MAZE_REGION_COUNT + 1):
        jobs = layout.get_maze_worker_jobs(worker_count)
        if jobs != full_jobs[:worker_count]:
            raise AssertionError(f"worker prefix changed at count {worker_count}")

        owned_coordinates = set()
        for maze_index, start_x, start_y in jobs:
            if (start_x, start_y) != layout.get_maze_anchor(maze_index):
                raise AssertionError(f"worker start changed for maze {maze_index}")

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
    test_worker_prefixes_are_disjoint()
    test_invalid_and_outside_coordinates()
    print("Passed disjoint 4x4 maze anchors, bounds, coverage, and worker-prefix tests")


if __name__ == "__main__":
    main()
