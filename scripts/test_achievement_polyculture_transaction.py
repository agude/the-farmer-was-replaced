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
import planting  # noqa: E402


class Entities:
    Grass = "Grass"
    Bush = "Bush"
    Tree = "Tree"
    Carrot = "Carrot"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Items:
    Hay = "Hay"
    Wood = "Wood"
    Carrot = "Carrot"
    Water = "Water"


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
        self.fail_companion_plant = False
        self.messages = []
        self.tick_count = 0
        self.water = {}
        self.inventory = {Items.Water: 1000}

    def install(self) -> None:
        transaction.Entities = Entities
        transaction.Grounds = Grounds
        transaction.Items = Items
        planting.Entities = Entities
        planting.Grounds = Grounds
        transaction.get_entity_type = self.get_entity_type
        transaction.get_ground_type = self.get_ground_type
        planting.get_ground_type = self.get_ground_type
        transaction.get_companion = self.get_companion
        transaction.get_world_size = lambda: 8
        transaction.move_to = self.move_to
        transaction.plant = self.plant
        transaction.till = self.till
        planting.till = self.till
        transaction.can_harvest = self.can_harvest
        transaction.harvest = self.harvest
        transaction.clear = self.clear
        transaction.quick_print = self.quick_print
        transaction.get_water = self.get_water
        transaction.num_items = self.num_items
        transaction.use_item = self.use_item
        transaction.get_tick_count = self.get_tick_count
        transaction.get_cost = self.get_cost

    def move_to(self, x: int, y: int) -> None:
        self.position = (x, y)
        self.events.append(("move", x, y))

    def get_entity_type(self):
        return self.entities.get(self.position)

    def get_water(self) -> int:
        return self.water.get(self.position, 0)

    def num_items(self, item) -> int:
        return self.inventory.get(item, 0)

    def use_item(self, item) -> bool:
        if self.inventory.get(item, 0) <= 0:
            return False
        self.inventory[item] -= 1
        self.water[self.position] = 1
        self.events.append(("water", self.position))
        return True

    def get_tick_count(self) -> int:
        return self.tick_count

    def get_cost(self, _entity):
        return {}

    def get_ground_type(self):
        return self.grounds.get(self.position, Grounds.Grassland)

    def get_companion(self):
        self.companion_reads += 1
        if self.companions:
            return self.companions.pop(0)
        return self.companion_entity, self.companion_position

    def plant(self, entity) -> bool:
        self.events.append(("plant", self.position, entity))
        if self.fail_companion_plant and entity != Entities.Grass:
            return False
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
        if self.get_entity_type() is None:
            return False

        self.harvest_count += 1
        self.entities.pop(self.position, None)
        return True

    def clear(self) -> None:
        self.events.append(("clear", self.position))
        self.entities.clear()
        self.position = (0, 0)

    def quick_print(self, message: str) -> None:
        self.messages.append(message)


