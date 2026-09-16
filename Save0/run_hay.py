from farm_config import REGULAR_WATER_THRESHOLD
from navigation import move_to
from watering import water_if_dry


def random_color_hat():
    # Explicit allowlist: keep crop, trophy, gold, dinosaur, and novelty hats out.
    color_hats = []

    if num_unlocked(Hats.Brown_Hat):
        color_hats.append(Hats.Brown_Hat)

    if num_unlocked(Hats.Gray_Hat):
        color_hats.append(Hats.Gray_Hat)

    if num_unlocked(Hats.Green_Hat):
        color_hats.append(Hats.Green_Hat)

    if num_unlocked(Hats.Purple_Hat):
        color_hats.append(Hats.Purple_Hat)

    if len(color_hats) == 0:
        return Hats.Straw_Hat

    index = random() * len(color_hats) // 1
    return color_hats[index]


def tend_hay_tile() -> None:
    # Remove other crops and return soil to grassland before harvesting hay.
    entity = get_entity_type()

    if entity == Entities.Grass:
        if can_harvest():
            harvest()
        elif get_ground_type() == Grounds.Soil:
            # Grass on soil is not the target state; remove it before tilling.
            harvest()
    elif entity != None:
        # Harvest ready crops or remove unready crops while switching modes.
        harvest()

    if get_ground_type() == Grounds.Soil and get_entity_type() == None:
        till()

    water_if_dry(REGULAR_WATER_THRESHOLD)


def harvest_grass_row() -> None:
    # Harvest and water one row forever.
    size = get_world_size()
    change_hat(random_color_hat())

    while True:
        for _ in range(size):
            tend_hay_tile()

            # After size moves, the wrapped map returns us to the row start.
            move(East)


def farm_hay() -> None:
    # On a 32x32 farm, spawn 31 workers and keep the original drone for row 32.
    size = get_world_size()
    move_to(0, 0)

    for _ in range(size - 1):
        spawn_drone(harvest_grass_row)
        move(North)

    harvest_grass_row()


farm_hay()
