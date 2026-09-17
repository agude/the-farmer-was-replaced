#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise Top Hat policy, live resampling, safeguards, and producer routing."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import top_hat  # noqa: E402
import resource_costs  # noqa: E402


class Items:
    Hay = "Hay"
    Wood = "Wood"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Cactus = "Cactus"
    Power = "Power"
    Weird_Substance = "Weird Substance"
    Gold = "Gold"
    Fertilizer = "Fertilizer"


class Entities:
    Tree = "Tree"
    Bush = "Bush"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Cactus = "Cactus"
    Sunflower = "Sunflower"


class Unlocks:
    Top_Hat = "Top Hat"


top_hat.Items = Items
top_hat.Entities = Entities
top_hat.Unlocks = Unlocks
REAL_PERFORM_NEXT_ACTION = top_hat.perform_next_action
REAL_RUN_ITEM_PRODUCER = top_hat.run_item_producer
inventory = {}
messages = []
unlock_calls = []


def reset_inventory() -> None:
    inventory.clear()
    for item in (
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Power,
        Items.Weird_Substance,
        Items.Gold,
        Items.Fertilizer,
    ):
        inventory[item] = 0

    messages.clear()
    unlock_calls.clear()
    top_hat.num_items = lambda item: inventory[item]
    resource_costs.num_items = lambda item: inventory[item]
    top_hat.quick_print = lambda message: messages.append(message)
    top_hat.num_unlocked = lambda unlock: 0
    top_hat.unlock = lambda unlock: unlock_calls.append(unlock) or True
    top_hat.get_world_size = lambda: 4
    top_hat.POWER_LOW_WATERMARK = 10
    top_hat.POWER_HIGH_WATERMARK = 20


def test_already_unlocked_returns_immediately() -> None:
    reset_inventory()
    top_hat.num_unlocked = lambda unlock: 1
    top_hat.get_top_hat_cost = lambda: (_ for _ in ()).throw(
        AssertionError("already-unlocked state queried costs")
    )

    if not top_hat.farm_top_hat():
        raise AssertionError("already-unlocked state reported failure")

    if unlock_calls:
        raise AssertionError("already-unlocked state called unlock")


def test_empty_cost_stops_visibly() -> None:
    reset_inventory()
    top_hat.get_top_hat_cost = lambda: None

    if top_hat.farm_top_hat():
        raise AssertionError("empty Top Hat cost reported success")

    if not messages:
        raise AssertionError("empty Top Hat cost was not reported")

    if unlock_calls:
        raise AssertionError("empty Top Hat cost called unlock")


def test_dynamic_costs_resample_and_allow_overshoot() -> None:
    reset_inventory()
    cost_calls = []

    def live_cost():
        cost_calls.append(inventory[Items.Wood])
        if len(cost_calls) < 4:
            return {Items.Wood: 2}

        return {Items.Wood: 4}

    top_hat.get_top_hat_cost = live_cost

    def produce_wood(cost) -> bool:
        inventory[Items.Wood] += 3
        return True

    top_hat.perform_next_action = produce_wood
    if not top_hat.farm_top_hat():
        raise AssertionError("dynamic-cost planner did not unlock")

    if inventory[Items.Wood] != 6:
        raise AssertionError("planner did not preserve an overshooting production cycle")

    if len(cost_calls) < 5:
        raise AssertionError("planner did not resample live costs after its action")

    if len(unlock_calls) != 1:
        raise AssertionError("dynamic-cost planner unlocked an unexpected number of times")


def test_no_progress_stops_after_repeated_action() -> None:
    reset_inventory()
    top_hat.get_top_hat_cost = lambda: {Items.Wood: 2}
    action_calls = []

    def no_progress(cost) -> bool:
        action_calls.append(cost)
        return False

    top_hat.perform_next_action = no_progress
    if top_hat.farm_top_hat():
        raise AssertionError("no-progress planner reported success")

    if len(action_calls) != top_hat.NO_PROGRESS_LIMIT:
        raise AssertionError("no-progress planner did not stop at its limit")

    if "no progress" not in messages[-1].lower():
        raise AssertionError("no-progress planner did not report its stop reason")


def test_unlock_failure_is_called_once() -> None:
    reset_inventory()
    inventory[Items.Wood] = 5
    top_hat.get_top_hat_cost = lambda: {Items.Wood: 2}
    top_hat.unlock = lambda unlock: unlock_calls.append(unlock) or False

    if top_hat.farm_top_hat():
        raise AssertionError("unlock failure reported success")

    if len(unlock_calls) != 1:
        raise AssertionError("unlock failure retried the unlock")


