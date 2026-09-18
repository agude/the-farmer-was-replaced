"""Pure coordinate layout for achievement polyculture workers."""

HAY_MODE = "Hay"
CARROT_MODE = "Carrot"

PRIMARY_ROLE = "primary"
COMPANION_ROLE = "companion"
GUARD_ROLE = "guard"

TEMPLATE_SIZE = 4


def is_supported_mode(mode) -> bool:
    return mode == HAY_MODE or mode == CARROT_MODE


def get_region_anchor(x: int, y: int):
    return (x // TEMPLATE_SIZE) * TEMPLATE_SIZE, (y // TEMPLATE_SIZE) * TEMPLATE_SIZE


def get_primary_position(x: int, y: int):
    return get_region_anchor(x, y)


def is_primary_tile(x: int, y: int, mode) -> bool:
    return is_supported_mode(mode) and x % TEMPLATE_SIZE == 0 and y % TEMPLATE_SIZE == 0


def is_template_companion_tile(x: int, y: int, mode) -> bool:
    if not is_supported_mode(mode):
        return False

    local_x = x % TEMPLATE_SIZE
    local_y = y % TEMPLATE_SIZE
    return (local_x == 1 and local_y <= 1) or (local_x == 0 and local_y == 1)


def get_layout_role(x: int, y: int, mode):
    if is_primary_tile(x, y, mode):
        return PRIMARY_ROLE

    if is_template_companion_tile(x, y, mode):
        return COMPANION_ROLE

    return GUARD_ROLE


def get_primary_owner(x: int, y: int, mode):
    if not is_supported_mode(mode) or x < 0 or y < 0:
        return None

    return get_primary_position(x, y)


def is_allowed_companion_coordinate(
    x: int,
    y: int,
    primary_x: int,
    primary_y: int,
    mode,
) -> bool:
    if not is_template_companion_tile(x, y, mode):
        return False

    return get_primary_owner(x, y, mode) == (primary_x, primary_y)


def get_primary_positions(world_size: int, mode):
    positions = []

    for x in range(world_size):
        for y in range(world_size):
            if is_primary_tile(x, y, mode):
                positions.append((x, y))

    return positions


def get_companion_positions_for_primary(
    primary_x: int,
    primary_y: int,
    world_size: int,
    mode,
):
    positions = []

    for x in range(primary_x, primary_x + TEMPLATE_SIZE):
        for y in range(primary_y, primary_y + TEMPLATE_SIZE):
            if x >= world_size or y >= world_size:
                continue

            if is_allowed_companion_coordinate(x, y, primary_x, primary_y, mode):
                positions.append((x, y))

    return positions
