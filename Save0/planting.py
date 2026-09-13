def ensure_soil() -> None:
    # Till the current tile if it is not already soil.
    if get_ground_type() != Grounds.Soil:
        till()


def plant_carrots() -> None:
    # Ensure soil and plant carrots unless a carrot is already present.
    if get_entity_type() == Entities.Carrot:
        return

    ensure_soil()
    plant(Entities.Carrot)


def plant_tree_or_bush() -> None:
    # Plant a tree or bush based on the current tile coordinates.
    if (get_pos_x() + get_pos_y()) % 2:
        target = Entities.Tree
    else:
        target = Entities.Bush

    if get_entity_type() == target:
        return

    plant(target)


def plant_grass() -> None:
    # Plant grass unless grass is already present on the tile.
    if get_entity_type() == Entities.Grass:
        return

    plant(Entities.Grass)


PLANTING_MAP = {
    0: plant_tree_or_bush,
    1: plant_tree_or_bush,
    2: plant_tree_or_bush,

    3: plant_grass,
    4: plant_grass,

    5: plant_carrots,
    6: plant_carrots,
    7: plant_carrots,
    8: plant_carrots,
    9: plant_carrots,
    10: plant_carrots,
    11: plant_carrots,
    12: plant_carrots,
    13: plant_carrots,
    14: plant_carrots,
    15: plant_carrots,
    16: plant_carrots,
    17: plant_carrots,
    18: plant_carrots,
    19: plant_carrots,
    20: plant_carrots,
    21: plant_carrots,
}


def plant_current_tile() -> None:
    # Run the planter assigned to the current x-column.
    PLANTING_MAP[get_pos_x()]()
