from farm_config import (
    POWER_TARGET,
    SUNFLOWER_HEIGHT,
    SUNFLOWER_START_X,
    SUNFLOWER_START_Y,
    SUNFLOWER_WATER_THRESHOLD,
    SUNFLOWER_WIDTH,
)
from navigation import distance_to, move_to
from planting import ensure_soil
from traversal import get_snake_positions
from traversal import should_scan_forward as choose_scan_direction
from watering import water_if_dry


SUNFLOWER_MIN_PETALS = 7
SUNFLOWER_MAX_PETALS = 15
SUNFLOWER_MIN_REMAINING = 9


def sunflower_end_x() -> int:
    # Return the inclusive right edge of the sunflower patch.
    return SUNFLOWER_START_X + SUNFLOWER_WIDTH - 1


def sunflower_end_y() -> int:
    # Return the inclusive top edge of the sunflower patch.
    return SUNFLOWER_START_Y + SUNFLOWER_HEIGHT - 1


def get_sunflower_positions():
    # Return patch positions in continuous snake order.
    return get_snake_positions(
        SUNFLOWER_START_X,
        SUNFLOWER_START_Y,
        SUNFLOWER_WIDTH,
        SUNFLOWER_HEIGHT,
    )


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    return choose_scan_direction(positions, distance_to)


def plant_sunflower() -> None:
    # Plant and water a sunflower on the current tile.
    ensure_soil()
    plant(Entities.Sunflower)
    water_if_dry(SUNFLOWER_WATER_THRESHOLD)


def prepare_sunflower_tile() -> bool:
    # Replace a previous crop, or report that it must mature first.
    entity = get_entity_type()

    if entity == Entities.Sunflower:
        water_if_dry(SUNFLOWER_WATER_THRESHOLD)
        return True

    if entity == Entities.Dead_Pumpkin or entity == None:
        plant_sunflower()
        return True

    if not can_harvest():
        water_if_dry(SUNFLOWER_WATER_THRESHOLD)
        return False

    harvest()
    plant_sunflower()
    return True


def plant_and_measure_sunflowers(positions):
    # Plant every sunflower and measure each one exactly once.
    positions_by_petals = [[], [], [], [], [], [], [], [], []]
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                if prepare_sunflower_tile():
                    petals = measure()
                    positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, y))
                else:
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                if prepare_sunflower_tile():
                    petals = measure()
                    positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, y))
                else:
                    still_pending = [(x, y)] + still_pending

        pending = still_pending

    return positions_by_petals


def wait_for_sunflowers(positions) -> None:
    # Revisit positions until every sunflower is mature.
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                if not can_harvest():
                    water_if_dry(SUNFLOWER_WATER_THRESHOLD)
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                if not can_harvest():
                    water_if_dry(SUNFLOWER_WATER_THRESHOLD)
                    still_pending = [(x, y)] + still_pending

        pending = still_pending


def harvest_sunflowers(positions_by_petals, harvest_count):
    # Harvest the highest-petal batch while leaving nine flowers behind.
    harvested_positions = []

    for petals in range(SUNFLOWER_MAX_PETALS, SUNFLOWER_MIN_PETALS - 1, -1):
        positions = positions_by_petals[petals - SUNFLOWER_MIN_PETALS]

        for i in range(len(positions)):
            if len(harvested_positions) >= harvest_count:
                return harvested_positions

            x, y = positions[i]

            move_to(x, y)
            harvest()
            harvested_positions.append((x, y))

    return harvested_positions


def replant_sunflowers(positions) -> None:
    # Replant the harvested batch after all harvests finish.
    for i in range(len(positions)):
        x, y = positions[i]

        move_to(x, y)
        plant_sunflower()


def needs_power() -> bool:
    # Return whether the farm should harvest another sunflower cycle.
    return num_items(Items.Power) < POWER_TARGET


def farm_sunflower_patch() -> None:
    # Replenish power with one complete measured-petal harvest cycle.
    if not needs_power():
        return

    positions = get_sunflower_positions()
    positions_by_petals = plant_and_measure_sunflowers(positions)

    wait_for_sunflowers(positions)
    harvest_count = len(positions) - SUNFLOWER_MIN_REMAINING
    harvested_positions = harvest_sunflowers(positions_by_petals, harvest_count)
    replant_sunflowers(harvested_positions)
