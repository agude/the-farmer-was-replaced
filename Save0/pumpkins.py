from navigation import distance_to, move_to
from planting import ensure_soil
from watering import water_if_dry


#
# Change ONLY these to resize / relocate the patch.
#
PUMPKIN_START_X = 0
PUMPKIN_START_Y = 0
PUMPKIN_SIZE = 16


PUMPKIN_WATER_THRESHOLD = 0.15


def pumpkin_end_x() -> int:
    # Return the inclusive right edge of the pumpkin patch.
    return PUMPKIN_START_X + PUMPKIN_SIZE - 1


def pumpkin_end_y() -> int:
    # Return the inclusive bottom edge of the pumpkin patch.
    return PUMPKIN_START_Y + PUMPKIN_SIZE - 1


def is_pumpkin_tile(x=None, y=None) -> bool:
    # Return whether a position lies inside the configured pumpkin patch.
    if x is None:
        x = get_pos_x()

    if y is None:
        y = get_pos_y()

    return (
        x >= PUMPKIN_START_X
        and x <= pumpkin_end_x()
        and y >= PUMPKIN_START_Y
        and y <= pumpkin_end_y()
    )


def plant_pumpkin() -> None:
    # Ensure soil and plant a pumpkin on the current tile.
    ensure_soil()
    plant(Entities.Pumpkin)


def pumpkin_is_ready() -> bool:
    # Maintain the current pumpkin tile and report when it is mature.
    entity = get_entity_type()

    #
    # Living pumpkin.
    #
    if entity == Entities.Pumpkin:
        if can_harvest():
            return True

        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Dead pumpkin.
    #
    if entity == Entities.Dead_Pumpkin:
        plant_pumpkin()
        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Empty tile.
    #
    if entity is None:
        plant_pumpkin()
        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Some other crop is occupying a tile that now
    # belongs to the pumpkin patch.
    #
    if can_harvest():
        harvest()
        plant_pumpkin()

    water_if_dry(PUMPKIN_WATER_THRESHOLD)

    return False


def get_pumpkin_positions():
    # Return all pumpkin-patch positions in continuous snake order.
    #
    # Continuous snake through the pumpkin square.
    #
    positions = []

    for x in range(PUMPKIN_START_X, pumpkin_end_x() + 1):
        column = x - PUMPKIN_START_X

        if column % 2 == 0:
            for y in range(PUMPKIN_START_Y, pumpkin_end_y() + 1):
                positions.append((x, y))

        else:
            for y in range(pumpkin_end_y(), PUMPKIN_START_Y - 1, -1):
                positions.append((x, y))

    return positions


def should_scan_forward(positions) -> bool:
    # Return whether the first pending tile is nearer than the last.
    first_x, first_y = positions[0]
    last_x, last_y = positions[len(positions) - 1]

    return distance_to(first_x, first_y) <= distance_to(last_x, last_y)


def wait_for_positions(positions) -> None:
    # Revisit pending tiles until each has produced a mature pumpkin.
    #
    # A position remains pending until we have
    # personally observed a mature living pumpkin
    # there.
    #
    pending = positions

    while len(pending) > 0:
        #
        # Endgame optimization:
        #
        # Only one pumpkin remains unresolved.
        # Go there ONCE and don't move again until
        # that pumpkin succeeds.
        #
        if len(pending) == 1:
            x, y = pending[0]

            move_to(x, y)

            while not pumpkin_is_ready():
                pass

            return

        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                if not pumpkin_is_ready():
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                if not pumpkin_is_ready():
                    #
                    # Preserve normal snake order.
                    #
                    still_pending = [(x, y)] + still_pending

        pending = still_pending


def farm_pumpkin_patch() -> None:
    # Grow the full patch, then harvest the final mature pumpkin.
    positions = get_pumpkin_positions()

    #
    # Every position begins unresolved.
    #
    # Once a mature pumpkin is seen there, that
    # position drops out permanently.
    #
    wait_for_positions(positions)

    #
    # When this returns, EVERY pumpkin has been
    # observed mature.
    #
    # We're standing on the final one, so harvest
    # immediately. No redundant verification pass.
    #
    harvest()
