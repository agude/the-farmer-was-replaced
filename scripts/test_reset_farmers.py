#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify reset-safe producer dispatch and precondition boundaries."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import reset_farmers as farmers  # noqa: E402
import planting  # noqa: E402


class Entities:
    Grass = "Grass"
    Bush = "Bush"
    Tree = "Tree"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"
    Cactus = "Cactus"
    Sunflower = "Sunflower"


class Items:
    Hay = "Hay"
    Wood = "Wood"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Cactus = "Cactus"
    Power = "Power"
    Fertilizer = "Fertilizer"
    Weird_Substance = "Weird Substance"
    Gold = "Gold"
    Bone = "Bone"
    Water = "Water"


class Unlocks:
    Plant = "Plant"
    Grass = "Grass"
    Trees = "Trees"
    Carrots = "Carrots"
    Pumpkins = "Pumpkins"
    Cactus = "Cactus"
    Sunflowers = "Sunflowers"
    Watering = "Watering"
    Fertilizer = "Fertilizer"
    Mazes = "Mazes"
    Dinosaurs = "Dinosaurs"


def install() -> None:
    farmers.Entities = Entities
    farmers.Items = Items
    farmers.Unlocks = Unlocks
    grounds = type("Grounds", (), {"Grassland": "Grassland", "Soil": "Soil"})
    farmers.Grounds = grounds
    planting.Entities = Entities
    planting.Grounds = grounds
    farmers.num_unlocked = lambda _unlock: 1
    farmers.get_world_size = lambda: 4
    farmers.num_items = lambda _item: 0
    farmers.get_cost = lambda _entity: {}
    farmers.move_to = lambda _x, _y: None
    farmers.get_entity_type = lambda: Entities.Grass
    planting.get_ground_type = lambda: grounds.Grassland
    farmers.can_harvest = lambda: False
    farmers.get_water = lambda: 1
    farmers.use_item = lambda _item: True
    farmers.till = lambda: None
    planting.till = lambda: None
    farmers.plant = lambda _entity: True
    farmers.harvest = lambda: True
    farmers.clear = lambda: None
    farmers.get_tick_count = lambda: 0
    farmers.do_a_flip = lambda: None
    farmers.quick_print = lambda _message: None


def test_wood_preparation_repairs_soil_and_preserves_grassland() -> None:
    install()
    ground = [farmers.Grounds.Soil]
    till_calls = []

    planting.get_ground_type = lambda: ground[0]

    def till() -> None:
        till_calls.append(True)
        ground[0] = farmers.Grounds.Grassland

    planting.till = till
    farmers.get_entity_type = lambda: None
    farmers.get_cost = lambda _entity: {}
    farmers.ensure_ground_for_entity = planting.ensure_ground_for_entity

    if not farmers.prepare_crop(Entities.Bush, 0):
        raise AssertionError("Wood preparation failed from Soil")
    if not till_calls or ground[0] != farmers.Grounds.Grassland:
        raise AssertionError("Wood preparation did not repair Soil to Grassland")

    till_calls.clear()
    if not farmers.prepare_crop(Entities.Bush, 0):
        raise AssertionError("Wood preparation failed from Grassland")
    if till_calls:
        raise AssertionError("Wood preparation retilled an existing Grassland tile")


def test_dead_pumpkin_is_cleared_before_replanting() -> None:
    install()
    state = {"entity": Entities.Dead_Pumpkin}
    events = []
    farmers.get_entity_type = lambda: state["entity"]
    farmers.clear = lambda: events.append("clear") or state.update(entity=None)
    farmers.get_cost = lambda _entity: {}
    farmers.ensure_ground_for_entity = lambda _entity: True
    farmers.plant = lambda entity: (
        events.append(("plant", entity)) or state.update(entity=entity) or True
    )

    if not farmers.prepare_crop(Entities.Pumpkin, 0):
        raise AssertionError("dead Pumpkin was not replaced")
    if events != ["clear", ("plant", Entities.Pumpkin)]:
        raise AssertionError(f"dead Pumpkin recovery actions changed: {events}")