class CarrotSequenceSimulator(TransactionSimulator):
    def __init__(self) -> None:
        super().__init__(Entities.Grass)
        self.companions = [
            (Entities.Grass, (4, 3)),
            (Entities.Bush, (5, 3)),
            (Entities.Tree, (4, 4)),
            (Entities.Bush, (5, 4)),
            (Entities.Tree, (4, 5)),
            (Entities.Bush, (5, 5)),
            (Entities.Tree, (4, 6)),
        ]
        self.inventory = {
            Items.Hay: 2,
            Items.Wood: 0,
            Items.Carrot: 0,
            Items.Water: 1000,
        }
        self.input_was_exhausted = False
        self.supply_harvests_before_exhaustion = None
        self.supply_visits = 0
        self.supply_visits_before_exhaustion = None
        self.supply_harvests = 0
        self.harvest_outputs = []

    def get_cost(self, entity):
        if entity == Entities.Carrot:
            return {Items.Hay: 1}
        return {}

    def move_to(self, x: int, y: int) -> None:
        super().move_to(x, y)
        if (x, y) == (7, 7):
            self.supply_visits += 1

    def plant(self, entity) -> bool:
        costs = {
            Entities.Grass: {},
            Entities.Bush: {},
            Entities.Tree: {},
            Entities.Carrot: {Items.Hay: 1},
        }
        for item in costs[entity]:
            if self.inventory.get(item, 0) < costs[entity][item]:
                return False
            self.inventory[item] -= costs[entity][item]

        self.events.append(("plant", self.position, entity))
        self.entities[self.position] = entity
        if self.inventory[Items.Hay] == 0:
            self.input_was_exhausted = True
            if self.supply_harvests_before_exhaustion is None:
                self.supply_harvests_before_exhaustion = self.supply_harvests
            if self.supply_visits_before_exhaustion is None:
                self.supply_visits_before_exhaustion = self.supply_visits
        return True

    def can_harvest(self) -> bool:
        return self.get_entity_type() in (
            Entities.Grass,
            Entities.Bush,
            Entities.Tree,
            Entities.Carrot,
        )

    def harvest(self) -> bool:
        entity = self.get_entity_type()
        self.events.append(("harvest", self.position))
        if entity is None:
            return False

        self.entities.pop(self.position, None)
        output_items = {
            Entities.Grass: Items.Hay,
            Entities.Bush: Items.Wood,
            Entities.Tree: Items.Wood,
            Entities.Carrot: Items.Carrot,
        }
        output_item = output_items[entity]
        self.inventory[output_item] += 1
        self.harvest_outputs.append((entity, output_item))
        if self.position == (7, 7):
            self.supply_harvests += 1
        return True


class UnsupportedInputSimulator(TransactionSimulator):
    def get_cost(self, entity):
        if entity == Entities.Carrot:
            return {Items.Wood: 1}
        return {}


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


def test_newly_planted_entities_are_watered_once() -> None:
    simulator = TransactionSimulator(Entities.Grass)
    simulator.install()

    if not transaction.plant_entity_for_transaction(Entities.Grass):
        raise AssertionError("newly planted entity was not established")
    if [event for event in simulator.events if event[0] == "water"] != [("water", (0, 0))]:
        raise AssertionError("newly planted entity was not watered once")


class SlowGrowthSimulator(TransactionSimulator):
    def __init__(self, checks_until_ready: int) -> None:
        super().__init__(Entities.Grass)
        self.checks_until_ready = checks_until_ready
        self.entities[(0, 0)] = Entities.Grass

    def can_harvest(self) -> bool:
        if self.checks_until_ready > 0:
            self.checks_until_ready -= 1
            self.tick_count += 1
            return False
        return True


def test_slow_growth_wait_uses_crop_readiness_and_ticks() -> None:
    simulator = SlowGrowthSimulator(30001)
    simulator.install()

    if not transaction.wait_for_primary(Entities.Grass):
        raise AssertionError("slow-growing primary hit a false readiness timeout")


def test_stuck_growth_has_a_bounded_failure() -> None:
    simulator = SlowGrowthSimulator(0)
    simulator.install()

    transaction.can_harvest = lambda: False
    if transaction.wait_for_primary(Entities.Grass):
        raise AssertionError("stuck primary reported readiness")


def test_different_existing_companion_is_replaced() -> None:
    simulator = TransactionSimulator(Entities.Carrot)
    simulator.entities[(4, 3)] = Entities.Tree
    simulator.install()

    if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("transaction did not replace the old companion")
    if ("harvest", (4, 3)) not in simulator.events:
        raise AssertionError("old companion was not harvested before replacement")
    if simulator.entities.get((4, 3)) != Entities.Carrot:
        raise AssertionError("requested companion was not established")


