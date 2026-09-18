#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify achievement inventory and elapsed-time measurements."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_metrics  # noqa: E402


class MeasurementSimulator:
    def __init__(self, item_amount: int, current_time: float) -> None:
        self.item_amount = item_amount
        self.current_time = current_time
        self.item_reads = 0
        self.time_reads = 0

    def num_items(self, _item) -> int:
        self.item_reads += 1
        return self.item_amount

    def get_time(self) -> float:
        self.time_reads += 1
        return self.current_time

    def install(self) -> None:
        achievement_metrics.num_items = self.num_items
        achievement_metrics.get_time = self.get_time


def test_positive_delta_excludes_existing_inventory() -> None:
    simulator = MeasurementSimulator(120, 10)
    simulator.install()

    starting_amount = achievement_metrics.start_item_measurement("Hay")
    simulator.item_amount = 155
    delta = achievement_metrics.get_item_delta("Hay", starting_amount)

    if starting_amount != 120 or delta != 35:
        raise AssertionError(f"inventory baseline was counted: {starting_amount}, {delta}")
    if simulator.item_reads != 2:
        raise AssertionError("item measurement did not read the balance at each boundary")


def test_consumed_inventory_is_reported_as_negative_delta() -> None:
    simulator = MeasurementSimulator(80, 10)
    simulator.install()

    delta = achievement_metrics.get_item_delta("Wood", 100)

    if delta != -20:
        raise AssertionError(f"consumed input was not reflected in the delta: {delta}")


def test_elapsed_time_and_rate_handle_clock_wrap() -> None:
    simulator = MeasurementSimulator(0, 20)
    simulator.install()
    starting_time = achievement_metrics.start_time_measurement()

    simulator.current_time = 35
    elapsed_time = achievement_metrics.get_elapsed_time(starting_time)
    rate = achievement_metrics.get_items_per_minute(120, elapsed_time)

    if elapsed_time != 15 or rate != 480:
        raise AssertionError(f"positive elapsed measurement changed: {elapsed_time}, {rate}")

    simulator.current_time = 5
    if achievement_metrics.get_elapsed_time(starting_time) != 0:
        raise AssertionError("clock wrap produced a negative elapsed duration")
    if achievement_metrics.get_items_per_minute(120, 0) != 0:
        raise AssertionError("zero elapsed time caused an invalid rate")


def main() -> None:
    test_positive_delta_excludes_existing_inventory()
    test_consumed_inventory_is_reported_as_negative_delta()
    test_elapsed_time_and_rate_handle_clock_wrap()
    print("Passed achievement item-delta, consumption, clock-wrap, and rate tests")


if __name__ == "__main__":
    main()
