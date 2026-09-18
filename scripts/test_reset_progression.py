#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise reset progression planning, live costs, and progress guards."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import reset_progression as reset  # noqa: E402


class Unlocks:
    A = "A"
    B = "B"
    C = "C"
    Target = "Target"
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


class ResetSimulator:
    def __init__(self) -> None:
        self.levels = {}
        self.inventory = {Items.Wood: 0}
        self.costs = {}
        self.unlock_results = {}
        self.unlock_calls = []
        self.cost_reads = []
        self.produce_result = True
        self.produce_amount = 0
        self.time = 0
        self.messages = []

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
        cost = self.costs.get(unlock)
        self.cost_reads.append((unlock, self.levels.get(unlock, 0)))
        if isinstance(cost, list):
            level = self.levels.get(unlock, 0)
            return cost[min(level, len(cost) - 1)]
        return cost

    def unlock(self, unlock) -> bool:
        self.unlock_calls.append(unlock)
        if not self.unlock_results.get(unlock, True):
            return False
        self.levels[unlock] = self.levels.get(unlock, 0) + 1
        return True

    def produce_item(self, item, _amount) -> bool:
        if not self.produce_result:
            return False
        self.inventory[item] = self.inventory.get(item, 0) + self.produce_amount
        return True


def test_dependency_cycle_detection() -> None:
    reset.Unlocks = Unlocks
    acyclic = [
        (Unlocks.A, "A", []),
        (Unlocks.B, "B", [Unlocks.A]),
        (Unlocks.C, "C", [Unlocks.B]),
    ]
    if not reset.validate_unlock_plan(acyclic):
        raise AssertionError("acyclic unlock plan was rejected")

    direct_cycle = [
        (Unlocks.A, "A", [Unlocks.B]),
        (Unlocks.B, "B", [Unlocks.A]),
    ]
    if reset.validate_unlock_plan(direct_cycle):
        raise AssertionError("direct unlock cycle was accepted")

    multi_cycle = [
        (Unlocks.A, "A", [Unlocks.C]),
        (Unlocks.B, "B", [Unlocks.A]),
        (Unlocks.C, "C", [Unlocks.B]),
    ]
    if reset.validate_unlock_plan(multi_cycle):
        raise AssertionError("multi-item unlock cycle was accepted")

    repeated = [
        (Unlocks.A, 1, "A1", []),
        (Unlocks.A, 2, "A2", []),
        (Unlocks.B, 1, "B1", [Unlocks.A]),
    ]
    if not reset.validate_unlock_plan(repeated):
        raise AssertionError("ordered repeated unlock levels were rejected")

    skipped_level = [
        (Unlocks.A, 1, "A1", []),
        (Unlocks.A, 3, "A3", []),
    ]
    if reset.validate_unlock_plan(skipped_level):
        raise AssertionError("unlock plan accepted a skipped target level")


def test_default_plan_contains_explicit_target_levels() -> None:
    plan = reset.get_unlock_plan()
    if not reset.validate_unlock_plan(plan):
        raise AssertionError("default reset plan is not a valid ordered level plan")

    levels = {}
    for unlock, target_level, _reason, _prerequisites in plan:
        if unlock not in levels:
            levels[unlock] = []
        levels[unlock].append(target_level)

    expected = {
        Unlocks.Expand: [1, 2, 3, 4, 5, 6, 7],
        Unlocks.Speed: [1, 2, 3, 4, 5],
        Unlocks.Grass: [1, 2, 3, 4],
        Unlocks.Trees: [1, 2, 3, 4, 5],
        Unlocks.Carrots: [1, 2, 3, 4, 5, 6],
        Unlocks.Fertilizer: [1, 2, 3, 4],
        Unlocks.Mazes: [1, 2, 3, 4],
        Unlocks.Megafarm: [1, 2, 3, 4],
        Unlocks.Cactus: [1, 2, 3],
        Unlocks.Dinosaurs: [1, 2, 3, 4, 5],
    }
    for unlock, expected_levels in expected.items():
        if levels.get(unlock) != expected_levels:
            raise AssertionError(f"target levels changed for {unlock}: {levels.get(unlock)}")


def test_changing_cost_and_overshooting_producer() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.costs[Unlocks.Target] = {Items.Wood: 4}
    simulator.produce_amount = 10

    result = reset.unlock_one(Unlocks.Target, [])
    if result["status"] != reset.UNLOCK_SUCCESS:
        raise AssertionError(f"overshooting producer did not unlock target: {result}")
    if simulator.inventory[Items.Wood] != 10:
        raise AssertionError("producer did not preserve overshoot for later costs")
    if simulator.unlock_calls != [Unlocks.Target]:
        raise AssertionError("changing live cost caused duplicate purchase attempts")


