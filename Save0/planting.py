def ensure_soil() -> None:
    # Till the current tile if it is not already soil.
    if get_ground_type() != Grounds.Soil:
        till()


def plant_target_entity(target) -> None:
    # Plant the layout-selected entity on the current tile.
    if get_entity_type() == target:
        return

    if target == Entities.Carrot:
        ensure_soil()

    plant(target)
