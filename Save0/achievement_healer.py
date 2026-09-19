# Import-safe operations for the finite Healer achievement runner.


def check_neighbor(direction, opposite) -> bool:
    if not move(direction):
        return False

    is_occupied = get_entity_type() != None
    if not move(opposite):
        return False

    return not is_occupied


def find_safe_tile() -> bool:
    size = get_world_size()

    for _row in range(size):
        for column in range(size):
            if (
                check_neighbor(East, West)
                and check_neighbor(North, South)
                and check_neighbor(West, East)
                and check_neighbor(South, North)
            ):
                return True

            if column < size - 1 and not move(East):
                return False

        if _row < size - 1 and not move(North):
            return False

    return False


def prepare_healer_tile() -> bool:
    entity = get_entity_type()

    if entity == Entities.Grass:
        return True

    if entity != None:
        # Harvesting an unready entity intentionally clears only this tile.
        harvest()
        if get_entity_type() != None:
            quick_print("Healer failed: isolated tile could not be cleared")
            return False

    if get_ground_type() != Grounds.Grassland:
        till()
        if get_ground_type() != Grounds.Grassland:
            quick_print("Healer failed: isolated tile is not Grassland")
            return False

    if not plant(Entities.Grass):
        quick_print("Healer failed: could not plant the test grass")
        return False

    if get_entity_type() != Entities.Grass:
        quick_print("Healer failed: test plant was not established")
        return False

    return True


def run_healer() -> bool:
    if num_items(Items.Fertilizer) <= 0:
        quick_print("Healer failed: Fertilizer is unavailable")
        return False

    if num_items(Items.Weird_Substance) <= 0:
        quick_print("Healer failed: Weird Substance is unavailable")
        return False

    if not find_safe_tile():
        quick_print("Healer failed: no isolated tile is available")
        return False

    if not prepare_healer_tile():
        return False

    if get_entity_type() != Entities.Grass:
        quick_print("Healer failed: test plant was not established")
        return False

    if not use_item(Items.Fertilizer):
        quick_print("Healer failed: could not use Fertilizer")
        return False

    if get_entity_type() != Entities.Grass:
        quick_print("Healer failed: Fertilizer changed the test plant")
        return False

    if not use_item(Items.Weird_Substance):
        quick_print("Healer failed: could not use Weird Substance")
        return False

    if get_entity_type() != Entities.Grass:
        quick_print("Healer failed: Weird Substance changed the test plant")
        return False

    quick_print("Healer complete")
    return True
