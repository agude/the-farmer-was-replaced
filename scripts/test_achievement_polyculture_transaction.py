#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise one bounded achievement polyculture transaction."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import achievement_polyculture as transaction  # noqa: E402


class Entities:
    Grass = "Grass"
    Bush = "Bush"
    Tree = "Tree"
    Carrot = "Carrot"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class TransactionSimulator:
    def __init__(self, companion_entity, companion_position=(4, 3), plant_result=True):
        self.companion_entity = companion_entity
        self.companion_position = companion_position
        self.companions = []
        self.plant_result = plant_result
        self.position = (0, 0)
        self.entities = {}
        self.grounds = {}
        self.events = []
        self.harvest_count = 0
        self.companion_reads = 0
        self.mature = True

    def install(self) -> None:
        transaction.Entities = Entities
        transaction.Grounds = Grounds
        transaction.get_entity_type = self.get_entity_type
        transaction.get_ground_type = self.get_ground_type
        transaction.get_companion = self.get_companion
        transaction.get_world_size = lambda: 8
        transaction.move_to = self.move_to
        transaction.plant = self.plant
        transaction.till = self.till
        transaction.can_harvest = self.can_harvest
        transaction.harvest = self.harvest

    def move_to(self, x: int, y: int) -> None:
        self.position = (x, y)
        self.events.append(("move", x, y))

    def get_entity_type(self):
        return self.entities.get(self.position)

    def get_ground_type(self):
        return self.grounds.get(self.position, Grounds.Grassland)

    def get_companion(self):
        self.companion_reads += 1
        if self.companions:
            return self.companions.pop(0)
        return self.companion_entity, self.companion_position

    def plant(self, entity) -> bool:
        self.events.append(("plant", self.position, entity))
        if not self.plant_result:
            return False

        self.entities[self.position] = entity
        return True

    def till(self) -> None:
        self.events.append(("till", self.position))
        if self.get_ground_type() == Grounds.Grassland:
            self.grounds[self.position] = Grounds.Soil
        else:
            self.grounds[self.position] = Grounds.Grassland

    def can_harvest(self) -> bool:
        return self.mature and self.get_entity_type() in (
            Entities.Grass,
            Entities.Carrot,
        )

    def harvest(self) -> bool:
        self.events.append(("harvest", self.position))
        if not self.can_harvest():
            return False

        self.harvest_count += 1
        self.entities.pop(self.position, None)
        return True


def test_all_companion_entity_types() -> None:
    companion_entities = (
        Entities.Grass,
        Entities.Bush,
        Entities.Tree,
        Entities.Carrot,
    )

    for companion_entity in companion_entities:
        simulator = TransactionSimulator(companion_entity)
        simulator.install()

        if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
            raise AssertionError(f"transaction rejected {companion_entity}")
        if simulator.harvest_count != 1:
            raise AssertionError("transaction did not harvest the primary exactly once")
        if simulator.get_entity_type() != Entities.Grass:
            raise AssertionError("transaction did not restore the primary grass")


def test_ground_conversion_matches_requested_entity() -> None:
    grass_companion = TransactionSimulator(Entities.Grass)
    grass_companion.install()
    if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("grass companion transaction failed")
    if any(event[0] == "till" for event in grass_companion.events if isinstance(event, tuple)):
        raise AssertionError("grass companion converted an already suitable grassland tile")

    carrot_companion = TransactionSimulator(Entities.Carrot)
    carrot_companion.install()
    if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("carrot companion transaction failed")
    if not any(event[0] == "till" for event in carrot_companion.events):
        raise AssertionError("soil companion did not convert its ground")


def test_failed_plant_does_not_harvest_primary() -> None:
    simulator = TransactionSimulator(Entities.Carrot, plant_result=False)
    simulator.install()

    if transaction.perform_polculture_transaction(3, 3, transaction.CARROT_MODE):
        raise AssertionError("unaffordable primary plant reported success")
    if simulator.harvest_count != 0:
        raise AssertionError("failed primary plant harvested a crop")


def test_out_of_region_request_is_rejected() -> None:
    simulator = TransactionSimulator(Entities.Carrot, companion_position=(7, 3))
    simulator.install()

    if transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("out-of-template companion request was accepted")
    if any(event[0] == "plant" and event[1] == (7, 3) for event in simulator.events):
        raise AssertionError("out-of-region companion was planted")


def test_invalid_request_can_reroll_own_primary() -> None:
    simulator = TransactionSimulator(Entities.Bush)
    simulator.companions = [(Entities.Carrot, (7, 3)), (Entities.Bush, (4, 3))]
    simulator.install()

    if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("valid companion after bounded reroll was rejected")
    if simulator.harvest_count != 2:
        raise AssertionError("reroll did not harvest only the owned primary")


def main() -> None:
    test_all_companion_entity_types()
    test_ground_conversion_matches_requested_entity()
    test_failed_plant_does_not_harvest_primary()
    test_out_of_region_request_is_rejected()
    test_invalid_request_can_reroll_own_primary()
    print("Passed bounded polyculture companion, ground, failure, ownership, and reroll tests")


if __name__ == "__main__":
    main()
