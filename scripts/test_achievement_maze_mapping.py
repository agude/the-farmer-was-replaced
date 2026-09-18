#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise achievement maze mapping, shortest paths, and move guards."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_maze as maze  # noqa: E402


class MazeSimulator:
    def __init__(self) -> None:
        self.position = (0, 0)
        self.blocked = set()
        self.move_attempts = []
        self.edges = {
            (0, 0): {"East": (1, 0)},
            (1, 0): {"West": (0, 0), "East": (2, 0), "North": (1, 1)},
            (2, 0): {"West": (1, 0), "North": (2, 1)},
            (2, 1): {"South": (2, 0), "North": (2, 2), "East": (3, 1)},
            (2, 2): {"South": (2, 1), "North": (2, 3)},
            (2, 3): {"South": (2, 2)},
            (3, 1): {"West": (2, 1), "North": (3, 2)},
            (3, 2): {"South": (3, 1), "North": (3, 3)},
            (3, 3): {"South": (3, 2)},
            (1, 1): {"South": (1, 0), "North": (1, 2)},
            (1, 2): {"South": (1, 1), "North": (1, 3)},
            (1, 3): {"South": (1, 2)},
        }
        self.treasure = (3, 3)

    def install(self) -> None:
        maze.North = "North"
        maze.East = "East"
        maze.South = "South"
        maze.West = "West"
        maze.move = self.move
        maze.measure = lambda: self.treasure

    def move(self, direction) -> bool:
        self.move_attempts.append((self.position, direction))
        next_position = self.edges[self.position].get(direction)
        if next_position is None or (self.position, next_position) in self.blocked:
            return False

        self.position = next_position
        return True


def test_mapper_discovers_branches_and_dead_ends() -> None:
    simulator = MazeSimulator()
    simulator.install()

    maze_map = maze.map_maze(0, 0, 0)
    if maze_map is None:
        raise AssertionError("maze mapper rejected a valid loop-free maze")
    if simulator.position != (0, 0):
        raise AssertionError("maze mapper did not return to the worker start")
    if len(maze_map["tiles"]) != len(simulator.edges):
        raise AssertionError("maze mapper missed a reachable branch or dead end")

    for position, neighbors in simulator.edges.items():
        mapped_neighbors = maze_map["edges"].get(position, {})
        if len(mapped_neighbors) != len(neighbors):
            raise AssertionError(f"maze mapper missed an edge at {position}")


def test_shortest_path_and_treasure_measurement() -> None:
    simulator = MazeSimulator()
    simulator.install()
    maze_map = maze.map_maze(0, 0, 0)

    path = maze.find_treasure_path(maze_map, 0, 0)
    if path != ["East", "East", "North", "East", "North", "North"]:
        raise AssertionError(f"shortest treasure path changed: {path}")
    if not maze.follow_maze_path(path):
        raise AssertionError("cached shortest path was not followable")
    if simulator.position != simulator.treasure:
        raise AssertionError("cached path did not reach the measured treasure")

    if maze.find_shortest_path(maze_map, 0, 0, 0, 1) is not None:
        raise AssertionError("unmapped target was treated as reachable")
    if maze.find_shortest_path(maze_map, 0, 0, 0, 0) != []:
        raise AssertionError("same-tile shortest path was not empty")


def test_later_edge_and_blocked_path_recovery_signal() -> None:
    simulator = MazeSimulator()
    simulator.install()
    maze_map = maze.map_maze(0, 0, 0)

    maze.add_maze_tile(maze_map, 0, 1)
    maze.record_maze_edge(maze_map, 0, 0, "North", 0, 1)
    if maze.find_shortest_path(maze_map, 0, 0, 0, 1) != ["North"]:
        raise AssertionError("later-added edge was not usable by shortest-path search")

    simulator.position = (0, 0)
    simulator.blocked.add(((0, 0), (1, 0)))
    cached_path = maze.find_shortest_path(maze_map, 0, 0, 3, 3)
    if maze.follow_maze_path(cached_path):
        raise AssertionError("blocked cached move was reported as successful")


def main() -> None:
    test_mapper_discovers_branches_and_dead_ends()
    test_shortest_path_and_treasure_measurement()
    test_later_edge_and_blocked_path_recovery_signal()
    print("Passed maze mapping, branch, dead-end, path, added-edge, and blocked-move tests")


if __name__ == "__main__":
    main()
