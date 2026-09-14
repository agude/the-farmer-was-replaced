from navigation import move_to
from cactus import farm_cactus_patch
from farm_config import (
    ENABLE_CACTUS_PATCH,
    ENABLE_CARROT_FILL,
    ENABLE_GRASS_STRIP,
    ENABLE_PUMPKIN_PATCH,
    ENABLE_TREE_BUSH_STRIP,
)
from pumpkins import farm_pumpkin_patch
from regular_farming import farm_regular_tiles


if (
    ENABLE_CACTUS_PATCH
    or ENABLE_PUMPKIN_PATCH
    or ENABLE_TREE_BUSH_STRIP
    or ENABLE_GRASS_STRIP
    or ENABLE_CARROT_FILL
):
    move_to(0, 0)

    while True:
        farm_regular_tiles()

        if ENABLE_PUMPKIN_PATCH:
            farm_pumpkin_patch()

        if ENABLE_CACTUS_PATCH:
            farm_cactus_patch()
