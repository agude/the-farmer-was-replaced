from farm_config import REGULAR_WATER_THRESHOLD
from navigation import move_to
from watering import water_if_dry


def tend_tree_row() -> None:
    # Farm one checkerboard row forever.
    size = get_world_size()

    while True:
        for _ in range(size):
            x = get_pos_x()
            y = get_pos_y()

            # Keep trees separated orthogonally; use bushes on the other color.
            if (x + y) % 2:
                target = Entities.Tree
            else:
                target = Entities.Bush

            if can_harvest():
                harvest()

            if get_entity_type() != target:
                plant(target)

            water_if_dry(REGULAR_WATER_THRESHOLD)
            move(East)


def farm_trees() -> None:
    # On a 32x32 farm, spawn 31 workers and keep the original drone for row 32.
    size = get_world_size()
    move_to(0, 0)

    for _ in range(size - 1):
        spawn_drone(tend_tree_row)
        move(North)

    tend_tree_row()


farm_trees()
