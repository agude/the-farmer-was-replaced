from farm_config import (
    CACTUS_SIZE,
    CACTUS_START_X,
    CACTUS_START_Y,
    ENABLE_CACTUS_PATCH,
    ENABLE_CARROT_FILL,
    ENABLE_GRASS_STRIP,
    ENABLE_PUMPKIN_PATCH,
    ENABLE_TREE_BUSH_STRIP,
    PUMPKIN_SIZE,
    PUMPKIN_START_X,
    PUMPKIN_START_Y,
)


TREE_BUSH_END_X = 2
GRASS_START_X = 3
GRASS_END_X = 4


def is_cactus_region(x: int, y: int) -> bool:
    # Return whether coordinates lie inside the cactus patch geometry.
    return (
        x >= CACTUS_START_X
        and x < CACTUS_START_X + CACTUS_SIZE
        and y >= CACTUS_START_Y
        and y < CACTUS_START_Y + CACTUS_SIZE
    )


def is_pumpkin_region(x: int, y: int) -> bool:
    # Return whether coordinates lie inside the pumpkin patch geometry.
    return (
        x >= PUMPKIN_START_X
        and x < PUMPKIN_START_X + PUMPKIN_SIZE
        and y >= PUMPKIN_START_Y
        and y < PUMPKIN_START_Y + PUMPKIN_SIZE
    )


def target_entity_at(x: int, y: int):
    # Return the highest-priority enabled target for coordinates.
    if ENABLE_CACTUS_PATCH and is_cactus_region(x, y):
        return Entities.Cactus

    if ENABLE_PUMPKIN_PATCH and is_pumpkin_region(x, y):
        return Entities.Pumpkin

    if ENABLE_TREE_BUSH_STRIP and x <= TREE_BUSH_END_X:
        if (x + y) % 2:
            return Entities.Tree

        return Entities.Bush

    if ENABLE_GRASS_STRIP and x >= GRASS_START_X and x <= GRASS_END_X:
        return Entities.Grass

    if ENABLE_CARROT_FILL:
        return Entities.Carrot

    return None


def is_regular_target(target) -> bool:
    # Return whether a target belongs to the regular farming loop.
    return target != None and target != Entities.Cactus and target != Entities.Pumpkin
