from farm_config import FERTILIZE_PUMPKIN_HARVEST
from fertilizing import fertilize_before_harvest
from navigation import distance_to, move_to
from pumpkins import pumpkin_is_ready


def grow_row_until_ready() -> None:
    # Remember unresolved positions so mature pumpkins are never checked again.
    size = get_world_size()
    row_y = get_pos_y()
    pending = list(range(size))

    while len(pending) > 0:
        # Once one pumpkin remains, stay on it until it is mature. This is
        # especially useful after pumpkin_is_ready() has just replanted it.
        if len(pending) == 1:
            move_to(pending[0], row_y)

            while not pumpkin_is_ready():
                pass

            return

        still_pending = []

        # The row is scanned from whichever unresolved bound is closer,
        # including the possibility that the shortest route wraps around.
        if distance_to(pending[0], row_y) <= distance_to(pending[-1], row_y):
            for i in range(len(pending)):
                x = pending[i]
                move_to(x, row_y)

                if not pumpkin_is_ready():
                    still_pending.append(x)
        else:
            for i in range(len(pending) - 1, -1, -1):
                x = pending[i]
                move_to(x, row_y)

                if not pumpkin_is_ready():
                    still_pending = [x] + still_pending

        pending = still_pending


def grow_full_patch() -> None:
    # Use the entire current world as one pumpkin patch.
    size = get_world_size()
    workers = []

    move_to(0, 0)

    # The original drone counts toward the limit, so spawn the other rows.
    for _ in range(size - 1):
        worker = spawn_drone(grow_row_until_ready)

        if worker == None:
            # Fallback if fewer than size drones are available.
            grow_row_until_ready()
        else:
            workers.append(worker)

        move(North)

    # The original drone owns the final row.
    grow_row_until_ready()

    # Barrier: every worker must report a completely mature row.
    for worker in workers:
        wait_for(worker)


def harvest_full_patch() -> None:
    # Move to the final tile, which is the harvest candidate after the barrier.
    size = get_world_size()
    move_to(size - 1, size - 1)

    while not can_harvest():
        do_a_flip()

    if FERTILIZE_PUMPKIN_HARVEST:
        fertilize_before_harvest()

    harvest()


while True:
    grow_full_patch()
    harvest_full_patch()
