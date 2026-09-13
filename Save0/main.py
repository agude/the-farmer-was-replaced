from navigation import move_to, distance_to
from planting import plant_current_tile
from pumpkins import farm_pumpkin_patch, is_pumpkin_tile
from watering import water_if_dry


WATER_THRESHOLD = 0.15


def tend_regular_tile() -> None:
    # Harvest, plant, and water the current non-pumpkin tile.
    if can_harvest():
        harvest()

    plant_current_tile()
    water_if_dry(WATER_THRESHOLD)


def get_regular_positions():
    # Return all non-pumpkin positions in snake-scan order.
    #
    # Build a snake over the entire world, but leave
    # pumpkin tiles out of the list.
    #
    positions = []
    size = get_world_size()

    for x in range(size):
        if x % 2 == 0:
            for y in range(size):
                if not is_pumpkin_tile(x, y):
                    positions.append((x, y))

        else:
            for y in range(size - 1, -1, -1):
                if not is_pumpkin_tile(x, y):
                    positions.append((x, y))

    return positions


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    if len(positions) == 0:
        return True

    first_x, first_y = positions[0]
    last_x, last_y = positions[len(positions) - 1]

    return distance_to(first_x, first_y) <= distance_to(last_x, last_y)


def farm_regular_tiles() -> None:
    # Visit and tend every regular tile in the shorter scan direction.
    positions = get_regular_positions()

    if len(positions) == 0:
        return

    if should_scan_forward(positions):
        for i in range(len(positions)):
            x, y = positions[i]

            move_to(x, y)
            tend_regular_tile()

    else:
        for i in range(len(positions) - 1, -1, -1):
            x, y = positions[i]

            move_to(x, y)
            tend_regular_tile()


move_to(0, 0)


while True:
    farm_regular_tiles()
    farm_pumpkin_patch()
