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
    farmers.Grounds = type("Grounds", (), {"Grassland": "Grassland", "Soil": "Soil"})
    farmers.num_unlocked = lambda _unlock: 1
    farmers.get_world_size = lambda: 4
    farmers.num_items = lambda _item: 0
    farmers.get_cost = lambda _entity: {}
    farmers.move_to = lambda _x, _y: None
    farmers.get_entity_type = lambda: Entities.Grass
    farmers.can_harvest = lambda: False
    farmers.get_water = lambda: 1
    farmers.use_item = lambda _item: True
    farmers.till = lambda: None
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
    test_controller_uses_reset_farmer_hook()
    print(
        "Passed reset crop mappings, preconditions, unsupported-input, maze, and dinosaur producer tests"
    )


if __name__ == "__main__":
    main()
