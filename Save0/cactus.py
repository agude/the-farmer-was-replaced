from farm_config import (
    CACTUS_SIZE,
    CACTUS_START_X,
    CACTUS_START_Y,
    CACTUS_WATER_THRESHOLD,
)
from navigation import distance_to, move_to
from planting import ensure_soil
from watering import water_if_dry


def cactus_end_x() -> int:
    # Return the inclusive right edge of the cactus patch.
    return CACTUS_START_X + CACTUS_SIZE - 1


def cactus_end_y() -> int:
    # Return the inclusive top edge of the cactus patch.
    return CACTUS_START_Y + CACTUS_SIZE - 1


def plant_cactus() -> None:
    # Ensure soil and plant a cactus on the current tile.
    ensure_soil()
    plant(Entities.Cactus)


def maintain_cactus_tile() -> bool:
    # Prepare the current tile and report whether its cactus is mature.
    entity = get_entity_type()

    if entity == Entities.Cactus:
        if can_harvest():
            return True

        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    if entity == Entities.Dead_Pumpkin or entity == None:
        plant_cactus()
        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    # Wait for an existing crop to mature before converting this tile.
    if not can_harvest():
        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    harvest()
    plant_cactus()
    water_if_dry(CACTUS_WATER_THRESHOLD)

    return False


def get_cactus_positions():
    # Return all cactus-patch positions in continuous snake order.
    positions = []

    for x in range(CACTUS_START_X, cactus_end_x() + 1):
        column = x - CACTUS_START_X

        if column % 2 == 0:
            for y in range(CACTUS_START_Y, cactus_end_y() + 1):
                positions.append((x, y))

        else:
            for y in range(cactus_end_y(), CACTUS_START_Y - 1, -1):
                positions.append((x, y))

    return positions


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    first_x, first_y = positions[0]
    last_x, last_y = positions[len(positions) - 1]

    return distance_to(first_x, first_y) <= distance_to(last_x, last_y)


def wait_for_cactuses(positions) -> None:
    # Revisit positions until every cactus is fully grown.
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                if not maintain_cactus_tile():
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                if not maintain_cactus_tile():
                    still_pending = [(x, y)] + still_pending

        pending = still_pending


def sort_cactus_row(y: int) -> None:
    # Sort one row west to east with an early-terminating cocktail sort.
    left_x = CACTUS_START_X
    right_x = cactus_end_x()

    while left_x < right_x:
        swapped = False

        for x in range(left_x, right_x):
            move_to(x, y)

            if measure() > measure(East):
                swap(East)
                swapped = True

        right_x -= 1

        if not swapped:
            return

        swapped = False

        for x in range(right_x, left_x, -1):
            move_to(x, y)

            if measure() < measure(West):
                swap(West)
                swapped = True

        left_x += 1

        if not swapped:
            return


def sort_cactus_rows() -> None:
    # Sort every row west to east with adjacent swaps.
    for y in range(CACTUS_START_Y, cactus_end_y() + 1):
        sort_cactus_row(y)


def sort_cactus_column(x: int) -> None:
    # Sort one column south to north with an early-terminating cocktail sort.
    bottom_y = CACTUS_START_Y
    top_y = cactus_end_y()

    while bottom_y < top_y:
        swapped = False

        for y in range(bottom_y, top_y):
            move_to(x, y)

            if measure() > measure(North):
                swap(North)
                swapped = True

        top_y -= 1

        if not swapped:
            return

        swapped = False

        for y in range(top_y, bottom_y, -1):
            move_to(x, y)

            if measure() < measure(South):
                swap(South)
                swapped = True

        bottom_y += 1

        if not swapped:
            return


def sort_cactus_columns() -> None:
    # Sort every column south to north with adjacent swaps.
    for x in range(CACTUS_START_X, cactus_end_x() + 1):
        sort_cactus_column(x)


def sort_cactuses() -> None:
    # Arrange the patch in the order required for bulk harvesting.
    sort_cactus_rows()
    sort_cactus_columns()


def farm_cactus_patch() -> None:
    # Grow, sort, and bulk-harvest the cactus patch.
    positions = get_cactus_positions()

    wait_for_cactuses(positions)
    sort_cactuses()

    move_to(CACTUS_START_X, CACTUS_START_Y)

    if can_harvest():
        harvest()
