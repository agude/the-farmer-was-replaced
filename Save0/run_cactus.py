from farm_config import (
    CACTUS_REVERSE_SORT,
    CACTUS_SIZE,
    CACTUS_START_X,
    CACTUS_START_Y,
    FERTILIZE_CACTUS_HARVEST,
)
from fertilizing import fertilize_before_harvest
from cactus import (
    cactus_end_x,
    maintain_cactus_tile,
    sort_cactus_column,
    sort_cactus_row,
)
from navigation import distance_to, move_to


def grow_cactus_row_until_ready() -> None:
    # Remember mature cactuses and revisit only unresolved positions.
    row_y = get_pos_y()
    pending = []

    for x in range(CACTUS_START_X, cactus_end_x() + 1):
        pending.append(x)

    while len(pending) > 0:
        # Stay on the final cactus until it is mature, including after a
        # dead cactus has just been replanted.
        if len(pending) == 1:
            move_to(pending[0], row_y)

            while not maintain_cactus_tile():
                pass

            return

        still_pending = []

        # Pick the nearer unresolved bound. distance_to() includes wrapping.
        if distance_to(pending[0], row_y) <= distance_to(pending[-1], row_y):
            for i in range(len(pending)):
                x = pending[i]
                move_to(x, row_y)

                if not maintain_cactus_tile():
                    still_pending.append(x)
        else:
            for i in range(len(pending) - 1, -1, -1):
                x = pending[i]
                move_to(x, row_y)

                if not maintain_cactus_tile():
                    still_pending = [x] + still_pending

        pending = still_pending


def sort_current_row() -> None:
    # The worker starts on the row it owns.
    sort_cactus_row(get_pos_y())


def sort_current_row_reverse() -> None:
    # Sort west to east in descending order for the inversion achievement.
    left_x = CACTUS_START_X
    right_x = cactus_end_x()
    row_y = get_pos_y()

    while left_x < right_x:
        swapped = False

        for x in range(left_x, right_x):
            move_to(x, row_y)

            if measure() < measure(East):
                swap(East)
                swapped = True

        right_x -= 1

        if not swapped:
            return

        swapped = False

        for x in range(right_x, left_x, -1):
            move_to(x, row_y)

            if measure() > measure(West):
                swap(West)
                swapped = True

        left_x += 1

        if not swapped:
            return


def sort_current_column() -> None:
    # The worker starts on the column it owns.
    sort_cactus_column(get_pos_x())


def sort_current_column_reverse() -> None:
    # Sort south to north in descending order for the inversion achievement.
    bottom_y = CACTUS_START_Y
    top_y = CACTUS_START_Y + CACTUS_SIZE - 1
    column_x = get_pos_x()

    while bottom_y < top_y:
        swapped = False

        for y in range(bottom_y, top_y):
            move_to(column_x, y)

            if measure() < measure(North):
                swap(North)
                swapped = True

        top_y -= 1

        if not swapped:
            return

        swapped = False

        for y in range(top_y, bottom_y, -1):
            move_to(column_x, y)

            if measure() > measure(South):
                swap(South)
                swapped = True

        bottom_y += 1

        if not swapped:
            return


def run_parallel_rows(task) -> None:
    # Spawn one worker for each row, keeping the original drone for the last.
    workers = []
    move_to(CACTUS_START_X, CACTUS_START_Y)

    for row in range(CACTUS_SIZE - 1):
        worker = spawn_drone(task)

        if worker == None:
            # Fall back to the current drone if the worker limit is reached.
            task()
        else:
            workers.append(worker)

        move_to(CACTUS_START_X, CACTUS_START_Y + row + 1)

    task()

    for worker in workers:
        wait_for(worker)


def run_parallel_columns(task) -> None:
    # Spawn one worker for each column, keeping the original drone for the last.
    workers = []
    move_to(CACTUS_START_X, CACTUS_START_Y)

    for column in range(CACTUS_SIZE - 1):
        worker = spawn_drone(task)

        if worker == None:
            # Fall back to the current drone if the worker limit is reached.
            task()
        else:
            workers.append(worker)

        move_to(CACTUS_START_X + column + 1, CACTUS_START_Y)

    task()

    for worker in workers:
        wait_for(worker)


def grow_patch() -> None:
    # Every row grows independently before sorting begins.
    run_parallel_rows(grow_cactus_row_until_ready)


def sort_patch() -> None:
    if CACTUS_REVERSE_SORT:
        # Row sorts are independent, so they can run concurrently.
        run_parallel_rows(sort_current_row_reverse)

        # Columns must wait until every row has finished its reverse sort.
        run_parallel_columns(sort_current_column_reverse)
    else:
        # Row sorts are independent, so they can run concurrently.
        run_parallel_rows(sort_current_row)

        # Columns must wait until every row has finished its cocktail sort.
        run_parallel_columns(sort_current_column)


def harvest_patch() -> None:
    # A sorted, mature cactus patch can be harvested from its southwest tile.
    move_to(CACTUS_START_X, CACTUS_START_Y)

    while not can_harvest():
        pass

    if FERTILIZE_CACTUS_HARVEST:
        fertilize_before_harvest()

    harvest()


while True:
    grow_patch()
    sort_patch()
    harvest_patch()