def test_weird_substance_fertilizes_before_harvesting() -> None:
    install()
    state = {
        "entity": Entities.Grass,
        "fertilizer": 1,
        "weird_substance": 0,
    }
    events = []
    farmers.get_world_size = lambda: 1
    farmers.num_unlocked = lambda _unlock: 1
    farmers.num_items = lambda item: {
        Items.Fertilizer: state["fertilizer"],
        Items.Weird_Substance: state["weird_substance"],
    }.get(item, 0)
    farmers.get_entity_type = lambda: state["entity"]
    farmers.get_cost = lambda _entity: {}
    farmers.ensure_ground_for_entity = lambda _entity: True
    farmers.can_harvest = lambda: True

    def use_item(item) -> bool:
        if item != Items.Fertilizer or state["fertilizer"] <= 0:
            return False
        state["fertilizer"] -= 1
        events.append("fertilizer")
        return True

    def harvest() -> bool:
        state["weird_substance"] += 1
        events.append("harvest")
        return True

    farmers.use_item = use_item
    farmers.harvest = harvest
    if not farmers.farm_weird_substance(1):
        raise AssertionError("Weird Substance producer did not complete")
    if events != ["fertilizer", "harvest"]:
        raise AssertionError(f"Weird Substance was harvested before fertilizing: {events}")


def test_crop_producer_completes_target_and_rotates_world_tiles() -> None:
    install()
    state = {"item": 0, "entity": None, "position": (0, 0)}
    visited = []

    farmers.get_world_size = lambda: 2
    farmers.num_unlocked = lambda _unlock: 1
    farmers.num_items = lambda item: state["item"] if item == Items.Wood else 0
    farmers.get_entity_type = lambda: state["entity"]
    farmers.move_to = lambda x, y: state.update(position=(x, y)) or visited.append((x, y))
    farmers.get_cost = lambda _entity: {}
    farmers.ensure_ground_for_entity = lambda _entity: True
    farmers.plant = lambda entity: state.update(entity=entity) or True
    farmers.can_harvest = lambda: state["entity"] == Entities.Bush

    def harvest() -> bool:
        state["item"] += 1
        state["entity"] = None
        return True

    farmers.harvest = harvest

    if not farmers.farm_crop(Items.Wood, Entities.Bush, Unlocks.Plant, 300, 0):
        raise AssertionError("crop producer stopped before reaching its target")
    if state["item"] != 300:
        raise AssertionError(f"crop producer target changed: {state['item']}")
    if set(visited) != {(0, 0), (1, 0), (1, 1), (0, 1)}:
        raise AssertionError("crop producer did not rotate across the world")


def test_slow_crop_waits_for_clock_progress_and_stuck_crop_fails() -> None:
    install()
    state = {"ticks": 0}
    farmers.get_entity_type = lambda: Entities.Carrot
    farmers.can_harvest = lambda: state["ticks"] >= 3
    farmers.get_tick_count = lambda: state["ticks"]
    farmers.do_a_flip = lambda: state.update(ticks=state["ticks"] + 1)

    if not farmers.wait_for_crop(Entities.Carrot):
        raise AssertionError("slow crop did not wait for maturity")

    state["ticks"] = 0
    farmers.MAX_STAGNANT_CROP_WAIT_CHECKS = 3
    farmers.do_a_flip = lambda: None
    if farmers.wait_for_crop(Entities.Carrot):
        raise AssertionError("stuck crop incorrectly reported maturity")
    farmers.MAX_STAGNANT_CROP_WAIT_CHECKS = 1000


def test_crop_mapping_covers_reset_outputs() -> None:
    install()
    outputs = [
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Power,
    ]
    for item in outputs:
        if farmers.get_crop_spec(item) is None:
            raise AssertionError(f"reset producer lost crop mapping for {item}")

    if farmers.get_crop_spec(Items.Hay)[1] is not None:
        raise AssertionError("natural Grass incorrectly requires a Grass unlock")
    if farmers.get_crop_spec(Items.Wood)[1] != Unlocks.Plant:
        raise AssertionError("early Bush production incorrectly requires Trees")