def test_target_level_buys_each_level_with_refreshed_costs() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.costs[Unlocks.Target] = [
        {Items.Wood: 4},
        {Items.Wood: 12},
        {Items.Wood: 30},
    ]
    simulator.produce_amount = 10

    result = reset.unlock_one(Unlocks.Target, [], 3)
    if result["status"] != reset.UNLOCK_SUCCESS:
        raise AssertionError(f"target level was not reached: {result}")
    if simulator.levels[Unlocks.Target] != 3:
        raise AssertionError("target-level purchase stopped at the first level")
    if simulator.unlock_calls != [Unlocks.Target, Unlocks.Target, Unlocks.Target]:
        raise AssertionError("target-level purchase did not buy each level")
    if simulator.cost_reads != [
        (Unlocks.Target, 0),
        (Unlocks.Target, 0),
        (Unlocks.Target, 1),
        (Unlocks.Target, 1),
        (Unlocks.Target, 2),
        (Unlocks.Target, 2),
    ]:
        raise AssertionError("target-level purchase reused a stale cost")


def test_nonzero_level_does_not_satisfy_higher_target() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.levels[Unlocks.Target] = 1
    simulator.costs[Unlocks.Target] = [{Items.Wood: 1}, {Items.Wood: 2}]
    simulator.produce_amount = 2

    result = reset.unlock_one(Unlocks.Target, [], 2)
    if result["status"] != reset.UNLOCK_SUCCESS:
        raise AssertionError("higher target level was not purchased")
    if simulator.unlock_calls != [Unlocks.Target]:
        raise AssertionError("already-owned level was purchased again")


def test_failure_report_identifies_target_missing_item_and_elapsed_time() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.time = 17
    simulator.costs[Unlocks.Target] = {Items.Wood: 4}

    reset.report_reset_failure(Unlocks.Target, 2, "Target stage", "no_progress", 5)
    if len(simulator.messages) != 1:
        raise AssertionError("reset failure did not emit one diagnostic")
    message = simulator.messages[0]
    for expected in (
        "Target stage",
        "no_progress",
        "Target",
        "0/2",
        "Wood",
        "12",
        "seconds",
    ):
        if expected not in message:
            raise AssertionError(f"reset diagnostic omitted {expected}: {message}")


def test_failed_purchase_is_visible() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.costs[Unlocks.Target] = {}
    simulator.unlock_results[Unlocks.Target] = False

    result = reset.unlock_one(Unlocks.Target, [])
    if result["status"] != reset.UNLOCK_PURCHASE_FAILED:
        raise AssertionError("failed unlock purchase was hidden")


def test_no_progress_guard_prevents_spin() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.costs[Unlocks.Target] = {Items.Wood: 1}
    simulator.produce_amount = 0

    result = reset.unlock_one(Unlocks.Target, [])
    if result["status"] != reset.UNLOCK_NO_PROGRESS:
        raise AssertionError("zero-progress producer was allowed to spin")
    if simulator.unlock_calls:
        raise AssertionError("unlock was attempted before required inventory progress")


def test_missing_prerequisite_is_visible() -> None:
    simulator = ResetSimulator()
    simulator.install()
    simulator.costs[Unlocks.Target] = {}

    result = reset.unlock_one(Unlocks.Target, [Unlocks.A])
    if result["status"] != reset.UNLOCK_MISSING_PREREQUISITE:
        raise AssertionError("missing prerequisite was ignored")


def test_fastest_reset_does_not_depend_on_hidden_top_hat() -> None:
    source = (SAVE_DIRECTORY / "reset_progression.py").read_text()
    if "Unlocks.Top_Hat" in source:
        raise AssertionError("Fastest Reset still depends on hidden Top Hat progression")


def main() -> None:
    test_dependency_cycle_detection()
    test_default_plan_contains_explicit_target_levels()
    test_changing_cost_and_overshooting_producer()
    test_target_level_buys_each_level_with_refreshed_costs()
    test_nonzero_level_does_not_satisfy_higher_target()
    test_failure_report_identifies_target_missing_item_and_elapsed_time()
    test_failed_purchase_is_visible()
    test_no_progress_guard_prevents_spin()
    test_missing_prerequisite_is_visible()
    test_fastest_reset_does_not_depend_on_hidden_top_hat()
    print(
        "Passed reset plan cycles, live costs, overshoot, purchase failure, and no-progress tests"
    )


if __name__ == "__main__":
    main()
