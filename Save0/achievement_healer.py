# Import-safe operations for the finite Healer achievement runner.


def clear_neighbor(direction, opposite) -> bool:
    if not move(direction):
        return False

    cleared = True
    if get_entity_type() != None:
        # An unguarded harvest intentionally clears the neighboring plant.
        harvest()
        cleared = get_entity_type() == None

    if not move(opposite):
        return False

    return cleared


def isolate_healer_tile() -> bool:
    return (
        clear_neighbor(East, West)
        and clear_neighbor(North, South)
        and clear_neighbor(West, East)
        and clear_neighbor(South, North)
    )


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

    if not prepare_healer_tile():
        return False

    if not isolate_healer_tile():
        quick_print("Healer failed: test plant could not be isolated")
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