def test_locked_crop_and_unsupported_input_fail_before_actions() -> None:
    install()
    farmers.num_unlocked = lambda unlock: 0 if unlock == Unlocks.Plant else 1
    if farmers.produce_item(Items.Wood, 1):
        raise AssertionError("locked crop producer reported success")
    if farmers.produce_item(Items.Water, 1):
        raise AssertionError("unsupported reset input reported success")


def test_fertilizer_preparation_does_not_harvest_mature_grass() -> None:
    install()
    harvest_calls = []
    farmers.can_harvest = lambda: True
    farmers.harvest = lambda: harvest_calls.append(True) or True

    if not farmers.prepare_crop(Entities.Grass, 0, False):
        raise AssertionError("mature Grass could not be retained for fertilizing")
    if harvest_calls:
        raise AssertionError("fertilizer preparation harvested mature Grass")


def test_gold_producer_repeats_funded_maze_batches() -> None:
    install()
    state = {Items.Gold: 0, Items.Weird_Substance: 6}
    worker_calls = []

    farmers.num_unlocked = lambda _unlock: 1
    farmers.num_items = lambda item: state.get(item, 0)
    farmers.get_reusable_maze_substance_budget = lambda _limit: 2
    farmers.ensure_planting_inputs = lambda _entity, _count, _depth: True

    def run_worker(_maze_index, _relocation_limit):
        worker_calls.append(True)
        state[Items.Weird_Substance] -= 2
        state[Items.Gold] += 2
        return {"reason": farmers.MAZE_WORKER_COMPLETE}

    farmers.run_reusable_maze_worker = run_worker
    if not farmers.farm_gold(5, 0):
        raise AssertionError("Gold producer stopped before reaching its target")
    if len(worker_calls) != 3:
        raise AssertionError("Gold producer did not repeat one-relocation maze batches")


def test_bone_producer_uses_reset_sized_dinosaur_batches() -> None:
    install()
    state = {Items.Bone: 0, Items.Cactus: 0}
    run_calls = []

    farmers.num_unlocked = lambda _unlock: 1
    farmers.num_items = lambda item: state.get(item, 0)
    farmers.get_apple_cactus_cost = lambda: 2
    farmers.get_full_run_cactus_cost = lambda _size, apple_cost: apple_cost * 4

    def farm_cactus(_item, _entity, _unlock, amount, _depth):
        state[Items.Cactus] += amount
        return True

    def run_dinosaur(_size):
        run_calls.append(True)
        state[Items.Cactus] -= 8
        state[Items.Bone] += 5
        return True

    farmers.farm_crop = farm_cactus
    farmers.run_dinosaur_once = run_dinosaur
    if not farmers.farm_bones(11, 0):
        raise AssertionError("Bone producer stopped before reaching its target")
    if len(run_calls) != 3:
        raise AssertionError("Bone producer did not repeat reset-sized dinosaur batches")


def test_controller_uses_reset_farmer_hook() -> None:
    source = (SAVE_DIRECTORY / "reset_progression.py").read_text()
    if "from reset_farmers import produce_item" not in source:
        raise AssertionError("reset controller is not connected to reset-safe farmers")
    source = (SAVE_DIRECTORY / "reset_farmers.py").read_text()
    for required_name in (
        "farm_gold",
        "farm_bones",
        "run_reusable_maze_worker",
        "run_dinosaur_once",
    ):
        if required_name not in source:
            raise AssertionError(f"reset farmers lost bounded stage {required_name}")


def main() -> None:
    test_crop_mapping_covers_reset_outputs()
    test_locked_crop_and_unsupported_input_fail_before_actions()
    test_fertilizer_preparation_does_not_harvest_mature_grass()
    test_wood_preparation_repairs_soil_and_preserves_grassland()
    test_dead_pumpkin_is_cleared_before_replanting()
    test_weird_substance_fertilizes_before_harvesting()
    test_crop_producer_completes_target_and_rotates_world_tiles()
    test_slow_crop_waits_for_clock_progress_and_stuck_crop_fails()
    test_gold_producer_repeats_funded_maze_batches()
    test_bone_producer_uses_reset_sized_dinosaur_batches()
    test_controller_uses_reset_farmer_hook()
    print(
        "Passed reset crop mappings, preconditions, unsupported-input, maze, and dinosaur producer tests"
    )


if __name__ == "__main__":
    main()
