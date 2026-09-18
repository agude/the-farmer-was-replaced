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


class Items:
    Wood = "Wood"


class ResetSimulator:
    def __init__(self) -> None:
        self.levels = {}
        self.inventory = {Items.Wood: 0}
        self.costs = {}
        self.unlock_results = {}
        self.unlock_calls = []
        self.produce_result = True
        self.produce_amount = 0

    def install(self) -> None:
        reset.Unlocks = Unlocks
        reset.Items = Items
        reset.num_unlocked = lambda unlock: self.levels.get(unlock, 0)
        reset.num_items = lambda item: self.inventory.get(item, 0)
        reset.get_cost = lambda unlock: self.costs.get(unlock)
        reset.unlock = self.unlock
        reset.produce_item = self.produce_item

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
    test_changing_cost_and_overshooting_producer()
    test_failed_purchase_is_visible()
    test_no_progress_guard_prevents_spin()
    test_missing_prerequisite_is_visible()
    test_fastest_reset_does_not_depend_on_hidden_top_hat()
    print(
        "Passed reset plan cycles, live costs, overshoot, purchase failure, and no-progress tests"
    )


if __name__ == "__main__":
    main()
