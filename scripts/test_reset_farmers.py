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
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
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
    test_gold_producer_repeats_funded_maze_batches()
    test_bone_producer_uses_reset_sized_dinosaur_batches()
    test_controller_uses_reset_farmer_hook()
    print(
        "Passed reset crop mappings, preconditions, unsupported-input, maze, and dinosaur producer tests"
    )


if __name__ == "__main__":
    main()
