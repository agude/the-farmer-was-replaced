def get_required_ground(entity):
    if entity == Entities.Grass or entity == Entities.Bush or entity == Entities.Tree:
        return Grounds.Grassland

    if (
        entity == Entities.Carrot
        or entity == Entities.Pumpkin
        or entity == Entities.Cactus
        or entity == Entities.Sunflower
    ):
        return Grounds.Soil

    return None


def ensure_ground_for_entity(entity) -> bool:
    required_ground = get_required_ground(entity)
    if required_ground == None:
        return False

    if get_ground_type() != required_ground:
        till()

    return get_ground_type() == required_ground


def ensure_soil() -> None:
    # Keep the existing generic helper for crop modules that only plant Soil crops.
    if get_ground_type() != Grounds.Soil:
        till()


def plant_target_entity(target) -> bool:
    # Plant the layout-selected entity on the current tile.
    if get_entity_type() == target:
        return True

    if not ensure_ground_for_entity(target):
        return False

    return plant(target)