def test_policy_priority() -> None:
    reset_inventory()
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    cost = {
        Items.Hay: 1,
        Items.Wood: 1,
        Items.Carrot: 1,
        Items.Pumpkin: 1,
        Items.Cactus: 1,
        Items.Power: 1,
        Items.Weird_Substance: 1,
        Items.Gold: 1,
    }
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True

    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("power was not the first missing production target")

    inventory[Items.Power] = 20
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Cactus:
        raise AssertionError("cactus was not prioritized after power")

    inventory[Items.Cactus] = 1
    inventory[Items.Gold] = 1
    inventory[Items.Weird_Substance] = 1
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Carrot:
        raise AssertionError("carrots were not deferred until prerequisites completed")


def test_power_reaches_high_watermark_without_live_power_cost() -> None:
    reset_inventory()
    cost = {Items.Wood: 1}
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True

    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("low power watermark did not trigger replenishment")

    inventory[Items.Power] = 10
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("power did not refill from low to high watermark")

    inventory[Items.Power] = 20
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Wood:
        raise AssertionError("planner did not leave power mode at the high watermark")


def test_tree_budget_counts_checkerboard_tiles() -> None:
    reset_inventory()
    original_budget = top_hat.get_planting_budget
    calls = []

    def record_budget(entity, width, height):
        calls.append((entity, width, height))
        return {Items.Wood: width * height}

    top_hat.get_planting_budget = record_budget
    budget = top_hat.get_tree_cycle_budget(4, 3)
    top_hat.get_planting_budget = original_budget

    if budget != {Items.Wood: 12}:
        raise AssertionError(f"tree budget counted non-checkerboard tiles: {budget}")

    if calls != [(Entities.Tree, 6, 1), (Entities.Bush, 6, 1)]:
        raise AssertionError(f"checkerboard geometry was not passed to costs: {calls}")


def test_protected_balance_plus_cycle_budget() -> None:
    reset_inventory()
    inventory[Items.Wood] = 5
    top_hat.get_planting_budget = lambda entity, width, height: {Items.Wood: 2}
    cost = {Items.Wood: 3}

    if not top_hat.can_run_carrots(cost, 2):
        raise AssertionError("exact protected balance plus cycle budget was rejected")

    inventory[Items.Wood] = 4
    if top_hat.can_run_carrots(cost, 2):
        raise AssertionError("underfunded protected balance was accepted")


def test_missing_fertilizer_reports_wait() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    top_hat.get_world_size = lambda: 4

    if top_hat.run_item_producer(Items.Weird_Substance, {Items.Weird_Substance: 2}):
        raise AssertionError("missing fertilizer reported Weird Substance progress")

    if "fertilizer" not in messages[-1].lower():
        raise AssertionError("missing fertilizer did not identify its feedstock")


def test_gold_and_cactus_receive_live_policy() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    inventory[Items.Weird_Substance] = 6
    inventory[Items.Fertilizer] = 1
    top_hat.get_maze_substance_cost = lambda: 5
    maze_calls = []
    cactus_calls = []
    top_hat.farm_mazes = lambda gold, reserve: maze_calls.append((gold, reserve)) or True
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True

    cost = {Items.Gold: 10, Items.Weird_Substance: 1}
    if not top_hat.run_item_producer(Items.Gold, cost):
        raise AssertionError("funded maze action reported failure")

    if maze_calls != [(10, 1)]:
        raise AssertionError(f"maze did not receive live targets: {maze_calls}")

    top_hat.can_run_cactus = lambda policy, size: True
    if not top_hat.run_item_producer(Items.Cactus, cost):
        raise AssertionError("funded cactus action reported failure")

    if cactus_calls[-1][5] != 1 or cactus_calls[-1][7] is not True:
        raise AssertionError("cactus did not receive live Weird Substance policy")


def main() -> None:
    test_already_unlocked_returns_immediately()
    test_empty_cost_stops_visibly()
    test_dynamic_costs_resample_and_allow_overshoot()
    test_no_progress_stops_after_repeated_action()
    test_unlock_failure_is_called_once()
    test_policy_priority()
    test_power_reaches_high_watermark_without_live_power_cost()
    test_tree_budget_counts_checkerboard_tiles()
    test_protected_balance_plus_cycle_budget()
    test_missing_fertilizer_reports_wait()
    test_gold_and_cactus_receive_live_policy()
    print("Passed Top Hat planner policy, live-cost, safeguard, and routing tests")


if __name__ == "__main__":
    main()
