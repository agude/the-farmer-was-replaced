from navigation import move_to
from regular_farming import tend_regular_tile


def tend_carrot_row() -> None:
    # Farm one row of carrots forever.
    size = get_world_size()

    while True:
        for _ in range(size):
            # This handles harvest, soil preparation, planting, and watering.
            tend_regular_tile(Entities.Carrot)
            move(East)


def farm_carrots() -> None:
    # On a 32x32 farm, spawn 31 workers and keep the original drone for row 32.
    size = get_world_size()
    move_to(0, 0)

    for _ in range(size - 1):
        spawn_drone(tend_carrot_row)
        move(North)

    tend_carrot_row()


farm_carrots()