def test_changing_companion_requests_complete_one_hundred_transactions() -> None:
    simulator = TransactionSimulator(Entities.Grass)
    positions = [(4, 3), (5, 3), (4, 4), (5, 4)]
    entities = (Entities.Grass, Entities.Bush, Entities.Tree, Entities.Carrot)

    for index in range(100):
        position = positions[index % len(positions)]
        entity = entities[(index + index // len(positions)) % len(entities)]
        simulator.companions.append((entity, position))

    simulator.install()
    completed = 0
    for _transaction in range(100):
        if not transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
            raise AssertionError(f"changing companion failed at transaction {completed}")
        completed += 1

    if completed != 100:
        raise AssertionError("not all changing companion transactions completed")


def test_companion_failure_reports_transaction_state() -> None:
    simulator = TransactionSimulator(Entities.Carrot)
    simulator.fail_companion_plant = True
    simulator.install()

    if transaction.perform_polculture_transaction(3, 3, transaction.HAY_MODE):
        raise AssertionError("failed companion plant reported success")
    if len(simulator.messages) != 1:
        raise AssertionError(f"companion failure was not reported once: {simulator.messages}")

    message = simulator.messages[0]
    for expected in (
        "primary=(3,3)",
        "companion=(4,3)",
        "expected=Carrot",
        "observed=None",
        "phase=companion-setup",
    ):
        if expected not in message:
            raise AssertionError(f"diagnostic omitted {expected}: {message}")


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


def test_carrot_worker_replenishes_hay_after_unfavorable_companions() -> None:
    simulator = CarrotSequenceSimulator()
    simulator.install()

    if not transaction.run_polculture_worker_for_cycles(
        (3, 3, transaction.CARROT_MODE),
        7,
    ):
        raise AssertionError("Carrot worker stopped after unfavorable companions")
    if not simulator.input_was_exhausted:
        raise AssertionError("Carrot test never exhausted its initial Hay reserve")
    if simulator.supply_harvests_before_exhaustion != 0:
        raise AssertionError("Carrot worker visited its supply before Hay was exhausted")
    if simulator.supply_visits_before_exhaustion != 0:
        raise AssertionError("Carrot worker used supply-tile work with sufficient Hay")
    if simulator.supply_harvests == 0:
        raise AssertionError("Carrot worker never used its reserved Hay supply tile")
    for entity, output_item in simulator.harvest_outputs:
        expected_output = {
            Entities.Grass: Items.Hay,
            Entities.Bush: Items.Wood,
            Entities.Tree: Items.Wood,
            Entities.Carrot: Items.Carrot,
        }[entity]
        if output_item != expected_output:
            raise AssertionError(f"{entity} produced the wrong item: {output_item}")


def test_unsupported_carrot_input_reports_replenishment_phase() -> None:
    simulator = UnsupportedInputSimulator(Entities.Grass)
    simulator.install()

    if transaction.perform_polculture_transaction(3, 3, transaction.CARROT_MODE):
        raise AssertionError("unsupported Carrot input reported success")
    messages = [message for message in simulator.messages if "phase=input-replenishment" in message]
    if len(messages) != 1:
        raise AssertionError(f"unsupported input was not reported clearly: {simulator.messages}")
    message = messages[0]
    if "item=Wood" not in message:
        raise AssertionError(f"unsupported input diagnostic is incomplete: {message}")


def main() -> None:
    test_all_companion_entity_types()
    test_ground_conversion_matches_requested_entity()
    test_newly_planted_entities_are_watered_once()
    test_slow_growth_wait_uses_crop_readiness_and_ticks()
    test_stuck_growth_has_a_bounded_failure()
    test_different_existing_companion_is_replaced()
    test_changing_companion_requests_complete_one_hundred_transactions()
    test_companion_failure_reports_transaction_state()
    test_failed_plant_does_not_harvest_primary()
    test_out_of_region_request_is_rejected()
    test_invalid_request_can_reroll_own_primary()
    test_carrot_worker_replenishes_hay_after_unfavorable_companions()
    test_unsupported_carrot_input_reports_replenishment_phase()
    print(
        "Passed bounded polyculture companion, ground, failure, ownership, reroll, and sustainability tests"
    )


if __name__ == "__main__":
    main()
